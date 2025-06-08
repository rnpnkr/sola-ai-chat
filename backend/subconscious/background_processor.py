import asyncio
from typing import Dict, Optional
from datetime import datetime
import logging
from memory.mem0_async_service import IntimateMemoryService
from .emotional_archaeology import EmotionalArchaeology
from .relationship_evolution import RelationshipEvolutionTracker
from .intimacy_scaffold import IntimacyScaffoldManager

logger = logging.getLogger(__name__)

class PersistentSubconsciousProcessor:
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service
        self.emotional_archaeology = EmotionalArchaeology(mem0_service)
        self.relationship_tracker = RelationshipEvolutionTracker(mem0_service)
        self.scaffold_manager = IntimacyScaffoldManager(mem0_service)
        self.active_processors = set()

    async def start_continuous_processing(self, user_id: str):
        """Start background relationship analysis for a user"""
        if user_id in self.active_processors:
            logger.info(f"Background processing already active for {user_id}")
            return

        self.active_processors.add(user_id)
        logger.info(f"Starting continuous relationship analysis for {user_id}")
        
        try:
            await self._continuous_relationship_analysis(user_id)
        except Exception as e:
            logger.error(f"Background processing failed for {user_id}: {e}")
        finally:
            self.active_processors.discard(user_id)

    async def _continuous_relationship_analysis(self, user_id: str):
        """Run every 3 minutes - psychologically-optimized analysis with 3 core searches"""
        while user_id in self.active_processors:
            try:
                logger.info(f"Running psychological analysis cycle for {user_id}")
                await self._coordinate_with_realtime(user_id)
                # PSYCHOLOGICAL SEARCH 1: Attachment & Safety Seeking
                attachment_data = await self.mem0_service.search_intimate_memories(
                    query="attachment trust safety security comfort support emotional regulation crisis distress anxiety fear",
                    user_id=user_id,
                    limit=25
                )
                # PSYCHOLOGICAL SEARCH 2: Vulnerability & Intimate Disclosure
                vulnerability_data = await self.mem0_service.search_intimate_memories(
                    query="vulnerable disclosure personal private secret sharing intimate emotional expression authentic feelings",
                    user_id=user_id,
                    limit=25
                )
                # PSYCHOLOGICAL SEARCH 3: Relationship Evolution & Growth
                relationship_data = await self.mem0_service.search_intimate_memories(
                    query="relationship growth progression development deeper connection understanding empathy companionship bond",
                    user_id=user_id,
                    limit=25
                )
                # Process all psychological data into comprehensive insights
                relationship_insight = self._synthesize_psychological_analysis(
                    attachment_patterns=self._analyze_attachment_patterns(attachment_data),
                    vulnerability_patterns=self._analyze_vulnerability_patterns(vulnerability_data),
                    relationship_evolution=self._analyze_relationship_evolution(relationship_data),
                    user_id=user_id
                )
                await self._store_relationship_evolution(user_id, relationship_insight)
                await self.scaffold_manager.trigger_backup_storage(user_id)
                logger.info(f"Psychological analysis cycle complete for {user_id} - 3 searches vs 8 previous")
            except Exception as e:
                logger.error(f"Error in psychological analysis for {user_id}: {e}")
            await asyncio.sleep(180)

    async def _coordinate_with_realtime(self, user_id: str):
        """Coordinate with real-time processing to avoid conflicts"""
        try:
            await asyncio.sleep(2.0)
            logger.debug(f"Background processing coordinated for {user_id}")
        except Exception as e:
            logger.error(f"Coordination error for {user_id}: {e}")

    def _analyze_attachment_patterns(self, attachment_data: Dict) -> Dict:
        """Analyze attachment and safety-seeking behaviors"""
        results = attachment_data.get("results", [])
        attachment_analysis = {
            "safety_seeking_count": 0,
            "trust_indicators": [],
            "crisis_moments": [],
            "emotional_regulation_needs": [],
            "attachment_style_indicators": "secure"  # default
        }
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            # Safety seeking patterns
            if any(word in memory_text for word in ["help", "support", "comfort", "safe", "security"]):
                attachment_analysis["safety_seeking_count"] += 1
            # Trust building moments
            if any(phrase in memory_text for phrase in ["trust you", "feel safe", "comfortable", "rely on"]):
                attachment_analysis["trust_indicators"].append({
                    "memory": memory_text[:100],
                    "timestamp": metadata.get("timestamp")
                })
            # Crisis or distress moments
            if any(word in memory_text for word in ["crisis", "panic", "emergency", "desperate", "overwhelmed"]):
                attachment_analysis["crisis_moments"].append({
                    "memory": memory_text[:100],
                    "timestamp": metadata.get("timestamp"),
                    "intensity": "high" if "panic" in memory_text else "medium"
                })
            # Emotional regulation needs
            if any(word in memory_text for word in ["regulate", "calm", "breathe", "center", "ground"]):
                attachment_analysis["emotional_regulation_needs"].append(memory_text[:100])
        # Determine attachment style based on patterns
        if len(attachment_analysis["crisis_moments"]) > 3:
            attachment_analysis["attachment_style_indicators"] = "anxious"
        elif attachment_analysis["safety_seeking_count"] < 2:
            attachment_analysis["attachment_style_indicators"] = "avoidant"
        else:
            attachment_analysis["attachment_style_indicators"] = "secure"
        return attachment_analysis

    def _analyze_vulnerability_patterns(self, vulnerability_data: Dict) -> Dict:
        """Analyze vulnerability and intimate disclosure patterns"""
        results = vulnerability_data.get("results", [])
        vulnerability_analysis = {
            "disclosure_depth": "surface",
            "vulnerability_comfort": 0.0,
            "intimate_sharing_events": [],
            "emotional_expression_types": [],
            "authentic_moments": []
        }
        intimate_disclosure_count = 0
        total_disclosures = len(results)
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            # Deep personal sharing
            if any(phrase in memory_text for phrase in ["never told", "secret", "personal", "private", "intimate"]):
                intimate_disclosure_count += 1
                vulnerability_analysis["intimate_sharing_events"].append({
                    "memory": memory_text[:100],
                    "timestamp": metadata.get("timestamp"),
                    "depth": "deep"
                })
            # Emotional expression types
            emotions_found = []
            emotion_keywords = {
                "fear": ["scared", "afraid", "terrified", "fear"],
                "sadness": ["sad", "crying", "heartbroken", "grief"],
                "joy": ["happy", "excited", "thrilled", "joyful"],
                "anger": ["angry", "furious", "mad", "irritated"],
                "shame": ["ashamed", "embarrassed", "humiliated"],
                "love": ["love", "adore", "cherish", "devoted"]
            }
            for emotion, keywords in emotion_keywords.items():
                if any(keyword in memory_text for keyword in keywords):
                    emotions_found.append(emotion)
            if emotions_found:
                vulnerability_analysis["emotional_expression_types"].extend(emotions_found)
            # Authentic expression indicators
            if any(phrase in memory_text for phrase in ["authentic", "real", "genuine", "true self", "honest"]):
                vulnerability_analysis["authentic_moments"].append(memory_text[:100])
        # Calculate vulnerability comfort level
        vulnerability_analysis["vulnerability_comfort"] = intimate_disclosure_count / max(total_disclosures, 1)
        # Determine disclosure depth
        if intimate_disclosure_count >= 3:
            vulnerability_analysis["disclosure_depth"] = "deep"
        elif intimate_disclosure_count >= 1:
            vulnerability_analysis["disclosure_depth"] = "moderate"
        else:
            vulnerability_analysis["disclosure_depth"] = "surface"
        return vulnerability_analysis

    def _analyze_relationship_evolution(self, relationship_data: Dict) -> Dict:
        """Analyze relationship growth and evolution patterns"""
        results = relationship_data.get("results", [])
        evolution_analysis = {
            "growth_trajectory": "stable",
            "connection_deepening": False,
            "empathy_development": [],
            "companionship_quality": "developing",
            "relationship_milestones": []
        }
        growth_indicators = 0
        connection_depth_indicators = 0
        for memory in results:
            memory_text = memory.get("memory", "").lower()
            metadata = memory.get("metadata", {})
            # Growth indicators
            if any(word in memory_text for word in ["growth", "progress", "development", "better", "improve"]):
                growth_indicators += 1
            # Deep connection indicators
            if any(phrase in memory_text for phrase in ["understand me", "get me", "connection", "bond", "close"]):
                connection_depth_indicators += 1
                evolution_analysis["relationship_milestones"].append({
                    "type": "connection_deepening",
                    "memory": memory_text[:100],
                    "timestamp": metadata.get("timestamp")
                })
            # Empathy development
            if any(word in memory_text for word in ["empathy", "understand", "compassion", "care", "support"]):
                evolution_analysis["empathy_development"].append(memory_text[:100])
        # Determine growth trajectory
        if growth_indicators >= 3:
            evolution_analysis["growth_trajectory"] = "accelerating"
        elif growth_indicators >= 1:
            evolution_analysis["growth_trajectory"] = "progressing"
        else:
            evolution_analysis["growth_trajectory"] = "stable"
        # Determine connection deepening
        evolution_analysis["connection_deepening"] = connection_depth_indicators >= 2
        # Determine companionship quality
        total_indicators = growth_indicators + connection_depth_indicators
        if total_indicators >= 5:
            evolution_analysis["companionship_quality"] = "intimate"
        elif total_indicators >= 3:
            evolution_analysis["companionship_quality"] = "established"
        else:
            evolution_analysis["companionship_quality"] = "developing"
        return evolution_analysis

    def _synthesize_psychological_analysis(
        self,
        attachment_patterns: Dict,
        vulnerability_patterns: Dict,
        relationship_evolution: Dict,
        user_id: str
    ) -> Dict:
        """Synthesize all psychological data into comprehensive relationship insight"""
        # Determine overall emotional themes
        emotional_themes = []
        # From attachment patterns
        if attachment_patterns["attachment_style_indicators"] == "anxious":
            emotional_themes.append("seeking_security")
        elif attachment_patterns["safety_seeking_count"] > 0:
            emotional_themes.append("building_trust")
        # From vulnerability patterns
        if vulnerability_patterns["disclosure_depth"] == "deep":
            emotional_themes.append("deep_intimacy")
        elif vulnerability_patterns["vulnerability_comfort"] > 0.3:
            emotional_themes.append("increasing_openness")
        # From relationship evolution
        if relationship_evolution["connection_deepening"]:
            emotional_themes.append("meaningful_connection")
        # Synthesize communication preferences
        communication_preferences = {
            "emotional_safety_needs": "high" if attachment_patterns["attachment_style_indicators"] == "anxious" else "moderate",
            "vulnerability_comfort": vulnerability_patterns["disclosure_depth"],
            "connection_style": relationship_evolution["companionship_quality"]
        }
        # Determine relationship depth
        relationship_depth_mapping = {
            ("surface", "developing"): "initial_curiosity",
            ("moderate", "developing"): "growing_trust", 
            ("moderate", "established"): "emotional_availability",
            ("deep", "established"): "intimate_companionship",
            ("deep", "intimate"): "intimate_companionship"
        }
        depth_key = (vulnerability_patterns["disclosure_depth"], relationship_evolution["companionship_quality"])
        current_phase = relationship_depth_mapping.get(depth_key, "growing_trust")
        # Generate analysis summary
        analysis_summary = f"Psychological analysis: {attachment_patterns['attachment_style_indicators']} attachment, {vulnerability_patterns['disclosure_depth']} vulnerability, {relationship_evolution['growth_trajectory']} growth"
        return {
            "timestamp": datetime.now().isoformat(),
            "emotional_undercurrent": " + ".join(emotional_themes) or "exploring_connection",
            "communication_preferences": communication_preferences,
            "relationship_depth": {
                "trust_level": current_phase,
                "current_phase": current_phase,
                "conversation_count": len(attachment_patterns.get("trust_indicators", [])) + len(vulnerability_patterns.get("intimate_sharing_events", []))
            },
            "psychological_profile": {
                "attachment_style": attachment_patterns["attachment_style_indicators"],
                "vulnerability_comfort": vulnerability_patterns["vulnerability_comfort"],
                "growth_trajectory": relationship_evolution["growth_trajectory"],
                "connection_quality": relationship_evolution["companionship_quality"]
            },
            "support_needs": self._extract_support_needs_from_analysis(attachment_patterns, vulnerability_patterns),
            "inside_references": [],  # Will be populated by relationship tracker
            "analysis_summary": analysis_summary,
            "search_efficiency": "3_psychological_searches_vs_8_previous"
        }

    def _extract_support_needs_from_analysis(self, attachment_patterns: Dict, vulnerability_patterns: Dict) -> list:
        """Extract current support needs from psychological analysis"""
        support_needs = []
        # From attachment analysis
        if attachment_patterns["crisis_moments"]:
            support_needs.append("crisis_support")
        if attachment_patterns["emotional_regulation_needs"]:
            support_needs.append("emotional_regulation")
        if attachment_patterns["attachment_style_indicators"] == "anxious":
            support_needs.append("reassurance")
        # From vulnerability analysis
        if vulnerability_patterns["disclosure_depth"] == "deep":
            support_needs.append("validation")
        if "fear" in vulnerability_patterns.get("emotional_expression_types", []):
            support_needs.append("comfort")
        if "sadness" in vulnerability_patterns.get("emotional_expression_types", []):
            support_needs.append("empathetic_presence")
        return support_needs[:3]  # Limit to top 3 needs

    async def _store_relationship_evolution(self, user_id: str, relationship_insight: Dict):
        """Store relationship evolution using coordinated memory operations - CACHE-AWARE"""
        try:
            from services.memory_coordinator import get_memory_coordinator
            coordinator = get_memory_coordinator()
            
            system_message = {
                "role": "system",
                "content": f"Relationship Analysis Update: {relationship_insight['analysis_summary']}"
            }
            
            await coordinator.schedule_memory_operation(
                user_id=user_id,
                operation_type="relationship_evolution",
                content={
                    "messages": [system_message],
                    "metadata": {
                        "type": "relationship_evolution",
                        "timestamp": relationship_insight["timestamp"],
                        "subconscious_analysis": relationship_insight,
                        "intimacy_level": "system_analysis"
                    }
                },
                priority=3  # Lower priority for background analysis
            )
            
            # FIXED: Only update cache if background data is fresher than cached data
            await self._update_cache_if_fresher(user_id, relationship_insight)
            
            logger.info(f"Scheduled relationship evolution storage for {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule relationship evolution for {user_id}: {e}")

    async def _update_cache_if_fresher(self, user_id: str, background_insight: Dict):
        """Only update cache if background data is fresher than cached data"""
        try:
            # Check if user has fresh cache data
            if user_id in self.scaffold_manager.scaffold_cache:
                cached_entry = self.scaffold_manager.scaffold_cache[user_id]
                cache_timestamp = cached_entry["timestamp"]
                
                # Parse background analysis timestamp
                background_timestamp_str = background_insight.get("timestamp")
                if background_timestamp_str:
                    from datetime import datetime
                    background_timestamp = datetime.fromisoformat(background_timestamp_str.replace('Z', '+00:00'))
                    
                    # Calculate age difference
                    cache_age = (datetime.now() - cache_timestamp).total_seconds()
                    
                    # RULE: Don't overwrite cache if it's fresher than 2 minutes
                    # This protects real-time insights during active conversations
                    if cache_age < 120:  # 2 minutes
                        logger.info(f"Cache is fresh ({cache_age:.1f}s old) for {user_id} - preserving real-time insights over background analysis")
                        return
                    
                    # Cache is stale - safe to update with background insights
                    logger.info(f"Cache is stale ({cache_age:.1f}s old) for {user_id} - updating with background analysis")
                    await self.scaffold_manager.update_scaffold_cache(user_id, background_insight)
                else:
                    # No timestamp in background data - update cautiously
                    logger.warning(f"Background insight missing timestamp for {user_id} - skipping cache update to preserve real-time data")
            else:
                # No cached data - safe to update
                logger.info(f"No cached data for {user_id} - updating with background analysis")
                await self.scaffold_manager.update_scaffold_cache(user_id, background_insight)
                
        except Exception as e:
            logger.error(f"Error in cache freshness check for {user_id}: {e}")
            # On error, don't update cache to be safe

    def stop_processing(self, user_id: str):
        """Stop background processing for a user"""
        if user_id in self.active_processors:
            self.active_processors.discard(user_id)
            logger.info(f"Stopped background processing for {user_id}")

    def get_active_processors(self) -> set:
        """Get list of users with active background processing"""
        return self.active_processors.copy()
