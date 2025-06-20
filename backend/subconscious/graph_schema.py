"""Graph schema definition for emotional relationship intelligence.

This module centralises labels, relationship types and constraint helpers
for the Neo4j graph used by the Intimate AI Companion. It provides
functions to ensure uniqueness constraints and indexes are created once
per process. All helpers automatically tag nodes with `user_id` to
prevent cross-user data leakage.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from neo4j import GraphDatabase, basic_auth

from config import NEO4J_CONFIG

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Label & relationship constants
# ---------------------------------------------------------------------------

USER_LABEL = "User"
MEMORY_LABEL = "Memory"
EVENT_LABEL = "Event"
EMOTION_LABEL = "Emotion"

# 🎯 EXPANDED EMOTION TAXONOMY for Intimate AI Companion
EMOTION_TAXONOMY: List[str] = [
    # Core Emotions
    "Joy", "Anxiety", "Trust", "Vulnerability", "Sadness", "Anger", "Love", "Fear",

    # 🔥 INTIMATE AI ADDITIONS:
    "Loneliness", "Comfort", "Safety", "Insecurity", "Excitement", "Disappointment",
    "Gratitude", "Shame", "Pride", "Confusion", "Hope", "Overwhelm", "Peace",
    "Validation", "Rejection", "Connection", "Isolation", "Anticipation"
]

# Relationship types
REL_FEELS = "FEELS"  # (User|Event)-[:FEELS]->(Emotion)
REL_TRIGGERED_BY = "TRIGGERED_BY"  # (Emotion)-[:TRIGGERED_BY]->(Event)
REL_CONNECTS_TO = "CONNECTS_TO"  # (Emotion)-[:CONNECTS_TO]->(Emotion)
REL_LEADS_TO = "LEADS_TO"  # (Emotion|Event)-[:LEADS_TO]->(Emotion|Event)
REL_SUPPORTED_BY = "SUPPORTED_BY"  # (Emotion|Event)-[:SUPPORTED_BY]->(Event)
REL_DISCLOSED_TO = "DISCLOSED_TO"  # (User)-[:DISCLOSED_TO]->(Event)

# 🔥 NEW INTIMATE AI RELATIONSHIPS
REL_COMFORTED_BY = "COMFORTED_BY"      # (User)-[:COMFORTED_BY]->(Event)
REL_TRUSTS_WITH = "TRUSTS_WITH"        # (User)-[:TRUSTS_WITH]->(Event)
REL_EVOLVED_FROM = "EVOLVED_FROM"      # (Emotion)-[:EVOLVED_FROM]->(Emotion)
REL_PATTERNS_TO = "PATTERNS_TO"        # (Event)-[:PATTERNS_TO]->(Event)
REL_VALIDATED_BY = "VALIDATED_BY"      # (Emotion)-[:VALIDATED_BY]->(Event)

# Constraint initialisation guard
_SCHEMA_INITIALISED = False


def _driver():
    """Return an active Neo4j driver using config."""
    uri = NEO4J_CONFIG.get("uri")
    if not uri:
        raise ValueError("NEO4J_URI not configured – cannot connect to graph store.")
    return GraphDatabase.driver(
        uri,
        auth=basic_auth(NEO4J_CONFIG.get("username"), NEO4J_CONFIG.get("password")),
    )


def ensure_constraints() -> None:
    """Create required uniqueness constraints & indexes with proper Neo4j 5.x syntax."""
    global _SCHEMA_INITIALISED
    if _SCHEMA_INITIALISED:
        return

    try:
        drv = _driver()
        with drv.session(database=NEO4J_CONFIG.get("database", "neo4j")) as session:
            # User uniqueness constraint
            session.run(
                "CREATE CONSTRAINT user_unique IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE"
            )

            # Memory uniqueness composite constraint
            session.run(
                "CREATE CONSTRAINT memory_unique IF NOT EXISTS FOR (m:Memory) REQUIRE (m.memory_id, m.user_id) IS UNIQUE"
            )

            # 🔧 Individual indexes per label for user_id
            session.run("CREATE INDEX user_user_id_idx IF NOT EXISTS FOR (u:User) ON (u.user_id)")
            session.run("CREATE INDEX memory_user_id_idx IF NOT EXISTS FOR (m:Memory) ON (m.user_id)")
            session.run("CREATE INDEX emotion_user_id_idx IF NOT EXISTS FOR (e:Emotion) ON (e.user_id)")
            session.run("CREATE INDEX event_user_id_idx IF NOT EXISTS FOR (ev:Event) ON (ev.user_id)")

            # 🎯 Performance indexes for emotional queries
            session.run("CREATE INDEX emotion_name_idx IF NOT EXISTS FOR (e:Emotion) ON (e.name)")
            session.run("CREATE INDEX emotion_created_idx IF NOT EXISTS FOR (e:Emotion) ON (e.created_at)")
            session.run("CREATE INDEX event_summary_idx IF NOT EXISTS FOR (ev:Event) ON (ev.summary)")
            session.run("CREATE INDEX memory_intimacy_idx IF NOT EXISTS FOR (m:Memory) ON (m.intimacy_level)")

        _SCHEMA_INITIALISED = True
        logger.info("✅ Graph schema constraints ensured with intimate AI optimizations.")
    except Exception as exc:
        logger.error("❌ Failed to ensure graph schema constraints: %s", exc, exc_info=True)
    finally:
        try:
            drv.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Helper creation functions
# ---------------------------------------------------------------------------

def get_or_create_user(tx, user_id: str):
    query = (
        "MERGE (u:User {user_id: $uid}) "
        "ON CREATE SET u.created_at = timestamp() "
        "RETURN u"
    )
    return tx.run(query, uid=user_id).single().get("u")


def get_or_create_emotion(tx, user_id: str, emotion: str):
    if emotion not in EMOTION_TAXONOMY:
        # For now ignore unknown emotion; could create new label later
        return None
    query = (
        "MERGE (e:Emotion {name: $emotion, user_id: $uid}) "
        "ON CREATE SET e.created_at = timestamp() "
        "RETURN e"
    )
    return tx.run(query, emotion=emotion, uid=user_id).single().get("e")


# Additional helpers (create_memory_node etc.) can be implemented as needed. 