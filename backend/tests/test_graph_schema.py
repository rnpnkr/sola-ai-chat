import uuid
import asyncio

import pytest

try:
    from neo4j import GraphDatabase, basic_auth  # type: ignore
except ModuleNotFoundError:
    pytest.skip("neo4j driver not installed", allow_module_level=True)

from backend.config import NEO4J_CONFIG
from backend.subconscious.graph_schema import ensure_constraints, USER_LABEL

pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(
    not NEO4J_CONFIG.get("uri"),
    reason="Neo4j not configured",
)
async def test_user_uniqueness_constraint():
    """Ensure only one User node exists for same user_id (uniqueness)."""
    ensure_constraints()

    uid = f"test_{uuid.uuid4().hex[:8]}"
    driver = GraphDatabase.driver(
        NEO4J_CONFIG["uri"],
        auth=basic_auth(NEO4J_CONFIG.get("username"), NEO4J_CONFIG.get("password")),
    )
    db = NEO4J_CONFIG.get("database", "neo4j")
    with driver.session(database=db) as session:
        # Create twice
        session.run(f"MERGE (u:{USER_LABEL} {{user_id: $uid}}) RETURN u", uid=uid)
        session.run(f"MERGE (u:{USER_LABEL} {{user_id: $uid}}) RETURN u", uid=uid)
        # Count
        cnt = session.run(
            f"MATCH (u:{USER_LABEL} {{user_id: $uid}}) RETURN count(u) as cnt",
            uid=uid,
        ).single()["cnt"]
        assert cnt == 1
    driver.close() 