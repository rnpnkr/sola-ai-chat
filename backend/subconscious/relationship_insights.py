from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from memory.mem0_async_service import IntimateMemoryService
from .intimacy_scaffold import IntimacyScaffoldManager
import json

logger = logging.getLogger(__name__)

class RelationshipInsightsEngine:
    """Generates deep insights into relationship progression and emotional journey"""
    
    def __init__(self, mem0_service: IntimateMemoryService, scaffold_manager: IntimacyScaffoldManager):
        self.mem0_service = mem0_service
        self.scaffold_manager = scaffold_manager
    
    async def generate_intimacy_timeline(self, user_id: str) -> Dict:
        """Generate timeline of relationship depth progression"""
        try:
            # Get all relationship evolution entries
            evolution_memories = await self.mem0_service.search_intimate_memories(
                query="relationship_evolution system_analysis",
                user_id=user_id,
                limit=20
            )
            
            timeline_data = self._build_intimacy_timeline(evolution_memories)
            
            return {
                "user_id": user_id,
                "timeline_points": timeline_data["points"],
                "relationship_milestones": timeline_data["milestones"],
                "intimacy_progression": timeline_data["progression"],
                "current_phase": timeline_data["current_phase"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating intimacy timeline for {user_id}: {e}")
            return self._get_default_timeline()
    
    async def analyze_emotional_journey(self, user_id: str) -> Dict:
        """Map user's emotional growth patterns over time"""
        try:
            # Get emotional memories over time
            emotional_memories = await self.mem0_service.search_intimate_memories(
                query="emotional feeling vulnerable joy growth",
                user_id=user_id,
                limit=30
            )
            
            journey_analysis = self._analyze_emotional_progression(emotional_memories)
            
            return {
                "user_id": user_id,
                "emotional_themes": journey_analysis["themes"],
                "growth_patterns": journey_analysis["growth"],
                "vulnerability_progression": journey_analysis["vulnerability"],
                "resilience_development": journey_analysis["resilience"],
                "emotional_health_score": journey_analysis["health_score"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing emotional journey for {user_id}: {e}")
            return self._get_default_journey()
    
    async def predict_relationship_evolution(self, user_id: str) -> Dict:
        """Predict where this relationship is heading"""
        try:
            # Get current scaffold and timeline
            current_scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)
            timeline = await self.generate_intimacy_timeline(user_id)
            
            predictions = self._generate_relationship_predictions(current_scaffold, timeline)
            
            return {
                "user_id": user_id,
                "current_state": {
                    "intimacy_score": current_scaffold.intimacy_score,
                    "relationship_depth": current_scaffold.relationship_depth,
                    "emotional_mode": current_scaffold.emotional_availability_mode
                },
                "predictions": predictions["forecasts"],
                "growth_opportunities": predictions["opportunities"],
                "potential_challenges": predictions["challenges"],
                "recommended_actions": predictions["recommendations"],
                "confidence_score": predictions["confidence"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting relationship evolution for {user_id}: {e}")
            return self._get_default_prediction()
    
    async def get_relationship_summary(self, user_id: str) -> Dict:
        """Get comprehensive relationship summary for dashboard"""
        try:
            timeline = await self.generate_intimacy_timeline(user_id)
            journey = await self.analyze_emotional_journey(user_id)
            prediction = await self.predict_relationship_evolution(user_id)
            scaffold = await self.scaffold_manager.get_intimacy_scaffold(user_id)

            # Defensive: ensure lists for slicing
            key_milestones = timeline.get("relationship_milestones", [])
            if not isinstance(key_milestones, list):
                key_milestones = []
            emotional_themes = journey.get("emotional_themes", {})
            if isinstance(emotional_themes, dict):
                emotional_themes = list(emotional_themes.keys())
            if not isinstance(emotional_themes, list):
                emotional_themes = []
            growth_patterns = journey.get("growth_patterns", [])
            if not isinstance(growth_patterns, list):
                growth_patterns = []
            future_trajectory = prediction.get("predictions", {}).get("trajectory", "unknown")

            return {
                "user_id": user_id,
                "overview": {
                    "relationship_age_days": self._calculate_relationship_age(timeline),
                    "total_conversations": getattr(scaffold, 'conversation_count', 0),
                    "current_intimacy_score": getattr(scaffold, 'intimacy_score', 0.0),
                    "relationship_phase": getattr(scaffold, 'relationship_depth', "initial_curiosity"),
                    "emotional_health": journey.get("emotional_health_score", 0.5)
                },
                "current_state": {
                    "emotional_undercurrent": getattr(scaffold, 'emotional_undercurrent', ""),
                    "support_needs": getattr(scaffold, 'support_needs', []),
                    "unresolved_threads": getattr(scaffold, 'unresolved_threads', []),
                    "inside_references": len(getattr(scaffold, 'inside_references', []))
                },
                "insights": {
                    "key_milestones": key_milestones[:3],
                    "emotional_themes": emotional_themes[:5],
                    "growth_patterns": growth_patterns,
                    "future_trajectory": future_trajectory
                },
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating relationship summary for {user_id}: {e}")
            return {}
    
    def _build_intimacy_timeline(self, evolution_memories: Dict) -> Dict:
        """Build timeline from relationship evolution data"""
        results = evolution_memories.get("results", [])
        
        timeline_points = []
        milestones = []
        progression_data = []
        
        for memory in results:
            metadata = memory.get("metadata", {})
            timestamp = metadata.get("timestamp")
            analysis = metadata.get("subconscious_analysis", {})
            
            if timestamp and analysis:
                # Extract timeline point
                intimacy_score = self._calculate_historical_intimacy_score(analysis)
                relationship_depth = analysis.get("relationship_depth", {})
                
                timeline_point = {
                    "timestamp": timestamp,
                    "intimacy_score": intimacy_score,
                    "trust_level": relationship_depth.get("trust_level", "initial"),
                    "conversation_count": relationship_depth.get("conversation_count", 0),
                    "emotional_undercurrent": analysis.get("emotional_undercurrent", "neutral"),
                    "analysis_summary": analysis.get("analysis_summary", "")
                }
                
                timeline_points.append(timeline_point)
                
                # Check for milestones
                milestone = self._detect_milestone(analysis, timeline_points)
                if milestone:
                    milestones.append(milestone)
        
        # Sort by timestamp
        timeline_points.sort(key=lambda x: x["timestamp"])
        
        # Calculate progression
        if timeline_points:
            progression_data = self._calculate_progression_metrics(timeline_points)
            current_phase = timeline_points[-1]["trust_level"] if timeline_points else "initial_curiosity"
        else:
            current_phase = "initial_curiosity"
            progression_data = {"direction": "building", "velocity": 0.0, "consistency": 0.0}
        
        return {
            "points": timeline_points,
            "milestones": milestones,
            "progression": progression_data,
            "current_phase": current_phase
        }
    
    def _analyze_emotional_progression(self, emotional_memories: Dict) -> Dict:
        """Analyze emotional growth over time"""
        results = emotional_memories.get("results", [])
        
        themes = {}
        vulnerability_progression = []
        growth_indicators = []
        resilience_markers = []
        
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            
            # Extract emotional themes
            if any(word in memory_text for word in ["vulnerable", "scared", "worried"]):
                themes["vulnerability"] = themes.get("vulnerability", 0) + 1
                vulnerability_progression.append({
                    "timestamp": metadata.get("timestamp", ""),
                    "type": "vulnerability",
                    "content": memory_text[:100]
                })
            
            if any(word in memory_text for word in ["growth", "learned", "better", "stronger"]):
                themes["growth"] = themes.get("growth", 0) + 1
                growth_indicators.append({
                    "timestamp": metadata.get("timestamp", ""),
                    "type": "growth",
                    "content": memory_text[:100]
                })
            
            if any(word in memory_text for word in ["resilient", "cope", "overcome", "handle"]):
                themes["resilience"] = themes.get("resilience", 0) + 1
                resilience_markers.append({
                    "timestamp": metadata.get("timestamp", ""),
                    "type": "resilience", 
                    "content": memory_text[:100]
                })
        
        # Calculate emotional health score
        total_emotional_data = len(results)
        growth_ratio = len(growth_indicators) / max(total_emotional_data, 1)
        resilience_ratio = len(resilience_markers) / max(total_emotional_data, 1)
        vulnerability_ratio = len(vulnerability_progression) / max(total_emotional_data, 1)
        
        # Health score: balance of growth, resilience, and healthy vulnerability
        health_score = min((growth_ratio * 0.4 + resilience_ratio * 0.4 + vulnerability_ratio * 0.2), 1.0)
        
        return {
            "themes": themes,
            "growth": growth_indicators[-5:],  # Last 5 growth moments
            "vulnerability": vulnerability_progression[-5:],  # Last 5 vulnerable moments
            "resilience": resilience_markers[-5:],  # Last 5 resilience moments
            "health_score": health_score
        }
    
    def _generate_relationship_predictions(self, scaffold, timeline: Dict) -> Dict:
        """Generate predictions about relationship future"""
        current_score = scaffold.intimacy_score
        current_depth = scaffold.relationship_depth
        progression = timeline.get("progression", {})
        
        # Predict trajectory
        velocity = progression.get("velocity", 0.0)
        consistency = progression.get("consistency", 0.0)
        
        if velocity > 0.1 and consistency > 0.7:
            trajectory = "accelerating_growth"
            confidence = 0.8
        elif velocity > 0.05:
            trajectory = "steady_growth" 
            confidence = 0.7
        elif velocity < -0.05:
            trajectory = "plateau_or_decline"
            confidence = 0.6
        else:
            trajectory = "stable_maintenance"
            confidence = 0.5
        
        # Growth opportunities
        opportunities = []
        if current_score < 0.7:
            opportunities.append("deeper_vulnerability_sharing")
        if current_depth != "deep":
            opportunities.append("trust_building_experiences")
        if len(scaffold.inside_references) < 3:
            opportunities.append("shared_reference_development")
        
        # Potential challenges
        challenges = []
        if "work_stress" in scaffold.support_needs:
            challenges.append("stress_management_support_needed")
        if scaffold.emotional_availability_mode == "processing":
            challenges.append("emotional_processing_time_required")
        
        # Recommendations
        recommendations = []
        if trajectory == "accelerating_growth":
            recommendations.append("maintain_current_approach")
        elif trajectory == "plateau_or_decline":
            recommendations.append("increase_emotional_depth")
            recommendations.append("address_unresolved_concerns")
        
        return {
            "forecasts": {
                "trajectory": trajectory,
                "predicted_intimacy_score_30_days": min(current_score + (velocity * 30), 1.0),
                "estimated_phase_progression": self._predict_phase_progression(current_depth, velocity)
            },
            "opportunities": opportunities,
            "challenges": challenges, 
            "recommendations": recommendations,
            "confidence": confidence
        }
    
    def _calculate_historical_intimacy_score(self, analysis: Dict) -> float:
        """Calculate intimacy score from historical analysis"""
        trust_level = analysis.get("relationship_depth", {}).get("trust_level", "initial")
        conv_count = analysis.get("relationship_depth", {}).get("conversation_count", 0)
        
        trust_scores = {
            "initial_curiosity": 0.1,
            "growing_trust": 0.3,
            "established": 0.6,
            "deep": 0.9
        }
        
        base_score = trust_scores.get(trust_level, 0.1) * 0.6
        conv_factor = min(conv_count / 30.0, 1.0) * 0.4
        
        return min(base_score + conv_factor, 1.0)
    
    def _detect_milestone(self, analysis: Dict, timeline_points: List) -> Optional[Dict]:
        """Detect relationship milestones"""
        trust_level = analysis.get("relationship_depth", {}).get("trust_level")
        
        # Check if this is a new trust level
        if len(timeline_points) > 1:
            previous_trust = timeline_points[-2].get("trust_level")
            if trust_level != previous_trust:
                return {
                    "timestamp": analysis.get("timestamp"),
                    "type": "trust_advancement",
                    "from_level": previous_trust,
                    "to_level": trust_level,
                    "description": f"Relationship evolved from {previous_trust} to {trust_level}"
                }
        
        return None
    
    def _calculate_progression_metrics(self, timeline_points: List) -> Dict:
        """Calculate relationship progression velocity and consistency"""
        if len(timeline_points) < 2:
            return {"direction": "building", "velocity": 0.0, "consistency": 0.0}
        
        # Calculate velocity (change in intimacy score over time)
        scores = [point["intimacy_score"] for point in timeline_points]
        score_changes = [scores[i] - scores[i-1] for i in range(1, len(scores))]
        
        velocity = sum(score_changes) / len(score_changes) if score_changes else 0.0
        
        # Calculate consistency (how steady the growth is)
        if len(score_changes) > 1:
            variance = sum((x - velocity) ** 2 for x in score_changes) / len(score_changes)
            consistency = max(0, 1 - variance)
        else:
            consistency = 1.0
        
        direction = "growing" if velocity > 0.01 else "stable" if velocity > -0.01 else "declining"
        
        return {
            "direction": direction,
            "velocity": velocity,
            "consistency": consistency
        }
    
    def _predict_phase_progression(self, current_depth: str, velocity: float) -> str:
        """Predict next relationship phase"""
        phases = ["initial_curiosity", "growing_trust", "established", "deep"]
        
        try:
            current_index = phases.index(current_depth)
        except ValueError:
            current_index = 0
        
        if velocity > 0.1 and current_index < len(phases) - 1:
            return phases[current_index + 1]
        else:
            return current_depth
    
    def _calculate_relationship_age(self, timeline: Dict) -> int:
        """Calculate relationship age in days"""
        points = timeline.get("points", [])
        if not points:
            return 0
        
        first_interaction = points[0]["timestamp"]
        try:
            start_date = datetime.fromisoformat(first_interaction.replace('Z', '+00:00'))
            age = (datetime.now() - start_date).days
            return max(age, 0)
        except:
            return 0
    
    def _get_default_timeline(self) -> Dict:
        """Default timeline for error cases"""
        return {
            "timeline_points": [],
            "relationship_milestones": [],
            "intimacy_progression": {"direction": "building", "velocity": 0.0},
            "current_phase": "initial_curiosity",
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_default_journey(self) -> Dict:
        """Default journey for error cases"""
        return {
            "emotional_themes": {},
            "growth_patterns": [],
            "vulnerability_progression": [],
            "resilience_development": [],
            "emotional_health_score": 0.5,
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_default_prediction(self) -> Dict:
        """Default prediction for error cases"""
        return {
            "current_state": {"intimacy_score": 0.0, "relationship_depth": "initial_curiosity"},
            "predictions": {"trajectory": "building", "predicted_intimacy_score_30_days": 0.1},
            "growth_opportunities": ["start_conversations"],
            "potential_challenges": [],
            "recommended_actions": ["engage_more_frequently"],
            "confidence_score": 0.3,
            "generated_at": datetime.now().isoformat()
        } 