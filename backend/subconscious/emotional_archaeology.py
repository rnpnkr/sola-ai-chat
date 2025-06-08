from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from memory.mem0_async_service import IntimateMemoryService

logger = logging.getLogger(__name__)

class EmotionalArchaeology:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service

    async def mine_vulnerability_moments(self, user_id: str) -> List[Dict]:
        """Extract times user opened up emotionally"""
        try:
            vulnerable_memories = await self.mem0_service.search_intimate_memories(
                query="vulnerable scared worried personal sharing afraid anxious fear",
                user_id=user_id,
                limit=15
            )
            
            return self._analyze_vulnerability_patterns(vulnerable_memories)
        except Exception as e:
            logger.error(f"Vulnerability mining failed for {user_id}: {e}")
            return []

    async def extract_joy_patterns(self, user_id: str) -> List[Dict]:
        """Identify what genuinely makes user happy"""
        try:
            joy_memories = await self.mem0_service.search_intimate_memories(
                query="happy excited grateful celebrate achievement joy love",
                user_id=user_id,
                limit=15
            )
            
            return self._analyze_joy_patterns(joy_memories)
        except Exception as e:
            logger.error(f"Joy pattern extraction failed for {user_id}: {e}")
            return []

    async def map_pain_points(self, user_id: str) -> List[Dict]:
        """Find recurring struggles and emotional triggers"""
        try:
            pain_memories = await self.mem0_service.search_intimate_memories(
                query="stressed struggle difficult problem upset frustrated",
                user_id=user_id,
                limit=15
            )
            
            return self._analyze_pain_patterns(pain_memories)
        except Exception as e:
            logger.error(f"Pain point mapping failed for {user_id}: {e}")
            return []

    async def track_growth_arcs(self, user_id: str) -> Dict:
        """How user has evolved emotionally over time"""
        try:
            # Get memories from different time periods
            all_memories = await self.mem0_service.search_intimate_memories(
                query="growth change better improve learned progress",
                user_id=user_id,
                limit=20
            )
            
            return self._track_emotional_evolution(all_memories)
        except Exception as e:
            logger.error(f"Growth tracking failed for {user_id}: {e}")
            return {}

    def _analyze_vulnerability_patterns(self, memories: Dict) -> List[Dict]:
        """Analyze vulnerability moments for patterns"""
        results = memories.get("results", [])
        if not results:
            return []

        vulnerability_patterns = []
        for memory in results:
            memory_text = memory.get("memory", "")
            metadata = memory.get("metadata", {})
            
            # Extract vulnerability context
            vulnerability_level = self._assess_vulnerability_level(memory_text)
            emotional_context = metadata.get("emotional_context", {})
            
            vulnerability_patterns.append({
                "memory": memory_text,
                "vulnerability_level": vulnerability_level,
                "emotional_context": emotional_context,
                "timestamp": metadata.get("timestamp"),
                "triggers": self._identify_vulnerability_triggers(memory_text)
            })

        return vulnerability_patterns

    def _analyze_joy_patterns(self, memories: Dict) -> List[Dict]:
        """Analyze what brings user joy"""
        results = memories.get("results", [])
        if not results:
            return []

        joy_patterns = []
        for memory in results:
            memory_text = memory.get("memory", "")
            metadata = memory.get("metadata", {})
            
            joy_triggers = self._identify_joy_triggers(memory_text)
            intensity = self._assess_joy_intensity(memory_text)
            
            joy_patterns.append({
                "memory": memory_text,
                "joy_triggers": joy_triggers,
                "intensity": intensity,
                "timestamp": metadata.get("timestamp"),
                "context": metadata.get("emotional_context", {})
            })

        return joy_patterns

    def _analyze_pain_patterns(self, memories: Dict) -> List[Dict]:
        """Analyze recurring pain points and triggers"""
        results = memories.get("results", [])
        if not results:
            return []

        pain_patterns = []
        for memory in results:
            memory_text = memory.get("memory", "")
            metadata = memory.get("metadata", {})
            
            pain_triggers = self._identify_pain_triggers(memory_text)
            severity = self._assess_pain_severity(memory_text)
            
            pain_patterns.append({
                "memory": memory_text,
                "pain_triggers": pain_triggers,
                "severity": severity,
                "timestamp": metadata.get("timestamp"),
                "coping_mechanisms": self._identify_coping_responses(memory_text)
            })

        return pain_patterns

    def _assess_vulnerability_level(self, text: str) -> str:
        """Assess how vulnerable/open the sharing was"""
        vulnerability_indicators = {
            "high": ["secret", "never told", "personal", "private", "scared", "afraid"],
            "medium": ["worried", "concerned", "nervous", "unsure"],
            "low": ["think", "maybe", "probably"]
        }
        
        text_lower = text.lower()
        high_count = sum(1 for indicator in vulnerability_indicators["high"] if indicator in text_lower)
        medium_count = sum(1 for indicator in vulnerability_indicators["medium"] if indicator in text_lower)
        
        if high_count >= 2:
            return "high"
        elif high_count >= 1 or medium_count >= 2:
            return "medium"
        else:
            return "low"

    def _identify_vulnerability_triggers(self, text: str) -> List[str]:
        """What made them feel vulnerable"""
        triggers = []
        trigger_keywords = {
            "relationships": ["family", "friend", "partner", "relationship"],
            "work": ["job", "work", "career", "boss"],
            "health": ["sick", "health", "medical", "doctor"],
            "finances": ["money", "financial", "expensive", "afford"],
            "self_worth": ["failure", "mistake", "wrong", "stupid"]
        }
        
        text_lower = text.lower()
        for category, keywords in trigger_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                triggers.append(category)
        
        return triggers

    def _identify_joy_triggers(self, text: str) -> List[str]:
        """What brings them joy"""
        triggers = []
        joy_keywords = {
            "achievement": ["accomplished", "proud", "succeeded", "won"],
            "relationships": ["friend", "family", "loved", "connected"],
            "creativity": ["created", "made", "art", "music", "write"],
            "nature": ["outside", "nature", "walk", "sunshine"],
            "learning": ["learned", "discovered", "understood", "knowledge"]
        }
        
        text_lower = text.lower()
        for category, keywords in joy_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                triggers.append(category)
        
        return triggers

    def _assess_joy_intensity(self, text: str) -> str:
        """How intense was the joy"""
        high_intensity = ["amazing", "incredible", "best", "perfect", "love"]
        medium_intensity = ["good", "happy", "nice", "pleased"]
        
        text_lower = text.lower()
        if any(word in text_lower for word in high_intensity):
            return "high"
        elif any(word in text_lower for word in medium_intensity):
            return "medium"
        else:
            return "low"

    def _identify_pain_triggers(self, text: str) -> List[str]:
        """What causes them stress/pain"""
        triggers = []
        pain_keywords = {
            "work_stress": ["deadline", "pressure", "overwhelmed", "busy"],
            "relationship_conflict": ["fight", "argument", "disagree", "tension"],
            "financial_pressure": ["expensive", "afford", "money", "budget"],
            "health_concerns": ["tired", "sick", "pain", "exhausted"],
            "self_criticism": ["failure", "mistake", "stupid", "wrong"]
        }
        
        text_lower = text.lower()
        for category, keywords in pain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                triggers.append(category)
        
        return triggers

    def _assess_pain_severity(self, text: str) -> str:
        """How severe was the pain/stress"""
        high_severity = ["terrible", "awful", "worst", "devastating", "crushing"]
        medium_severity = ["difficult", "hard", "tough", "stressful"]
        
        text_lower = text.lower()
        if any(word in text_lower for word in high_severity):
            return "high"
        elif any(word in text_lower for word in medium_severity):
            return "medium"
        else:
            return "low"

    def _identify_coping_responses(self, text: str) -> List[str]:
        """How they cope with pain/stress"""
        coping_mechanisms = []
        coping_keywords = {
            "social_support": ["talked", "friend", "help", "support"],
            "self_care": ["rest", "sleep", "exercise", "relax"],
            "problem_solving": ["plan", "solve", "figure", "organize"],
            "avoidance": ["ignore", "avoid", "escape", "distract"]
        }
        
        text_lower = text.lower()
        for mechanism, keywords in coping_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                coping_mechanisms.append(mechanism)
        
        return coping_mechanisms

    def _track_emotional_evolution(self, memories: Dict) -> Dict:
        """Track how user has grown/changed over time"""
        results = memories.get("results", [])
        if not results:
            return {}

        # Group by time periods and analyze evolution
        evolution = {
            "emotional_maturity": "developing",
            "coping_skills": "improving",
            "self_awareness": "growing",
            "growth_areas": []
        }

        growth_indicators = []
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            if any(word in memory_text for word in ["learned", "realized", "understand", "growth"]):
                growth_indicators.append(memory_text)

        if len(growth_indicators) > 3:
            evolution["emotional_maturity"] = "advanced"
            evolution["self_awareness"] = "high"

        return evolution
