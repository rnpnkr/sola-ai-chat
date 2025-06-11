"""GraphQueryService – execute read queries against Neo4j with simple caching."""

from __future__ import annotations

import time
import logging
from typing import List, Dict

from neo4j import GraphDatabase, basic_auth

from config import NEO4J_CONFIG
from subconscious import graph_schema as gs

logger = logging.getLogger(__name__)


class GraphQueryService:
    """Lightweight wrapper around Neo4j for common relationship queries."""

    def __init__(self):
        uri = NEO4J_CONFIG.get("uri")
        if not uri:
            raise RuntimeError("Neo4j URI not configured; graph queries unavailable.")

        self._driver = GraphDatabase.driver(
            uri,
            auth=basic_auth(NEO4J_CONFIG.get("username"), NEO4J_CONFIG.get("password")),
        )
        self.database = NEO4J_CONFIG.get("database", "neo4j")

        # Ensure constraints exist once
        gs.ensure_constraints()

        # Cache: {user_id: (timestamp, List[str])}
        self._recent_emotion_cache: Dict[str, tuple] = {}
        self.cache_ttl_seconds: int = 60

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_recent_emotional_context(self, user_id: str, limit: int = 3) -> List[str]:
        """Return recent emotions the user felt with optional triggers."""

        # Check cache first
        cache_entry = self._recent_emotion_cache.get(user_id)
        if cache_entry and (time.time() - cache_entry[0] < self.cache_ttl_seconds):
            return cache_entry[1]

        query = (
            f"MATCH (u:{gs.USER_LABEL} {{user_id: $uid}})-[:{gs.REL_FEELS}]->(e:{gs.EMOTION_LABEL}) "
            f"OPTIONAL MATCH (e)-[:{gs.REL_TRIGGERED_BY}]->(ev:{gs.EVENT_LABEL}) "
            "WITH e, ev ORDER BY e.created_at DESC LIMIT $lim "
            "RETURN e.name AS emotion, ev.summary AS cause"
        )

        with self._driver.session(database=self.database) as session:
            records = session.run(query, uid=user_id, lim=limit)
            lines = [
                f"{rec['emotion']} (triggered by: {rec.get('cause') or 'unknown'})"
                for rec in records if rec.get("emotion")
            ]

        # Cache and return
        self._recent_emotion_cache[user_id] = (time.time(), lines)
        return lines

    # ------------------------------------------------------------------

    def close(self):
        try:
            self._driver.close()
        except Exception:
            pass

    # ---- Stubs for future complex queries --------------------------------

    def analyze_trust_progression(self, user_id: str) -> List[str]:
        """Return simplified trust progression events (stub)."""
        # TODO: Implement real traversal; for now return empty list to satisfy scaffold.
        return []

    def map_vulnerability_pattern(self, user_id: str) -> List[str]:
        """Return patterns of vulnerability (stub)."""
        return []

    def support_network_context(self, user_id: str) -> List[str]:
        """Return support network context (stub)."""
        return []

    # ------------------------------------------------------------------
    # 🌟 Intimate AI Companion – advanced queries
    # ------------------------------------------------------------------

    def get_comfort_patterns(self, user_id: str):
        """Find what comforts this user during different emotional states."""
        query = (
            f"MATCH (u:{gs.USER_LABEL} {{user_id: $uid}})-[:{gs.REL_COMFORTED_BY}]->(ev:{gs.EVENT_LABEL}) "
            f"OPTIONAL MATCH (e:{gs.EMOTION_LABEL})-[:{gs.REL_SUPPORTED_BY}]->(ev) "
            "WHERE e.user_id = $uid "
            "RETURN ev.summary as comfort_activity, e.name as emotion_helped, ev.created_at as when_used "
            "ORDER BY ev.created_at DESC LIMIT 5"
        )
        with self._driver.session(database=self.database) as session:
            records = session.run(query, uid=user_id)
            return [
                {
                    "comfort_activity": rec["comfort_activity"],
                    "emotion_helped": rec["emotion_helped"],
                    "when_used": rec["when_used"],
                }
                for rec in records if rec.get("comfort_activity")
            ]

    def analyze_emotional_evolution_paths(self, user_id: str):
        """Trace how user's emotions evolve over time."""
        query = (
            f"MATCH (e1:{gs.EMOTION_LABEL} {{user_id: $uid}})-[r:{gs.REL_EVOLVED_FROM}]->(e2:{gs.EMOTION_LABEL} {{user_id: $uid}}) "
            "RETURN e1.name as from_emotion, e2.name as to_emotion, r.evolution_catalyst as catalyst, r.created_at as when_evolved "
            "ORDER BY r.created_at DESC LIMIT 10"
        )
        with self._driver.session(database=self.database) as session:
            records = session.run(query, uid=user_id)
            return [
                {
                    "emotional_journey": f"{rec['from_emotion']} → {rec['to_emotion']}",
                    "catalyst": rec["catalyst"],
                    "when_evolved": rec["when_evolved"],
                }
                for rec in records
            ]

    def get_trust_progression_timeline(self, user_id: str):
        """Get chronological trust building milestones."""
        query = (
            f"MATCH (u:{gs.USER_LABEL} {{user_id: $uid}})-[r:{gs.REL_TRUSTS_WITH}]->(ev:{gs.EVENT_LABEL}) "
            "RETURN ev.summary as milestone, r.trust_level as trust_level, ev.created_at as when_achieved "
            "ORDER BY ev.created_at ASC"
        )
        with self._driver.session(database=self.database) as session:
            records = session.run(query, uid=user_id)
            return [
                {
                    "milestone": rec["milestone"],
                    "trust_level": rec["trust_level"],
                    "when_achieved": rec["when_achieved"],
                }
                for rec in records
            ] 