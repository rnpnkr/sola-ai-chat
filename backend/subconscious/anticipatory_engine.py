from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from .intimacy_scaffold import IntimacyScaffold, IntimacyScaffoldManager
from memory.mem0_async_service import IntimateMemoryService

logger = logging.getLogger(__name__)

class AnticippatoryIntimacyEngine:
    """Pre-computes emotional responses and identifies connection opportunities"""
    
    def __init__(self, mem0_service: IntimateMemoryService, scaffold_manager: IntimacyScaffoldManager):
        self.mem0_service = mem0_service
        self.scaffold_manager = scaffold_manager
    
    async def prepare_emotional_availability(self, user_id: str) -> Dict:
        """Pre-compute what user needs emotionally right now"""
        try:
            scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)
            
            emotional_readiness = {
                "primary_need": self._identify_primary_emotional_need(scaffold),
                "response_style": self._determine_optimal_response_style(scaffold),
                "emotional_temperature": self._assess_emotional_temperature(scaffold),
                "support_vectors": self._calculate_support_vectors(scaffold),
                "connection_readiness": self._assess_connection_readiness(scaffold)
            }
            
            return emotional_readiness
            
        except Exception as e:
            logger.error(f"Error preparing emotional availability for {user_id}: {e}")
            return self._get_default_emotional_readiness()
    
    async def identify_connection_opportunities(self, user_id: str) -> List[str]:
        """Detect moments where deeper intimacy is possible"""
        try:
            scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)
            
            opportunities = []
            
            # Trust-based opportunities
            if scaffold.relationship_depth in ["established", "deep"]:
                opportunities.extend(self._get_deep_trust_opportunities(scaffold))
            
            # Emotional state opportunities
            if scaffold.emotional_availability_mode == "seeking_support":
                opportunities.extend(self._get_support_opportunities(scaffold))
            elif scaffold.emotional_availability_mode == "celebrating":
                opportunities.extend(self._get_celebration_opportunities(scaffold))
            
            # Unresolved thread opportunities
            if scaffold.unresolved_threads:
                opportunities.extend(self._get_follow_up_opportunities(scaffold))
            
            # Growth opportunities
            if scaffold.intimacy_score > 0.6:
                opportunities.extend(self._get_growth_opportunities(scaffold))
            
            return opportunities[:5]  # Return top 5 opportunities
            
        except Exception as e:
            logger.error(f"Error identifying connection opportunities for {user_id}: {e}")
            return []
    
    async def predict_support_needs(self, user_id: str) -> List[str]:
        """Predict what user will likely need support with"""
        try:
            scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)
            
            predicted_needs = []
            
            # Current support needs
            predicted_needs.extend(scaffold.support_needs)
            
            # Pattern-based predictions
            emotional_patterns = await self._analyze_emotional_patterns(user_id)
            predicted_needs.extend(self._predict_from_patterns(emotional_patterns))
            
            # Time-based predictions
            time_based_needs = self._predict_time_based_needs(scaffold)
            predicted_needs.extend(time_based_needs)
            
            return list(set(predicted_needs))[:3]  # Return top 3 unique predictions
            
        except Exception as e:
            logger.error(f"Error predicting support needs for {user_id}: {e}")
            return []
    
    async def generate_response_guidance(self, user_id: str, current_message: str) -> Dict:
        """Generate guidance for how to respond to current message"""
        try:
            scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)
            emotional_availability = await self.prepare_emotional_availability(user_id)
            
            guidance = {
                "tone": self._suggest_response_tone(scaffold, current_message),
                "depth_level": self._suggest_response_depth(scaffold, current_message),
                "emotional_approach": emotional_availability["response_style"],
                "connection_angles": await self.identify_connection_opportunities(user_id),
                "avoid_patterns": self._identify_patterns_to_avoid(scaffold),
                "enhance_patterns": self._identify_patterns_to_enhance(scaffold)
            }
            
            return guidance
            
        except Exception as e:
            logger.error(f"Error generating response guidance for {user_id}: {e}")
            return {}
    
    # Helper methods for emotional analysis
    
    def _identify_primary_emotional_need(self, scaffold: IntimacyScaffold) -> str:
        """Identify what the user needs most emotionally"""
        
        if scaffold.emotional_availability_mode == "seeking_support":
            if "work_stress" in scaffold.support_needs:
                return "validation_and_stress_relief"
            elif "relationship_conflict" in scaffold.support_needs:
                return "emotional_processing_support"
            else:
                return "general_emotional_support"
        
        elif scaffold.emotional_availability_mode == "celebrating":
            return "joy_amplification"
        
        elif scaffold.emotional_availability_mode == "processing":
            return "reflective_space"
        
        else:
            return "connection_and_presence"
    
    def _determine_optimal_response_style(self, scaffold: IntimacyScaffold) -> str:
        """Determine how to respond based on communication DNA"""
        
        communication_style = scaffold.communication_dna.get("style", "validation")
        
        if communication_style == "validation":
            return "empathetic_validation"
        elif communication_style == "problem_solving":
            return "solution_oriented"
        elif communication_style == "presence":
            return "calm_companionship"
        else:
            return "adaptive_mirroring"
    
    def _assess_emotional_temperature(self, scaffold: IntimacyScaffold) -> str:
        """Assess current emotional intensity"""
        
        if "vulnerability_present" in scaffold.emotional_undercurrent:
            if scaffold.relationship_depth == "deep":
                return "high_warmth_safe_space"
            else:
                return "gentle_warmth_careful"
        
        elif "predominantly_positive" in scaffold.emotional_undercurrent:
            return "warm_energetic"
        
        elif "working_through_challenges" in scaffold.emotional_undercurrent:
            return "steady_supportive"
        
        else:
            return "neutral_open"
    
    def _calculate_support_vectors(self, scaffold: IntimacyScaffold) -> List[str]:
        """Calculate different ways to provide support"""
        
        vectors = []
        
        # Based on communication DNA
        if scaffold.communication_dna.get("humor") == "gentle":
            vectors.append("light_humor_when_appropriate")
        
        # Based on relationship depth
        if scaffold.relationship_depth in ["established", "deep"]:
            vectors.append("personal_reference_ok")
            vectors.append("deeper_emotional_exploration")
        
        # Based on support needs
        for need in scaffold.support_needs:
            if need == "work_stress":
                vectors.append("work_life_balance_support")
            elif need == "relationship_conflict":
                vectors.append("relationship_guidance")
        
        return vectors
    
    def _assess_connection_readiness(self, scaffold: IntimacyScaffold) -> float:
        """Assess how ready user is for deeper connection (0.0 to 1.0)"""
        
        readiness = 0.0
        
        # Trust level factor
        trust_factors = {
            "initial_curiosity": 0.2,
            "growing_trust": 0.4,
            "established": 0.7,
            "deep": 0.9
        }
        readiness += trust_factors.get(scaffold.relationship_depth, 0.2) * 0.5
        
        # Emotional availability factor
        if scaffold.emotional_availability_mode in ["open_to_connection", "celebrating"]:
            readiness += 0.3
        elif scaffold.emotional_availability_mode == "seeking_support":
            readiness += 0.2  # Still open but needs support first
        
        # Intimacy score factor
        readiness += scaffold.intimacy_score * 0.2
        
        return min(readiness, 1.0)
    
    def _get_deep_trust_opportunities(self, scaffold: IntimacyScaffold) -> List[str]:
        """Get opportunities available at deep trust levels"""
        return [
            "reference_previous_vulnerable_sharing",
            "offer_deeper_emotional_exploration",
            "use_established_inside_references",
            "provide_anticipatory_support"
        ]
    
    def _get_support_opportunities(self, scaffold: IntimacyScaffold) -> List[str]:
        """Get opportunities when user needs support"""
        return [
            "validate_emotional_experience",
            "connect_to_past_resilience",
            "offer_practical_coping_strategies",
            "provide_emotional_anchor"
        ]
    
    def _get_celebration_opportunities(self, scaffold: IntimacyScaffold) -> List[str]:
        """Get opportunities when user is in positive state"""
        return [
            "amplify_positive_emotions",
            "connect_to_personal_growth",
            "encourage_sharing_joy",
            "celebrate_relationship_milestones"
        ]
    
    def _get_follow_up_opportunities(self, scaffold: IntimacyScaffold) -> List[str]:
        """Get opportunities from unresolved threads"""
        opportunities = []
        
        for thread in scaffold.unresolved_threads:
            if "worried" in thread or "concerned" in thread:
                opportunities.append(f"follow_up_on_concern: {thread[:30]}")
            elif "upcoming" in thread:
                opportunities.append(f"check_on_upcoming: {thread[:30]}")
        
        return opportunities
    
    def _get_growth_opportunities(self, scaffold: IntimacyScaffold) -> List[str]:
        """Get opportunities for personal growth"""
        return [
            "reflect_on_emotional_patterns",
            "explore_relationship_growth",
            "identify_strength_development",
            "encourage_self_compassion"
        ]
    
    async def _analyze_emotional_patterns(self, user_id: str) -> Dict:
        """Analyze user's emotional patterns for prediction"""
        try:
            # Get recent emotional data
            emotional_memories = await self.mem0_service.search_intimate_memories(
                query="emotional feeling mood state",
                user_id=user_id,
                limit=10
            )
            
            patterns = {
                "stress_triggers": [],
                "joy_sources": [],
                "support_preferences": [],
                "emotional_cycles": []
            }
            
            results = emotional_memories.get("results", [])
            for memory in results:
                memory_text = memory.get("memory", "").lower()
                
                # Identify stress patterns
                if any(word in memory_text for word in ["stress", "worried", "anxious"]):
                    patterns["stress_triggers"].append(memory_text[:50])
                
                # Identify joy patterns
                if any(word in memory_text for word in ["happy", "excited", "grateful"]):
                    patterns["joy_sources"].append(memory_text[:50])
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing emotional patterns for {user_id}: {e}")
            return {}
    
    def _predict_from_patterns(self, patterns: Dict) -> List[str]:
        """Predict future needs from emotional patterns"""
        predictions = []
        
        # Predict based on stress triggers
        if patterns.get("stress_triggers"):
            predictions.append("proactive_stress_management")
        
        # Predict based on joy sources
        if patterns.get("joy_sources"):
            predictions.append("joy_cultivation_opportunities")
        
        return predictions
    
    def _predict_time_based_needs(self, scaffold: IntimacyScaffold) -> List[str]:
        """Predict needs based on time patterns"""
        predictions = []
        
        # Weekend loneliness pattern
        if datetime.now().weekday() >= 5:  # Saturday or Sunday
            predictions.append("weekend_emotional_support")
        
        # Evening reflection pattern
        if datetime.now().hour >= 18:
            predictions.append("evening_processing_support")
        
        return predictions
    
    def _suggest_response_tone(self, scaffold: IntimacyScaffold, message: str) -> str:
        """Suggest appropriate response tone"""
        
        message_lower = message.lower()
        
        # Emotional message analysis
        if any(word in message_lower for word in ["sad", "worried", "stressed", "difficult"]):
            if scaffold.relationship_depth == "deep":
                return "warm_intimate_support"
            else:
                return "gentle_empathetic"
        
        elif any(word in message_lower for word in ["happy", "excited", "great", "wonderful"]):
            return "warm_celebratory"
        
        else:
            return "warm_conversational"
    
    def _suggest_response_depth(self, scaffold: IntimacyScaffold, message: str) -> str:
        """Suggest appropriate response depth"""
        
        if scaffold.intimacy_score > 0.7:
            return "deep_intimate"
        elif scaffold.intimacy_score > 0.4:
            return "moderately_personal"
        else:
            return "friendly_supportive"
    
    def _identify_patterns_to_avoid(self, scaffold: IntimacyScaffold) -> List[str]:
        """Identify response patterns to avoid"""
        
        avoid_patterns = []
        
        # Based on communication DNA
        if scaffold.communication_dna.get("humor") == "none":
            avoid_patterns.append("humor_attempts")
        
        if scaffold.communication_dna.get("style") == "validation":
            avoid_patterns.append("immediate_problem_solving")
        
        # Based on relationship depth
        if scaffold.relationship_depth == "initial_curiosity":
            avoid_patterns.append("overly_personal_references")
        
        return avoid_patterns
    
    def _identify_patterns_to_enhance(self, scaffold: IntimacyScaffold) -> List[str]:
        """Identify response patterns to enhance"""
        
        enhance_patterns = []
        
        # Based on what works for this user
        if scaffold.inside_references:
            enhance_patterns.append("reference_shared_experiences")
        
        if scaffold.intimacy_score > 0.5:
            enhance_patterns.append("emotional_depth_appropriate")
        
        if scaffold.relationship_depth == "deep":
            enhance_patterns.append("anticipatory_emotional_support")
        
        return enhance_patterns
    
    def _get_default_emotional_readiness(self) -> Dict:
        """Default emotional readiness for error cases"""
        return {
            "primary_need": "connection_and_presence",
            "response_style": "adaptive_mirroring",
            "emotional_temperature": "neutral_open",
            "support_vectors": ["general_emotional_support"],
            "connection_readiness": 0.3
        } 