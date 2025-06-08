from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from memory.mem0_async_service import IntimateMemoryService
from .intimacy_scaffold import IntimacyScaffoldManager
import statistics

logger = logging.getLogger(__name__)

class AdvancedMemoryAnalytics:
    """Advanced analytics for memory patterns and relationship health"""
    
    def __init__(self, mem0_service: IntimateMemoryService, scaffold_manager: IntimacyScaffoldManager):
        self.mem0_service = mem0_service
        self.scaffold_manager = scaffold_manager
    
    async def conversation_depth_scoring(self, user_id: str) -> Dict:
        """Score intimacy progression over time"""
        try:
            # Get recent conversations with intimacy metadata
            conversations = await self.mem0_service.search_intimate_memories(
                query="conversation interaction",
                user_id=user_id,
                limit=50
            )
            
            depth_analysis = self._analyze_conversation_depths(conversations)
            
            return {
                "user_id": user_id,
                "overall_depth_score": depth_analysis["overall_score"],
                "depth_trend": depth_analysis["trend"],
                "conversation_scores": depth_analysis["individual_scores"],
                "depth_distribution": depth_analysis["distribution"],
                "intimacy_peaks": depth_analysis["peaks"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scoring conversation depth for {user_id}: {e}")
            return {"overall_depth_score": 0.0, "depth_trend": "unknown"}
    
    async def emotional_pattern_analysis(self, user_id: str) -> Dict:
        """Identify emotional cycles and triggers"""
        try:
            # Get emotional memories over extended period
            emotional_data = await self.mem0_service.search_intimate_memories(
                query="emotional feeling mood vulnerable joy stress",
                user_id=user_id,
                limit=100
            )
            
            pattern_analysis = self._identify_emotional_patterns(emotional_data)
            
            return {
                "user_id": user_id,
                "emotional_cycles": pattern_analysis["cycles"],
                "trigger_patterns": pattern_analysis["triggers"],
                "emotional_resilience": pattern_analysis["resilience"],
                "mood_variability": pattern_analysis["variability"],
                "support_effectiveness": pattern_analysis["support_effectiveness"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotional patterns for {user_id}: {e}")
            return {"emotional_cycles": [], "trigger_patterns": {}}
    
    async def relationship_health_metrics(self, user_id: str) -> Dict:
        """Comprehensive relationship quality assessment"""
        try:
            # Get current scaffold
            scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)
            
            # Get various analytics
            depth_scores = await self.conversation_depth_scoring(user_id)
            emotional_patterns = await self.emotional_pattern_analysis(user_id)
            
            health_metrics = self._calculate_relationship_health(scaffold, depth_scores, emotional_patterns)
            
            return {
                "user_id": user_id,
                "overall_health_score": health_metrics["overall"],
                "dimension_scores": health_metrics["dimensions"],
                "health_indicators": health_metrics["indicators"],
                "improvement_areas": health_metrics["improvements"],
                "relationship_strengths": health_metrics["strengths"],
                "risk_factors": health_metrics["risks"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating relationship health for {user_id}: {e}")
            return {"overall_health_score": 0.5}
    
    async def memory_quality_assessment(self, user_id: str) -> Dict:
        """Assess quality and richness of stored memories"""
        try:
            # Get all user memories
            all_memories = await self.mem0_service.search_intimate_memories(
                query="",  # Get all memories
                user_id=user_id,
                limit=200
            )
            
            quality_metrics = self._assess_memory_quality(all_memories)
            
            return {
                "user_id": user_id,
                "memory_richness": quality_metrics["richness"],
                "emotional_diversity": quality_metrics["diversity"],
                "temporal_coverage": quality_metrics["coverage"],
                "memory_coherence": quality_metrics["coherence"],
                "total_memories": quality_metrics["total"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing memory quality for {user_id}: {e}")
            return {"memory_richness": 0.0}
    
    def _analyze_conversation_depths(self, conversations: Dict) -> Dict:
        """Analyze depth of individual conversations"""
        results = conversations.get("results", [])
        
        individual_scores = []
        intimacy_levels = []
        timestamps = []
        
        for conversation in results:
            metadata = conversation.get("metadata", {})
            intimacy_level = metadata.get("intimacy_level", "low")
            timestamp = metadata.get("timestamp")
            
            # Convert intimacy level to score
            level_scores = {"low": 0.2, "medium": 0.6, "high": 0.9, "system_analysis": 0.5}
            score = level_scores.get(intimacy_level, 0.2)
            
            individual_scores.append({
                "timestamp": timestamp,
                "intimacy_level": intimacy_level,
                "depth_score": score,
                "memory": conversation.get("memory", "")[:100]
            })
            
            intimacy_levels.append(intimacy_level)
            if timestamp:
                timestamps.append(timestamp)
        
        # Calculate overall metrics
        scores = [item["depth_score"] for item in individual_scores]
        overall_score = statistics.mean(scores) if scores else 0.0
        
        # Calculate trend
        if len(scores) >= 3:
            recent_avg = statistics.mean(scores[-5:])  # Last 5 conversations
            older_avg = statistics.mean(scores[:-5]) if len(scores) > 5 else recent_avg
            trend = "improving" if recent_avg > older_avg + 0.1 else "stable" if abs(recent_avg - older_avg) <= 0.1 else "declining"
        else:
            trend = "insufficient_data"
        
        # Distribution analysis
        distribution = {
            "low": intimacy_levels.count("low"),
            "medium": intimacy_levels.count("medium"), 
            "high": intimacy_levels.count("high")
        }
        
        # Find intimacy peaks
        peaks = [item for item in individual_scores if item["depth_score"] >= 0.8][-5:]
        
        return {
            "overall_score": overall_score,
            "trend": trend,
            "individual_scores": individual_scores[-20:],  # Last 20 conversations
            "distribution": distribution,
            "peaks": peaks
        }
    
    def _identify_emotional_patterns(self, emotional_data: Dict) -> Dict:
        """Identify recurring emotional patterns"""
        results = emotional_data.get("results", [])
        
        emotional_entries = []
        trigger_counts = {}
        resilience_indicators = []
        
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            timestamp = metadata.get("timestamp")
            
            # Categorize emotional content
            emotional_type = "neutral"
            if any(word in memory_text for word in ["sad", "worried", "anxious", "stressed"]):
                emotional_type = "negative"
            elif any(word in memory_text for word in ["happy", "excited", "grateful", "joy"]):
                emotional_type = "positive"
            elif any(word in memory_text for word in ["vulnerable", "scared", "uncertain"]):
                emotional_type = "vulnerable"
            
            emotional_entries.append({
                "timestamp": timestamp,
                "type": emotional_type,
                "content": memory_text[:100]
            })
            
            # Track triggers
            triggers = self._extract_triggers(memory_text)
            for trigger in triggers:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
            
            # Track resilience indicators
            if any(word in memory_text for word in ["overcome", "handle", "cope", "resilient", "better"]):
                resilience_indicators.append({
                    "timestamp": timestamp,
                    "content": memory_text[:100]
                })
        
        # Analyze cycles
        cycles = self._detect_emotional_cycles(emotional_entries)
        
        # Calculate variability
        emotion_types = [entry["type"] for entry in emotional_entries]
        variability = len(set(emotion_types)) / len(emotion_types) if emotion_types else 0
        
        # Support effectiveness (recovery patterns)
        support_effectiveness = len(resilience_indicators) / max(len(emotional_entries), 1)
        
        return {
            "cycles": cycles,
            "triggers": trigger_counts,
            "resilience": {
                "indicators": resilience_indicators[-10:],
                "resilience_ratio": support_effectiveness
            },
            "variability": variability,
            "support_effectiveness": support_effectiveness
        }
    
    def _calculate_relationship_health(self, scaffold, depth_scores: Dict, emotional_patterns: Dict) -> Dict:
        """Calculate comprehensive relationship health metrics"""
        
        # Dimension scores (0.0 to 1.0)
        dimensions = {
            "trust_level": self._score_trust_level(scaffold.relationship_depth),
            "emotional_safety": self._score_emotional_safety(scaffold, emotional_patterns),
            "communication_quality": depth_scores.get("overall_depth_score", 0.0),
            "intimacy_progression": scaffold.intimacy_score,
            "emotional_support": emotional_patterns.get("support_effectiveness", 0.0),
            "relationship_stability": self._score_stability(depth_scores.get("depth_trend", "stable"))
        }
        
        # Calculate overall health (weighted average)
        weights = {
            "trust_level": 0.25,
            "emotional_safety": 0.20,
            "communication_quality": 0.15,
            "intimacy_progression": 0.15,
            "emotional_support": 0.15,
            "relationship_stability": 0.10
        }
        
        overall_health = sum(dimensions[dim] * weights[dim] for dim in dimensions)
        
        # Health indicators
        indicators = self._generate_health_indicators(dimensions)
        
        # Areas for improvement
        improvements = [dim for dim, score in dimensions.items() if score < 0.6]
        
        # Relationship strengths
        strengths = [dim for dim, score in dimensions.items() if score > 0.8]
        
        # Risk factors
        risks = self._identify_risk_factors(scaffold, dimensions)
        
        return {
            "overall": overall_health,
            "dimensions": dimensions,
            "indicators": indicators,
            "improvements": improvements,
            "strengths": strengths,
            "risks": risks
        }
    
    def _assess_memory_quality(self, all_memories: Dict) -> Dict:
        """Assess quality and richness of memory store"""
        results = all_memories.get("results", [])
        
        if not results:
            return {
                "richness": 0.0,
                "diversity": 0.0,
                "coverage": 0.0,
                "coherence": 0.0,
                "total": 0
            }
        
        # Richness: variety of emotional content
        emotional_types = set()
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            if any(word in memory_text for word in ["happy", "joy", "excited"]):
                emotional_types.add("positive")
            if any(word in memory_text for word in ["sad", "worried", "stressed"]):
                emotional_types.add("negative")
            if any(word in memory_text for word in ["vulnerable", "personal", "private"]):
                emotional_types.add("vulnerable")
            if any(word in memory_text for word in ["growth", "learn", "progress"]):
                emotional_types.add("growth")
        
        richness = len(emotional_types) / 4.0  # Max 4 types
        
        # Diversity: unique content ratio
        unique_content = len(set(memory.get("memory", "") for memory in results))
        diversity = unique_content / len(results)
        
        # Temporal coverage: spread across time
        timestamps = [memory.get("metadata", {}).get("timestamp") for memory in results]
        valid_timestamps = [ts for ts in timestamps if ts]
        
        if len(valid_timestamps) >= 2:
            try:
                dates = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in valid_timestamps]
                date_range = (max(dates) - min(dates)).days
                coverage = min(date_range / 30.0, 1.0)  # Coverage over 30 days
            except:
                coverage = 0.5
        else:
            coverage = 0.0
        
        # Coherence: consistency of relationship progression
        coherence = self._calculate_memory_coherence(results)
        
        return {
            "richness": richness,
            "diversity": diversity,
            "coverage": coverage,
            "coherence": coherence,
            "total": len(results)
        }
    
    def _extract_triggers(self, text: str) -> List[str]:
        """Extract emotional triggers from text"""
        triggers = []
        trigger_keywords = {
            "work": ["work", "job", "boss", "deadline", "meeting"],
            "family": ["family", "parent", "sibling", "relative"],
            "health": ["sick", "pain", "tired", "medical", "doctor"],
            "financial": ["money", "expensive", "budget", "financial"],
            "social": ["friend", "social", "party", "relationship"],
            "personal": ["myself", "self", "identity", "confidence"]
        }
        
        text_lower = text.lower()
        for trigger_type, keywords in trigger_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                triggers.append(trigger_type)
        
        return triggers
    
    def _detect_emotional_cycles(self, emotional_entries: List[Dict]) -> List[Dict]:
        """Detect recurring emotional patterns"""
        if len(emotional_entries) < 5:
            return []
        
        # Group by emotional type and look for patterns
        cycles = []
        
        # Weekly pattern detection
        weekly_pattern = self._analyze_weekly_patterns(emotional_entries)
        if weekly_pattern:
            cycles.append(weekly_pattern)
        
        # Stress-recovery cycles
        stress_recovery = self._analyze_stress_recovery_cycles(emotional_entries)
        if stress_recovery:
            cycles.append(stress_recovery)
        
        return cycles
    
    def _analyze_weekly_patterns(self, entries: List[Dict]) -> Optional[Dict]:
        """Analyze weekly emotional patterns"""
        # This is a simplified pattern detection
        # In production, you'd use more sophisticated time series analysis
        negative_count = len([e for e in entries if e["type"] == "negative"])
        positive_count = len([e for e in entries if e["type"] == "positive"])
        
        if len(entries) > 10:
            return {
                "type": "weekly_pattern",
                "description": f"Shows {negative_count} negative and {positive_count} positive emotional episodes",
                "pattern_strength": min(abs(negative_count - positive_count) / len(entries), 1.0)
            }
        return None
    
    def _analyze_stress_recovery_cycles(self, entries: List[Dict]) -> Optional[Dict]:
        """Analyze stress and recovery patterns"""
        stress_events = [e for e in entries if e["type"] == "negative"]
        recovery_events = [e for e in entries if e["type"] == "positive"]
        
        if len(stress_events) > 2 and len(recovery_events) > 1:
            return {
                "type": "stress_recovery",
                "description": f"Shows pattern of {len(stress_events)} stress events followed by {len(recovery_events)} recovery periods",
                "recovery_ratio": len(recovery_events) / len(stress_events)
            }
        return None
    
    def _score_trust_level(self, relationship_depth: str) -> float:
        """Score trust level based on relationship depth"""
        trust_scores = {
            "initial_curiosity": 0.2,
            "growing_trust": 0.5,
            "established": 0.8,
            "deep": 1.0
        }
        return trust_scores.get(relationship_depth, 0.2)
    
    def _score_emotional_safety(self, scaffold, emotional_patterns: Dict) -> float:
        """Score emotional safety based on vulnerability and support"""
        vulnerability_comfort = 0.8 if "vulnerability_present" in scaffold.emotional_undercurrent else 0.4
        support_effectiveness = emotional_patterns.get("support_effectiveness", 0.5)
        
        return (vulnerability_comfort + support_effectiveness) / 2.0
    
    def _score_stability(self, trend: str) -> float:
        """Score relationship stability based on trend"""
        stability_scores = {
            "improving": 1.0,
            "stable": 0.8,
            "declining": 0.3,
            "insufficient_data": 0.5
        }
        return stability_scores.get(trend, 0.5)
    
    def _generate_health_indicators(self, dimensions: Dict) -> List[str]:
        """Generate health status indicators"""
        indicators = []
        
        if dimensions["trust_level"] > 0.8:
            indicators.append("Strong trust foundation established")
        
        if dimensions["emotional_safety"] > 0.7:
            indicators.append("High emotional safety and vulnerability comfort")
        
        if dimensions["intimacy_progression"] > 0.6:
            indicators.append("Healthy intimacy development")
        
        if dimensions["emotional_support"] > 0.7:
            indicators.append("Effective emotional support patterns")
        
        if all(score > 0.6 for score in dimensions.values()):
            indicators.append("Overall relationship health is good")
        
        return indicators
    
    def _identify_risk_factors(self, scaffold, dimensions: Dict) -> List[str]:
        """Identify potential relationship risk factors"""
        risks = []
        
        if dimensions["trust_level"] < 0.4:
            risks.append("Low trust levels may limit intimacy development")
        
        if dimensions["emotional_safety"] < 0.5:
            risks.append("Emotional safety concerns may inhibit vulnerability")
        
        if dimensions["relationship_stability"] < 0.5:
            risks.append("Relationship showing signs of instability")
        
        if len(scaffold.unresolved_threads) > 3:
            risks.append("Multiple unresolved concerns may impact relationship")
        
        if scaffold.emotional_availability_mode == "processing" and scaffold.intimacy_score < 0.3:
            risks.append("Extended processing mode in early relationship phase")
        
        return risks
    
    def _calculate_memory_coherence(self, results: List[Dict]) -> float:
        """Calculate coherence of memory progression"""
        # Simplified coherence calculation
        # Look for logical progression in relationship development
        
        if len(results) < 3:
            return 0.5
        
        # Check for progression in intimacy levels
        intimacy_levels = []
        for memory in results:
            metadata = memory.get("metadata", {})
            level = metadata.get("intimacy_level", "low")
            if level != "system_analysis":  # Skip system entries
                intimacy_levels.append(level)
        
        if not intimacy_levels:
            return 0.5
        
        # Simple progression check
        level_values = {"low": 1, "medium": 2, "high": 3}
        numeric_levels = [level_values.get(level, 1) for level in intimacy_levels]
        
        # Check if there's general upward trend
        if len(numeric_levels) >= 2:
            recent_avg = statistics.mean(numeric_levels[-5:]) if len(numeric_levels) >= 5 else statistics.mean(numeric_levels)
            early_avg = statistics.mean(numeric_levels[:5]) if len(numeric_levels) >= 10 else statistics.mean(numeric_levels[:-5]) if len(numeric_levels) > 5 else recent_avg
            
            progression = (recent_avg - early_avg) / 2.0  # Normalize
            coherence = 0.5 + min(max(progression, -0.5), 0.5)  # Clamp between 0 and 1
        else:
            coherence = 0.5
        
        return coherence 