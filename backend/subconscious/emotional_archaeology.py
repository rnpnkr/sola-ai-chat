from __future__ import annotations

"""subconscious.emotional_archaeology

Responsible for analysing emotionally-salient memories (vulnerability, joy, pain) so that
long-running background processes can reason about the user at a deeper level.

The class wraps the existing IntimateMemoryService so that it can execute its own
semantic searches against Mem0 while still supporting direct analysis of already-fetched
search results (this allows us to reuse the same search data if another component has
fetched it earlier in the pipeline).

All public methods are kept **async** to avoid blocking the event-loop when they need to
perform network IO. Pure analysis helpers are synchronous.
"""

import logging
from datetime import datetime
from typing import Dict, List

from memory.mem0_async_service import IntimateMemoryService

logger = logging.getLogger(__name__)

__all__ = ["EmotionalArchaeology"]


class EmotionalArchaeology:
    """Extracts fine-grained emotional patterns from a user's memories."""

    # Keyword pools for the three core emotional strata we currently support
    _VULNERABILITY_KEYWORDS = (
        "vulnerable scared worried personal sharing afraid secret private disclosure fear anxious"
    )
    _JOY_KEYWORDS = (
        "happy excited thrilled joyful celebrate delighted gratitude proud love enjoyable"
    )
    _PAIN_KEYWORDS = (
        "struggle difficult challenge pain frustration recurring hurt sad grief lonely upset"
    )

    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service

    # ---------------------------------------------------------------------
    # High-level helpers that *both* search and analyse in a single call
    # ---------------------------------------------------------------------

    async def mine_vulnerability_moments(self, user_id: str, limit: int = 25) -> Dict:
        """Run a vulnerability-focused semantic search and return pattern analysis."""
        data = await self.mem0_service.search_intimate_memories(
            query=self._VULNERABILITY_KEYWORDS,
            user_id=user_id,
            limit=limit,
        )
        return self._analyse_vulnerability_patterns(data)

    async def extract_joy_patterns(self, user_id: str, limit: int = 25) -> Dict:
        """Find joyful memories and extract intensity/timestamps."""
        data = await self.mem0_service.search_intimate_memories(
            query=self._JOY_KEYWORDS,
            user_id=user_id,
            limit=limit,
        )
        return self._analyse_emotional_pattern(
            data, positive=True, label="joy_patterns", keywords=self._JOY_KEYWORDS.split()
        )

    async def map_pain_points(self, user_id: str, limit: int = 25) -> Dict:
        """Detect recurring pain/struggle points in the user's memories."""
        data = await self.mem0_service.search_intimate_memories(
            query=self._PAIN_KEYWORDS,
            user_id=user_id,
            limit=limit,
        )
        return self._analyse_emotional_pattern(
            data, positive=False, label="pain_points", keywords=self._PAIN_KEYWORDS.split()
        )

    async def track_growth_arcs(self, user_id: str, limit: int = 25) -> Dict:
        """Identify emotional growth arcs by searching for reflective memories.

        Growth arcs are moments where the user explicitly references personal
        change, insight, or progress (e.g. *"I've realised…", "I'm getting
        better at…", "I finally overcame…").  We perform a targeted search and
        then summarise a timeline-like structure that downstream components can
        visualise or further analyse.
        """
        growth_keywords = (
            "growth progress evolved improvement overcome learned realised realized insight change better"
        )

        data = await self.mem0_service.search_intimate_memories(
            query=growth_keywords,
            user_id=user_id,
            limit=limit,
        )
        return self._analyse_growth_arcs(data)

    # ------------------------------------------------------------------
    # Public *analysis-only* helpers (operate on already fetched data)
    # ------------------------------------------------------------------

    def analyse_vulnerability_data(self, vulnerability_data: Dict) -> Dict:
        """Expose the vulnerability analysis for already-fetched search data."""
        return self._analyse_vulnerability_patterns(vulnerability_data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_iter_results(self, search_payload: Dict) -> List[Dict]:
        """Normalise the search results into a predictable list of dicts."""
        results = search_payload.get("results", []) if isinstance(search_payload, dict) else []
        # Mem0 occasionally returns a single dict instead of list – normalise
        if isinstance(results, dict):
            return [results]
        return list(results)

    def _analyse_vulnerability_patterns(self, vulnerability_data: Dict) -> Dict:
        """Core logic extracted from *background_processor* with minor refactor."""
        results = self._safe_iter_results(vulnerability_data)
        analysis = {
            "disclosure_depth": "surface",
            "vulnerability_comfort": 0.0,
            "intimate_sharing_events": [],
            "emotional_expression_types": [],
            "authentic_moments": [],
        }
        intimate_disclosure_count = 0
        total_disclosures = len(results)

        # Keyword mappings preserved from original implementation
        emotion_keywords = {
            "fear": ["scared", "afraid", "terrified", "fear"],
            "sadness": ["sad", "crying", "heartbroken", "grief"],
            "joy": ["happy", "excited", "thrilled", "joyful"],
            "anger": ["angry", "furious", "mad", "irritated"],
            "shame": ["ashamed", "embarrassed", "humiliated"],
            "love": ["love", "adore", "cherish", "devoted"],
        }

        for memory in results:
            memory_text = str(memory.get("memory", "")).lower() if isinstance(memory, dict) else str(memory).lower()
            metadata = memory.get("metadata", {}) if isinstance(memory, dict) else {}
            if not memory_text:
                continue

            # Deep personal sharing detection
            if any(p in memory_text for p in ["never told", "secret", "personal", "private", "intimate"]):
                intimate_disclosure_count += 1
                analysis["intimate_sharing_events"].append(
                    {
                        "memory": memory_text[:100],
                        "timestamp": metadata.get("timestamp"),
                        "depth": "deep",
                    }
                )

            # Emotion extraction
            emotions_found = [e for e, kws in emotion_keywords.items() if any(k in memory_text for k in kws)]
            if emotions_found:
                analysis["emotional_expression_types"].extend(emotions_found)

            # Authenticity markers
            if any(p in memory_text for p in ["authentic", "real", "genuine", "true self", "honest"]):
                analysis["authentic_moments"].append(memory_text[:100])

        # Aggregate metrics
        analysis["vulnerability_comfort"] = intimate_disclosure_count / max(total_disclosures, 1)
        if intimate_disclosure_count >= 3:
            analysis["disclosure_depth"] = "deep"
        elif intimate_disclosure_count >= 1:
            analysis["disclosure_depth"] = "moderate"
        else:
            analysis["disclosure_depth"] = "surface"

        return analysis

    def _analyse_emotional_pattern(
        self,
        search_data: Dict,
        *,
        positive: bool,
        label: str,
        keywords: List[str],
    ) -> Dict:
        """Generic analyser for positive/negative emotional patterns."""
        results = self._safe_iter_results(search_data)
        pattern_results = []
        intensity_sum = 0

        for memory in results:
            memory_text = str(memory.get("memory", "")).lower() if isinstance(memory, dict) else str(memory).lower()
            metadata = memory.get("metadata", {}) if isinstance(memory, dict) else {}
            if not memory_text:
                continue

            intensity = sum(word in memory_text for word in keywords) / len(keywords)
            intensity_sum += intensity
            pattern_results.append(
                {
                    "memory": memory_text[:100],
                    "timestamp": metadata.get("timestamp"),
                    "intensity": round(intensity, 2),
                }
            )

        average_intensity = round(intensity_sum / max(len(pattern_results), 1), 2)
        return {
            "pattern": label,
            "average_intensity": average_intensity,
            "occurrences": pattern_results,
            "generated_at": datetime.utcnow().isoformat(),
            "positive": positive,
        }

    # ------------------------------------------------------------------
    # Private growth-analysis helper
    # ------------------------------------------------------------------

    def _analyse_growth_arcs(self, search_data: Dict) -> Dict:
        """Produce a lightweight growth timeline from Mem0 search output."""
        results = self._safe_iter_results(search_data)
        timeline: List[Dict] = []

        for memory in results:
            text = str(memory.get("memory", "")) if isinstance(memory, dict) else str(memory)
            meta = memory.get("metadata", {}) if isinstance(memory, dict) else {}
            if not text:
                continue

            # Basic heuristics for growth direction (positive/negative)
            direction = "positive" if any(k in text.lower() for k in ["better", "overcome", "improved", "growth"]) else "neutral"
            timestamp = meta.get("timestamp") or meta.get("created_at")
            timeline.append({
                "snippet": text[:120],
                "direction": direction,
                "timestamp": timestamp,
            })

        return {
            "growth_events": timeline,
            "event_count": len(timeline),
            "generated_at": datetime.utcnow().isoformat(),
        }
