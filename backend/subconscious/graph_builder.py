"""GraphRelationshipBuilder – write relationships into Neo4j respecting user isolation."""
from __future__ import annotations

import logging
from typing import Optional

from neo4j import GraphDatabase, basic_auth

from config import NEO4J_CONFIG
from subconscious import graph_schema as gs

logger = logging.getLogger(__name__)


class GraphRelationshipBuilder:
    def __init__(self):
        uri = NEO4J_CONFIG.get("uri")
        if not uri:
            raise RuntimeError("NEO4J URI missing for Graph Builder")
        self._driver = GraphDatabase.driver(uri, auth=basic_auth(NEO4J_CONFIG.get("username"), NEO4J_CONFIG.get("password")))
        self.db = NEO4J_CONFIG.get("database", "neo4j")
        gs.ensure_constraints()

    # -------------------------------------------------------------
    def add_feels(self, user_id: str, emotion: str, intensity: Optional[str] = None):
        if emotion not in gs.EMOTION_TAXONOMY:
            return
        query = (
            f"MERGE (u:{gs.USER_LABEL} {{user_id: $uid}}) "
            f"MERGE (e:{gs.EMOTION_LABEL} {{name: $emotion, user_id: $uid}}) "
            f"MERGE (u)-[r:{gs.REL_FEELS}]->(e) "
            "ON CREATE SET r.created_at = timestamp(), r.intensity = $intensity "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(query, uid=user_id, emotion=emotion, intensity=intensity or "unknown")

    def add_triggered_by(self, user_id: str, emotion: str, event_summary: str):
        """Create TRIGGERED_BY relationship between emotion and event."""
        if emotion not in gs.EMOTION_TAXONOMY:
            return
        query = (
            f"MERGE (u:{gs.USER_LABEL} {{user_id: $uid}}) "
            f"MERGE (e:{gs.EMOTION_LABEL} {{name: $emotion, user_id: $uid}}) "
            f"MERGE (ev:{gs.EVENT_LABEL} {{summary: $summary, user_id: $uid}}) "
            "ON CREATE SET ev.created_at = timestamp() "
            f"MERGE (e)-[r:{gs.REL_TRIGGERED_BY}]->(ev) "
            "ON CREATE SET r.created_at = timestamp() "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(query, uid=user_id, emotion=emotion, summary=event_summary[:200])

    def add_disclosure_relationship(self, user_id: str, event_summary: str, intimacy_level: str):
        """Create DISCLOSED_TO relationship for vulnerability tracking."""
        query = (
            f"MERGE (u:{gs.USER_LABEL} {{user_id: $uid}}) "
            f"MERGE (ev:{gs.EVENT_LABEL} {{summary: $summary, user_id: $uid}}) "
            "ON CREATE SET ev.created_at = timestamp(), ev.intimacy_level = $intimacy "
            f"MERGE (u)-[r:{gs.REL_DISCLOSED_TO}]->(ev) "
            "ON CREATE SET r.created_at = timestamp(), r.intimacy_level = $intimacy "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(query, uid=user_id, summary=event_summary[:200], intimacy=intimacy_level)

    def add_emotional_connection(self, user_id: str, emotion1: str, emotion2: str, connection_type: str = "leads_to"):
        """Connect two emotions with LEADS_TO or CONNECTS_TO relationships."""
        if emotion1 not in gs.EMOTION_TAXONOMY or emotion2 not in gs.EMOTION_TAXONOMY:
            return
        rel_type = gs.REL_LEADS_TO if connection_type == "leads_to" else gs.REL_CONNECTS_TO
        query = (
            f"MERGE (e1:{gs.EMOTION_LABEL} {{name: $e1, user_id: $uid}}) "
            f"MERGE (e2:{gs.EMOTION_LABEL} {{name: $e2, user_id: $uid}}) "
            f"MERGE (e1)-[r:{rel_type}]->(e2) "
            "ON CREATE SET r.created_at = timestamp(), r.connection_type = $ctype "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(query, uid=user_id, e1=emotion1, e2=emotion2, ctype=connection_type)

    def close(self):
        self._driver.close()

    # -----------------------------------------------------------------
    # Intimate AI Companion specific builders
    # -----------------------------------------------------------------

    def add_comfort_relationship(self, user_id: str, comfort_event: str, emotion_comforted: str):
        """Track what comforts this user during specific emotional states."""
        if emotion_comforted not in gs.EMOTION_TAXONOMY:
            return
        query = (
            f"MERGE (u:{gs.USER_LABEL} {{user_id: $uid}}) "
            f"MERGE (ev:{gs.EVENT_LABEL} {{summary: $event, user_id: $uid}}) "
            f"MERGE (e:{gs.EMOTION_LABEL} {{name: $emotion, user_id: $uid}}) "
            "ON CREATE SET ev.created_at = timestamp(), e.created_at = timestamp() "
            f"MERGE (u)-[r:{gs.REL_COMFORTED_BY}]->(ev) "
            f"MERGE (e)-[r2:{gs.REL_SUPPORTED_BY}]->(ev) "
            "ON CREATE SET r.created_at = timestamp(), r2.created_at = timestamp() "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(query, uid=user_id, event=comfort_event[:200], emotion=emotion_comforted)

    def add_trust_milestone(self, user_id: str, milestone_event: str, trust_level: str):
        """Record trust progression milestones."""
        query = (
            f"MERGE (u:{gs.USER_LABEL} {{user_id: $uid}}) "
            f"MERGE (ev:{gs.EVENT_LABEL} {{summary: $event, user_id: $uid}}) "
            "ON CREATE SET ev.created_at = timestamp(), ev.trust_level = $trust_level "
            f"MERGE (u)-[r:{gs.REL_TRUSTS_WITH}]->(ev) "
            "ON CREATE SET r.created_at = timestamp(), r.trust_level = $trust_level "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(query, uid=user_id, event=milestone_event[:200], trust_level=trust_level)

    def add_emotional_evolution(self, user_id: str, from_emotion: str, to_emotion: str, catalyst_event: str):
        """Track how emotions evolve over time through specific events."""
        if from_emotion not in gs.EMOTION_TAXONOMY or to_emotion not in gs.EMOTION_TAXONOMY:
            return
        query = (
            f"MERGE (e1:{gs.EMOTION_LABEL} {{name: $from_emotion, user_id: $uid}}) "
            f"MERGE (e2:{gs.EMOTION_LABEL} {{name: $to_emotion, user_id: $uid}}) "
            f"MERGE (ev:{gs.EVENT_LABEL} {{summary: $catalyst, user_id: $uid}}) "
            "ON CREATE SET e1.created_at = timestamp(), e2.created_at = timestamp(), ev.created_at = timestamp() "
            f"MERGE (e1)-[r:{gs.REL_EVOLVED_FROM}]->(e2) "
            f"MERGE (ev)-[r2:{gs.REL_TRIGGERED_BY}]->(e2) "
            "ON CREATE SET r.created_at = timestamp(), r.evolution_catalyst = $catalyst, r2.created_at = timestamp() "
            "RETURN id(r)"
        )
        with self._driver.session(database=self.db) as sess:
            sess.run(
                query,
                uid=user_id,
                from_emotion=from_emotion,
                to_emotion=to_emotion,
                catalyst=catalyst_event[:200],
            )

    # -----------------------------------------------------------------
    # Migration & validation helpers (Phase-4)
    # -----------------------------------------------------------------

    @classmethod
    def migrate_missing_relationships(cls):
        """Populate any FEELS / TRIGGERED_BY relationships that are missing.

        This migration is *idempotent* – it uses MERGE so running multiple
        times is safe.  It attempts to back-fill basic emotional data for all
        users by scanning existing Emotion and Event nodes.
        """

        try:
            uri = NEO4J_CONFIG.get("uri")
            if not uri:
                logger.warning("Neo4j URI missing – skip relationship migration")
                return

            driver = GraphDatabase.driver(
                uri,
                auth=basic_auth(
                    NEO4J_CONFIG.get("username"), NEO4J_CONFIG.get("password")
                ),
            )

            db = NEO4J_CONFIG.get("database", "neo4j")

            with driver.session(database=db) as session:
                # FEELS: ensure each (User, Emotion) pair has at least one FEELS edge
                session.run(
                    f"""
                    MATCH (u:{gs.USER_LABEL})-[:{gs.REL_FEELS}]-(e:{gs.EMOTION_LABEL})
                    RETURN COUNT(*) AS dummy
                    """
                )

                session.run(
                    f"""
                    MATCH (u:{gs.USER_LABEL})<-[:{gs.REL_TRIGGERED_BY}]-(e:{gs.EMOTION_LABEL})
                    RETURN COUNT(*) AS dummy
                    """
                )

                # Create missing FEELS
                session.run(
                    f"""
                    MATCH (u:{gs.USER_LABEL}), (e:{gs.EMOTION_LABEL})
                    WHERE e.user_id = u.user_id
                    MERGE (u)-[r:{gs.REL_FEELS}]->(e)
                    ON CREATE SET r.created_at = timestamp()
                    """
                )

                # Create missing TRIGGERED_BY relationships if Event exists
                session.run(
                    f"""
                    MATCH (e:{gs.EMOTION_LABEL})
                    OPTIONAL MATCH (ev:{gs.EVENT_LABEL} {{user_id: e.user_id}})
                    WHERE ev IS NOT NULL
                    MERGE (e)-[r:{gs.REL_TRIGGERED_BY}]->(ev)
                    ON CREATE SET r.created_at = timestamp()
                    """
                )

            logger.info("✅ Graph relationship migration completed.")
        except Exception as exc:
            logger.error("Graph migration failed: %s", exc, exc_info=True)

    # -----------------------------------------------------------------
    @staticmethod
    def validate_relationship_exists(session, rel_type: str) -> bool:
        """Return True if `rel_type` exists in DB schema."""
        try:
            result = session.run(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType AS rel"
            )
            types = {rec["rel"] for rec in result}
            return rel_type in types
        except Exception:
            return False 