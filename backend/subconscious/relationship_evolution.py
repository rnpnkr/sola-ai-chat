from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from memory.mem0_async_service import IntimateMemoryService

logger = logging.getLogger(__name__)

class RelationshipEvolutionTracker:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service

    async def track_trust_milestones(self, user_id: str) -> Dict:
        """Detect intimacy progression over time"""
        try:
            # Search for trust-building moments
            trust_memories = await self.mem0_service.search_intimate_memories(
                query="trust share personal private open comfortable",
                user_id=user_id,
                limit=20
            )
            
            return self._analyze_trust_progression(trust_memories)
        except Exception as e:
            logger.error(f"Trust milestone tracking failed for {user_id}: {e}")
            return {}

    async def analyze_communication_patterns(self, user_id: str) -> Dict:
        """Learn user's preferred interaction style"""
        try:
            # Get diverse conversation samples
            communication_memories = await self.mem0_service.search_intimate_memories(
                query="conversation talk discuss prefer style communication",
                user_id=user_id,
                limit=25
            )
            
            return self._analyze_communication_dna(communication_memories)
        except Exception as e:
            logger.error(f"Communication analysis failed for {user_id}: {e}")
            return {}

    async def detect_relationship_phases(self, user_id: str) -> Dict:
        """Identify current relationship phase and progression"""
        try:
            # Get chronological conversation data
            all_memories = await self.mem0_service.search_intimate_memories(
                query="conversation interaction relationship",
                user_id=user_id,
                limit=30
            )
            
            return self._identify_relationship_phase(all_memories)
        except Exception as e:
            logger.error(f"Relationship phase detection failed for {user_id}: {e}")
            return {}

    async def track_inside_references(self, user_id: str) -> List[str]:
        """Identify shared references and inside jokes developing"""
        try:
            reference_memories = await self.mem0_service.search_intimate_memories(
                query="remember mentioned before recall previous",
                user_id=user_id,
                limit=15
            )
            
            return self._extract_inside_references(reference_memories)
        except Exception as e:
            logger.error(f"Inside reference tracking failed for {user_id}: {e}")
            return []

    def _analyze_trust_progression(self, memories: Dict) -> Dict:
        """Analyze how trust has built over time"""
        results = memories.get("results", [])
        if not results:
            return {"trust_level": "initial", "milestones": []}

        trust_indicators = {
            "surface": 0,
            "developing": 0,
            "established": 0,
            "deep": 0
        }

        milestones = []
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            
            # Assess trust level of this interaction
            if any(word in memory_text for word in ["secret", "never told", "private"]):
                trust_indicators["deep"] += 1
                milestones.append({
                    "type": "deep_sharing",
                    "memory": memory.get("memory"),
                    "timestamp": metadata.get("timestamp")
                })
            elif any(word in memory_text for word in ["personal", "share", "open"]):
                trust_indicators["established"] += 1
                milestones.append({
                    "type": "personal_sharing", 
                    "memory": memory.get("memory"),
                    "timestamp": metadata.get("timestamp")
                })
            elif any(word in memory_text for word in ["comfortable", "trust"]):
                trust_indicators["developing"] += 1

        # Determine overall trust level
        if trust_indicators["deep"] >= 2:
            trust_level = "deep"
        elif trust_indicators["established"] >= 3:
            trust_level = "established"
        elif trust_indicators["developing"] >= 2:
            trust_level = "developing"
        else:
            trust_level = "surface"

        return {
            "trust_level": trust_level,
            "milestones": milestones[-5:],  # Last 5 significant moments
            "trust_indicators": trust_indicators
        }

    def _analyze_communication_dna(self, memories: Dict) -> Dict:
        """Extract user's unique communication preferences"""
        results = memories.get("results", [])
        if not results:
            return {}

        communication_patterns = {
            "humor_style": "unknown",
            "comfort_preference": "unknown", 
            "energy_matching": "unknown",
            "response_preference": "unknown",
            "emotional_processing": "unknown"
        }

        humor_indicators = {"wordplay": 0, "sarcasm": 0, "gentle": 0, "none": 0}
        comfort_indicators = {"validation": 0, "problem_solving": 0, "presence": 0}
        energy_indicators = {"high_energy": 0, "contemplative": 0, "adaptive": 0}

        for memory in results:
            memory_text = memory.get("memory", "").lower()
            
            # Analyze humor style
            if any(word in memory_text for word in ["joke", "funny", "laugh"]):
                if any(word in memory_text for word in ["clever", "witty"]):
                    humor_indicators["wordplay"] += 1
                elif any(word in memory_text for word in ["sarcastic", "ironic"]):
                    humor_indicators["sarcasm"] += 1
                else:
                    humor_indicators["gentle"] += 1

            # Analyze comfort preference
            if any(word in memory_text for word in ["understand", "validate", "feel"]):
                comfort_indicators["validation"] += 1
            elif any(word in memory_text for word in ["solve", "fix", "advice"]):
                comfort_indicators["problem_solving"] += 1
            elif any(word in memory_text for word in ["listen", "here", "present"]):
                comfort_indicators["presence"] += 1

            # Analyze energy preference
            if any(word in memory_text for word in ["excited", "energetic", "enthusiastic"]):
                energy_indicators["high_energy"] += 1
            elif any(word in memory_text for word in ["thoughtful", "reflect", "consider"]):
                energy_indicators["contemplative"] += 1
            else:
                energy_indicators["adaptive"] += 1

        # Determine dominant patterns
        communication_patterns["humor_style"] = max(humor_indicators, key=humor_indicators.get)
        communication_patterns["comfort_preference"] = max(comfort_indicators, key=comfort_indicators.get)
        communication_patterns["energy_matching"] = max(energy_indicators, key=energy_indicators.get)

        return communication_patterns

    def _identify_relationship_phase(self, memories: Dict) -> Dict:
        """Determine current relationship phase"""
        results = memories.get("results", [])
        if not results:
            return {"phase": "initial_curiosity", "conversation_count": 0}

        conversation_count = len(results)
        
        # Analyze interaction depth
        intimacy_score = 0
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            intimacy_level = metadata.get("intimacy_level", "low")
            
            if intimacy_level == "high":
                intimacy_score += 3
            elif intimacy_level == "medium":
                intimacy_score += 2
            else:
                intimacy_score += 1

        avg_intimacy = intimacy_score / conversation_count if conversation_count > 0 else 0

        # Determine phase based on conversation count and intimacy
        if conversation_count < 5:
            phase = "initial_curiosity"
        elif conversation_count < 15 and avg_intimacy < 2:
            phase = "growing_trust"
        elif conversation_count < 30 and avg_intimacy >= 2:
            phase = "emotional_availability"
        else:
            phase = "intimate_companionship"

        return {
            "phase": phase,
            "conversation_count": conversation_count,
            "avg_intimacy_score": avg_intimacy,
            "progression_indicators": self._get_progression_indicators(phase)
        }

    def _get_progression_indicators(self, phase: str) -> List[str]:
        """Get characteristics of current relationship phase"""
        phase_indicators = {
            "initial_curiosity": [
                "polite exploration",
                "basic information sharing",
                "testing boundaries"
            ],
            "growing_trust": [
                "personal details emerging",
                "increased comfort",
                "seeking AI's opinion"
            ],
            "emotional_availability": [
                "sharing struggles",
                "seeking emotional support",
                "vulnerable moments"
            ],
            "intimate_companionship": [
                "inside references",
                "comfortable silence",
                "deep emotional connection"
            ]
        }
        return phase_indicators.get(phase, [])

    def _extract_inside_references(self, memories: Dict) -> List[str]:
        """Find developing inside jokes and shared references"""
        results = memories.get("results", [])
        if not results:
            return []

        inside_references = []
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            
            # Look for callback references
            if any(phrase in memory_text for phrase in ["remember when", "like before", "as we discussed"]):
                inside_references.append(memory.get("memory"))

        return inside_references[-10:]  # Last 10 references
