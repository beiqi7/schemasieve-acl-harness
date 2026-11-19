import networkx as nx
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify


def extract_verified_joins(
    query_logs: list[str],
    catalog_schema: dict,
    dialect: str = "snowflake",
) -> nx.DiGraph:
    """
    Normalizes raw SQL logs against INFORMATION_SCHEMA metadata via AST qualification
    and extracts weighted production join edges.
    """
    join_graph = nx.DiGraph()

    for raw_sql in query_logs:
        try:
            ast = sqlglot.parse_one(raw_sql, read=dialect)
            qualified = qualify(ast, schema=catalog_schema, dialect=dialect)

            for join in qualified.find_all(exp.Join):
                on_clause = join.args.get("on")
                if not on_clause:
                    continue
                cols = list(on_clause.find_all(exp.Column))
                if len(cols) >= 2:
                    left = f"{cols[0].table}.{cols[0].name}".upper()
                    right = f"{cols[1].table}.{cols[1].name}".upper()
                    weight = join_graph.get_edge_data(left, right, {}).get("weight", 0) + 1
                    join_graph.add_edge(left, right, weight=weight)
        except sqlglot.errors.ParseError:
            continue

    return join_graph


if __name__ == "__main__":
    mock_schema = {
        "PROD_DB": {
            "CORE": {
                "ORDERS": {"ORDER_ID": "INT", "CUSTOMER_ID": "INT"},
                "CUSTOMERS": {"CUSTOMER_ID": "INT", "REGION": "VARCHAR"},
            }
        }
    }
    logs = [
        "SELECT o.order_id, c.region FROM prod_db.core.orders o JOIN prod_db.core.customers c ON o.customer_id = c.customer_id",
        "SELECT * FROM prod_db.core.orders JOIN prod_db.core.customers USING (customer_id)",
    ]
    graph = extract_verified_joins(logs, mock_schema)
    print("Verified Join Edges:", list(graph.edges(data=True)))
