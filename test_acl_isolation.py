import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from qdrant_client import QdrantClient, models

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = PRIVATE_KEY.public_key()


def mint_mock_jwt(sub: str, groups: list[str]) -> str:
    return jwt.encode({"sub": sub, "groups": groups}, PRIVATE_KEY, algorithm="RS256")


def secure_search(client: QdrantClient, token: str, query_vec: list[float]):
    claims = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
    principals = [claims["sub"], *claims["groups"]]

    return client.query_points(
        collection_name="enterprise_chunks",
        query=query_vec,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="allowed_principals",
                    match=models.MatchAny(any=principals),
                )
            ]
        ),
        limit=5,
    )


@pytest.fixture
def seeded_qdrant() -> QdrantClient:
    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name="enterprise_chunks",
        vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
    )
    client.upsert(
        collection_name="enterprise_chunks",
        points=[
            models.PointStruct(
                id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={
                    "doc_id": "engineering_handbook",
                    "allowed_principals": ["grp_eng", "grp_exec"],
                },
            ),
            models.PointStruct(
                id=2,
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={
                    "doc_id": "doc_exec_comp_broken_inheritance",
                    "allowed_principals": ["grp_exec"],
                },
            ),
        ],
    )
    return client


def test_broken_inheritance_zero_leakage(seeded_qdrant: QdrantClient):
    intern_token = mint_mock_jwt(sub="user_intern", groups=["grp_eng"])
    res = secure_search(seeded_qdrant, intern_token, query_vec=[0.1, 0.2, 0.3, 0.4])

    returned_ids = [p.payload["doc_id"] for p in res.points]
    assert "engineering_handbook" in returned_ids
    assert "doc_exec_comp_broken_inheritance" not in returned_ids
