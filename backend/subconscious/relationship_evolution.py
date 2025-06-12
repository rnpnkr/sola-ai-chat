from __future__ import annotations

"""subconscious.relationship_evolution

Encapsulates logic for understanding how the relationship between the
user and the AI companion is progressing over time. Extracted from the
previous monolithic *background_processor* so it can be reused across
different background services or exposed via future analytics APIs.
"""

import logging
from datetime import datetime
from typing import Dict, List

from memory.mem0_async_service import IntimateMemoryService

logger = logging.getLogger(__name__)

__all__ = ["RelationshipEvolutionTracker"]


class RelationshipEvolutionTracker:
    """Analyse temporal signals that indicate relationship evolution."""

    _REL_EVOLUTION_KEYWORDS = (
        "relationship growth progression development deeper connection understanding empathy companionship bond"
    )

    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service

    # ------------------------------------------------------------------
    # Higher-level helpers that search + analyse in one go
    # ------------------------------------------------------------------

    async def detect_relationship_velocity(self, user_id: str, limit: int = 25) -> Dict:
        """Compute the rate at which intimacy is deepening based on memory signals."""
        data = await self.mem0_service.search_intimate_memories(
            query=self._REL_EVOLUTION_KEYWORDS,
            user_id=user_id,
            limit=limit,
        )
        return self._analyse_relationship_evolution(data)

    async def track_trust_milestones(self, user_id: str, limit: int = 25) -> Dict:
        """Identify key memories that reflect deepening trust and summarise level."""
        data = await self.mem0_service.search_intimate_memories(
            query="trust rely safe comfortable share secret confidence depend",
            user_id=user_id,
            limit=limit,
        )
        milestone_events: List[Dict] = []
        for memory in self._safe_iter_results(data):
            memory_text = memory.get("memory", "") if isinstance(memory, dict) else str(memory)
            metadata = memory.get("metadata", {}) if isinstance(memory, dict) else {}
            if not memory_text:
                continue
            if any(p in memory_text.lower() for p in ["trust you", "rely on", "i feel safe"]):
                milestone_events.append({
                    "memory": memory_text[:120],
                    "timestamp": metadata.get("timestamp"),
                    "type": "trust_declaration",
                })

        # Simple trust level heuristic based on number of declarations
        count = len(milestone_events)
        if count >= 5:
            level = "high"
        elif count >= 2:
            level = "medium"
        elif count == 1:
            level = "emerging"
        else:
            level = "low"

        return {
            "trust_level": level,
            "milestones": milestone_events,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def analyze_communication_patterns(self, user_id: str, limit: int = 25) -> Dict:
        """Infer the user's interaction style (tone, prompt length, etc.)."""
        data = await self.mem0_service.search_intimate_memories(
            query="share talk speak conversation discuss ask say tell",  # broad
            user_id=user_id,
            limit=limit,
        )
        results = self._safe_iter_results(data)
        pattern = {
            "average_message_length": 0,
            "question_ratio": 0,
            "emotionally_expressive_ratio": 0,
            "sample_size": len(results),
        }
        total_chars = 0
        questions = 0
        expressive_markers = 0
        expressive_keywords = ["feel", "emotion", "love", "worry", "excited", "sad", "happy"]
        for memory in results:
            text = str(memory.get("memory", "")) if isinstance(memory, dict) else str(memory)
            total_chars += len(text)
            if "?" in text:
                questions += 1
            if any(k in text.lower() for k in expressive_keywords):
                expressive_markers += 1
        if results:
            pattern["average_message_length"] = round(total_chars / len(results), 2)
            pattern["question_ratio"] = round(questions / len(results), 2)
            pattern["emotionally_expressive_ratio"] = round(expressive_markers / len(results), 2)
        return pattern

    async def detect_relationship_phases(self, user_id: str, limit: int = 25) -> Dict:
        """Infer the current phase of the relationship (exploration, building, deep).

        This helper piggy-backs on the *relationship velocity* analysis and
        trust milestones.  It keeps logic intentionally simple because more
        advanced modelling is handled by the intimacy scaffold.
        """
        velocity_data = await self.detect_relationship_velocity(user_id, limit=limit)
        trust_milestones = await self.track_trust_milestones(user_id, limit=limit)

        # Basic heuristics
        growth = velocity_data.get("growth_trajectory", "stable")
        trust_events = len(trust_milestones["milestones"])

        if trust_events >= 5 or growth == "accelerating":
            phase = "deepening"
        elif trust_events >= 2 or growth in {"progressing", "accelerating"}:
            phase = "building"
        else:
            phase = "exploration"

        return {
            "phase": phase,
            "growth_trajectory": growth,
            "trust_milestone_count": trust_events,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def track_inside_references(self, user_id: str, limit: int = 25) -> List[Dict]:
        """Collect references that signal shared knowledge or inside jokes."""
        query_terms = "inside joke remember when just like last time as we talked continuation callback reference"
        data = await self.mem0_service.search_intimate_memories(
            query=query_terms,
            user_id=user_id,
            limit=limit,
        )
        refs: List[Dict] = []
        for memory in self._safe_iter_results(data):
            txt = memory.get("memory", "") if isinstance(memory, dict) else str(memory)
            meta = memory.get("metadata", {}) if isinstance(memory, dict) else {}
            if not txt:
                continue
            refs.append({
                "snippet": txt[:120],
                "timestamp": meta.get("timestamp"),
            })
        return refs

    # ------------------------------------------------------------------
    # Public analysis helper for pre-fetched search data
    # ------------------------------------------------------------------

    def analyse_relationship_evolution_data(self, relationship_data: Dict) -> Dict:
        return self._analyse_relationship_evolution(relationship_data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_iter_results(self, payload: Dict):
        results = payload.get("results", []) if isinstance(payload, dict) else []
        if isinstance(results, dict):
            return [results]
        return list(results)

    def _analyse_relationship_evolution(self, relationship_data: Dict) -> Dict:
        """Ported from background_processor._analyze_relationship_evolution."""
        results = self._safe_iter_results(relationship_data)
        evolution_analysis = {
            "growth_trajectory": "stable",
            "connection_deepening": False,
            "empathy_development": [],
            "companionship_quality": "developing",
            "relationship_milestones": [],
        }
        growth_indicators = 0
        connection_depth_indicators = 0
        for memory in results:
            memory_text = (
                str(memory.get("memory", "")).lower()
                if isinstance(memory, dict)
                else str(memory).lower()
            )
            metadata = memory.get("metadata", {}) if isinstance(memory, dict) else {}
            if not memory_text:
                continue

            if any(w in memory_text for w in ["growth", "progress", "development", "better", "improve"]):
                growth_indicators += 1
            if any(p in memory_text for p in [
                "understand me",
                "get me",
                "connection",
                "bond",
                "close",
            ]):
                connection_depth_indicators += 1
                evolution_analysis["relationship_milestones"].append(
                    {
                        "type": "connection_deepening",
                        "memory": memory_text[:100],
                        "timestamp": metadata.get("timestamp"),
                    }
                )
            if any(w in memory_text for w in ["empathy", "understand", "compassion", "care", "support"]):
                evolution_analysis["empathy_development"].append(memory_text[:100])

        if growth_indicators >= 3:
            evolution_analysis["growth_trajectory"] = "accelerating"
        elif growth_indicators >= 1:
            evolution_analysis["growth_trajectory"] = "progressing"
        else:
            evolution_analysis["growth_trajectory"] = "stable"

        evolution_analysis["connection_deepening"] = connection_depth_indicators >= 2
        total = growth_indicators + connection_depth_indicators
        if total >= 5:
            evolution_analysis["companionship_quality"] = "intimate"
        elif total >= 3:
            evolution_analysis["companionship_quality"] = "established"
        else:
            evolution_analysis["companionship_quality"] = "developing"

        return evolution_analysis
