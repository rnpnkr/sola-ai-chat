from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import logging
from memory.mem0_async_service import IntimateMemoryService
import asyncio
from services.memory_coordinator import get_memory_coordinator

logger = logging.getLogger(__name__)

@dataclass
class IntimacyScaffold:
    """Real-time relationship state for intimate AI responses"""
    emotional_undercurrent: str = "neutral"              # Current emotional themes
    unresolved_threads: List[str] = field(default_factory=list)  # Ongoing conversation topics
    intimacy_opportunities: Dict[str, float] = field(default_factory=dict)  # Connection moments
    communication_dna: Dict[str, str] = field(default_factory=dict)  # Communication preferences
    relationship_depth: str = "initial_curiosity"        # Trust/intimacy level
    emotional_availability_mode: str = "exploring"       # Current support needs
    support_needs: List[str] = field(default_factory=list)  # What they need right now
    inside_references: List[str] = field(default_factory=list)  # Shared memories
    last_updated: datetime = field(default_factory=datetime.now)
    conversation_count: int = 0
    intimacy_score: float = 0.0

class IntimacyScaffoldManager:
    """Manages real-time access to relationship state with <150ms guarantee"""
    
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service
        self.scaffold_cache = {}  # In-memory cache for <150ms access
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.pending_storage_tasks = {}  # Track async storage tasks
        self.session_changes = {}  # Track changes per session for batch storage
        
    async def get_intimacy_scaffold(self, user_id: str) -> IntimacyScaffold:
        """Retrieve current relationship scaffold with <150ms guarantee"""
        try:
            # Check local cache first (<10ms access)
            if self._is_cached_fresh(user_id):
                logger.debug(f"Cache hit for user {user_id}")
                return self.scaffold_cache[user_id]["scaffold"]
            
            # Build from Mem0 data (~100-150ms)
            logger.debug(f"Cache miss for user {user_id}, building from Mem0")
            scaffold = await self._build_scaffold_from_mem0(user_id)
            
            # Cache for future access
            self._cache_scaffold(user_id, scaffold)
            
            return scaffold
            
        except Exception as e:
            logger.error(f"Error getting intimacy scaffold for {user_id}: {e}")
            return self._get_default_scaffold()
    
    async def update_scaffold_cache(self, user_id: str, new_insights: Dict):
        """Update cached scaffold with new background insights"""
        try:
            if user_id in self.scaffold_cache:
                # Update existing scaffold with new insights
                scaffold = self.scaffold_cache[user_id]["scaffold"]
                scaffold = self._merge_insights_into_scaffold(scaffold, new_insights)
                self._cache_scaffold(user_id, scaffold)
                logger.debug(f"Updated cached scaffold for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating scaffold cache for {user_id}: {e}")
    
    async def _build_scaffold_from_mem0(self, user_id: str) -> IntimacyScaffold:
        """Build intimacy scaffold from Mem0 stored insights"""
        try:
            # Search for latest relationship evolution insights
            relationship_insights = await self.mem0_service.search_intimate_memories(
                query="relationship_evolution subconscious_analysis system_analysis",
                user_id=user_id,
                limit=1
            )
            
            # Get recent conversation context
            recent_conversations = await self.mem0_service.search_intimate_memories(
                query="conversation interaction",
                user_id=user_id,
                limit=5
            )
            
            return self._parse_scaffold_from_memories(relationship_insights, recent_conversations, user_id)
            
        except Exception as e:
            logger.error(f"Error building scaffold from Mem0 for {user_id}: {e}")
            return self._get_default_scaffold()
    
    def _parse_scaffold_from_memories(self, relationship_insights: Dict, recent_conversations: Dict, user_id: str) -> IntimacyScaffold:
        """Parse Mem0 memories into IntimacyScaffold structure"""
        
        # Extract relationship insights from background analysis
        insights_results = relationship_insights.get("results", [])
        recent_results = recent_conversations.get("results", [])
        
        if insights_results:
            # Get the most recent subconscious analysis
            latest_insight = insights_results[0]
            metadata = latest_insight.get("metadata", {})
            subconscious_analysis = metadata.get("subconscious_analysis", {})
            
            # Build scaffold from stored analysis
            scaffold = IntimacyScaffold(
                emotional_undercurrent=subconscious_analysis.get("emotional_undercurrent", "neutral"),
                communication_dna=subconscious_analysis.get("communication_preferences", {}),
                relationship_depth=subconscious_analysis.get("relationship_depth", {}).get("trust_level", "initial_curiosity"),
                support_needs=subconscious_analysis.get("support_needs", []),
                inside_references=subconscious_analysis.get("inside_references", []),
                conversation_count=subconscious_analysis.get("relationship_depth", {}).get("conversation_count", 0),
                last_updated=datetime.now()
            )
            
            # Add unresolved threads from recent conversations
            scaffold.unresolved_threads = self._extract_unresolved_threads(recent_results)
            
            # Calculate current emotional availability mode
            scaffold.emotional_availability_mode = self._determine_emotional_mode(subconscious_analysis, recent_results)
            
            # Calculate intimacy opportunities
            scaffold.intimacy_opportunities = self._calculate_intimacy_opportunities(subconscious_analysis, recent_results)
            
            # Calculate overall intimacy score
            scaffold.intimacy_score = self._calculate_intimacy_score(scaffold)
            
            return scaffold
        
        else:
            # New user - build basic scaffold from recent conversations
            return self._build_basic_scaffold(recent_results, user_id)
    
    def _extract_unresolved_threads(self, recent_conversations: List[Dict]) -> List[str]:
        """Extract ongoing conversation topics that need follow-up"""
        threads = []
        
        for conversation in recent_conversations:
            memory_text = conversation.get("memory", "").lower()
            
            # Look for unresolved concerns
            if any(indicator in memory_text for indicator in ["worried", "anxious", "concerned", "stressed"]):
                # Extract the concern
                if "about" in memory_text:
                    concern = memory_text.split("about", 1)[1].strip()[:50]
                    threads.append(f"concerned about {concern}")
            
            # Look for pending events
            if any(indicator in memory_text for indicator in ["tomorrow", "next week", "upcoming", "planning"]):
                event = memory_text[:60]
                threads.append(f"upcoming: {event}")
        
        return threads[:3]  # Keep most recent 3 threads
    
    def _determine_emotional_mode(self, analysis: Dict, recent_conversations: List[Dict]) -> str:
        """Determine current emotional availability mode"""
        
        # Check recent emotional state
        if recent_conversations:
            recent_memory = recent_conversations[0].get("memory", "").lower()
            
            if any(word in recent_memory for word in ["happy", "excited", "great", "wonderful"]):
                return "celebrating"
            elif any(word in recent_memory for word in ["sad", "worried", "stressed", "difficult"]):
                return "seeking_support"
            elif any(word in recent_memory for word in ["confused", "thinking", "wondering"]):
                return "processing"
        
        # Default based on relationship analysis
        emotional_undercurrent = analysis.get("emotional_undercurrent", "")
        if "vulnerability_present" in emotional_undercurrent:
            return "seeking_support"
        elif "predominantly_positive" in emotional_undercurrent:
            return "open_to_connection"
        else:
            return "exploring"
    
    def _calculate_intimacy_opportunities(self, analysis: Dict, recent_conversations: List[Dict]) -> Dict[str, float]:
        """Calculate opportunities for deeper connection"""
        opportunities = {}
        
        # Support opportunity based on emotional state
        if any("working_through_challenges" in analysis.get("emotional_undercurrent", "") for _ in [1]):
            opportunities["deeper_support"] = 0.8
        
        # Celebration opportunity based on positive emotions
        if any("predominantly_positive" in analysis.get("emotional_undercurrent", "") for _ in [1]):
            opportunities["celebration"] = 0.7
        
        # Growth opportunity based on relationship phase
        relationship_phase = analysis.get("relationship_depth", {}).get("current_phase", "")
        if relationship_phase in ["emotional_availability", "intimate_companionship"]:
            opportunities["personal_growth"] = 0.6
        
        # Connection opportunity based on trust level
        trust_level = analysis.get("relationship_depth", {}).get("trust_level", "")
        if trust_level in ["established", "deep"]:
            opportunities["intimate_sharing"] = 0.9
        
        return opportunities
    
    def _calculate_intimacy_score(self, scaffold: IntimacyScaffold) -> float:
        """Calculate overall intimacy score (0.0 to 1.0)"""
        score = 0.0
        
        # Relationship depth scoring
        depth_scores = {
            "initial_curiosity": 0.1,
            "growing_trust": 0.3,
            "established": 0.6,
            "deep": 0.9
        }
        score += depth_scores.get(scaffold.relationship_depth, 0.1) * 0.4
        
        # Conversation count scoring (up to 0.3 points)
        conversation_factor = min(scaffold.conversation_count / 30.0, 1.0)  # Max at 30 conversations
        score += conversation_factor * 0.3
        
        # Emotional vulnerability scoring (up to 0.2 points)
        if "vulnerability_present" in scaffold.emotional_undercurrent:
            score += 0.2
        
        # Inside references scoring (up to 0.1 points)
        if len(scaffold.inside_references) > 0:
            score += min(len(scaffold.inside_references) / 5.0, 1.0) * 0.1
        
        return min(score, 1.0)
    
    def _build_basic_scaffold(self, recent_conversations: List[Dict], user_id: str) -> IntimacyScaffold:
        """Build basic scaffold for new users"""
        conversation_count = len(recent_conversations)
        
        # Determine basic relationship phase
        if conversation_count < 3:
            relationship_depth = "initial_curiosity"
        elif conversation_count < 10:
            relationship_depth = "growing_trust"
        else:
            relationship_depth = "established"
        
        return IntimacyScaffold(
            emotional_undercurrent="exploring_connection",
            relationship_depth=relationship_depth,
            emotional_availability_mode="open_to_connection",
            conversation_count=conversation_count,
            intimacy_score=conversation_count * 0.05,  # Basic scoring
            last_updated=datetime.now()
        )
    
    def _merge_insights_into_scaffold(self, scaffold: IntimacyScaffold, new_insights: Dict) -> IntimacyScaffold:
        """Merge new background insights into existing scaffold"""
        
        # Update with new insights
        scaffold.emotional_undercurrent = new_insights.get("emotional_undercurrent", scaffold.emotional_undercurrent)
        scaffold.communication_dna.update(new_insights.get("communication_preferences", {}))
        scaffold.support_needs = new_insights.get("support_needs", scaffold.support_needs)
        scaffold.inside_references = new_insights.get("inside_references", scaffold.inside_references)
        
        # Update relationship depth
        relationship_depth = new_insights.get("relationship_depth", {})
        scaffold.relationship_depth = relationship_depth.get("trust_level", scaffold.relationship_depth)
        scaffold.conversation_count = relationship_depth.get("conversation_count", scaffold.conversation_count)
        
        # Recalculate intimacy score
        scaffold.intimacy_score = self._calculate_intimacy_score(scaffold)
        scaffold.last_updated = datetime.now()
        
        return scaffold
    
    def _is_cached_fresh(self, user_id: str) -> bool:
        """Check if cached scaffold is still fresh"""
        if user_id not in self.scaffold_cache:
            return False
        
        cache_entry = self.scaffold_cache[user_id]
        age_seconds = (datetime.now() - cache_entry["timestamp"]).total_seconds()
        
        return age_seconds < self.cache_ttl
    
    def _cache_scaffold(self, user_id: str, scaffold: IntimacyScaffold):
        """Cache scaffold for fast access"""
        self.scaffold_cache[user_id] = {
            "scaffold": scaffold,
            "timestamp": datetime.now()
        }
    
    def _get_default_scaffold(self) -> IntimacyScaffold:
        """Return default scaffold for error cases"""
        return IntimacyScaffold(
            emotional_undercurrent="neutral",
            relationship_depth="initial_curiosity",
            emotional_availability_mode="exploring",
            last_updated=datetime.now()
        )
    
    def clear_cache(self, user_id: Optional[str] = None):
        """Clear scaffold cache for user or all users"""
        if user_id:
            self.scaffold_cache.pop(user_id, None)
        else:
            self.scaffold_cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring"""
        return {
            "cached_users": len(self.scaffold_cache),
            "cache_size_mb": len(str(self.scaffold_cache)) / 1024 / 1024,
            "users": list(self.scaffold_cache.keys())
        }
    
    def get_cache_freshness_info(self, user_id: str) -> Dict:
        """Get cache freshness information for debugging"""
        if user_id not in self.scaffold_cache:
            return {"cached": False, "age_seconds": None}
        
        cache_entry = self.scaffold_cache[user_id]
        age_seconds = (datetime.now() - cache_entry["timestamp"]).total_seconds()
        
        return {
            "cached": True,
            "age_seconds": age_seconds,
            "is_fresh": age_seconds < 120,  # Fresh if less than 2 minutes old
            "intimacy_score": cache_entry["scaffold"].intimacy_score,
            "last_updated": cache_entry["timestamp"].isoformat()
        }
    
    # ADD: Immediate cache update with async storage trigger
    async def update_scaffold_real_time(self, user_id: str, analysis_insights: Dict):
        """Update scaffold cache immediately + trigger async storage"""
        try:
            # 1. Update cache immediately (for fast access)
            if user_id in self.scaffold_cache:
                scaffold = self.scaffold_cache[user_id]["scaffold"]
                updated_scaffold = self._merge_insights_into_scaffold(scaffold, analysis_insights)
                self._cache_scaffold(user_id, updated_scaffold)
            else:
                # Build new scaffold with insights
                scaffold = await self._build_scaffold_from_mem0(user_id)
                updated_scaffold = self._merge_insights_into_scaffold(scaffold, analysis_insights)
                self._cache_scaffold(user_id, updated_scaffold)
            # 2. Track session changes for batch storage
            if user_id not in self.session_changes:
                self.session_changes[user_id] = []
            self.session_changes[user_id].append({
                "timestamp": datetime.now().isoformat(),
                "insights": analysis_insights,
                "scaffold_snapshot": {
                    "intimacy_score": updated_scaffold.intimacy_score,
                    "relationship_depth": updated_scaffold.relationship_depth,
                    "emotional_undercurrent": updated_scaffold.emotional_undercurrent
                }
            })
            # 3. Trigger async storage (fire-and-forget)
            self._trigger_async_storage(user_id, analysis_insights)
            # NEW: Log cache protection info
            freshness_info = self.get_cache_freshness_info(user_id)
            logger.info(f"Real-time scaffold update complete for {user_id} - Cache freshness: {freshness_info}")
        except Exception as e:
            logger.error(f"Error in real-time scaffold update for {user_id}: {e}")
    def _trigger_async_storage(self, user_id: str, insights: Dict):
        """Trigger async storage without blocking"""
        # Cancel any pending storage task for this user
        if user_id in self.pending_storage_tasks:
            self.pending_storage_tasks[user_id].cancel()
        # Start new async storage task
        storage_task = asyncio.create_task(
            self._store_scaffold_insights_async(user_id, insights)
        )
        self.pending_storage_tasks[user_id] = storage_task
    async def _store_scaffold_insights_async(self, user_id: str, insights: Dict):
        """Store scaffold insights using coordinated memory operations"""
        try:
            # Use memory coordinator instead of direct storage
            coordinator = get_memory_coordinator()
            await coordinator.schedule_memory_operation(
                user_id=user_id,
                operation_type="scaffold_update",
                content={
                    "messages": [{
                        "role": "system",
                        "content": f"Real-time scaffold update: {insights.get('analysis_type', 'conversation_analysis')}"
                    }],
                    "metadata": {
                        "type": "scaffold_update",
                        "timestamp": insights.get("timestamp"),
                        "real_time_insights": insights,
                        "intimacy_level": "system_analysis"
                    }
                },
                priority=2  # Medium priority
            )
            logger.debug(f"Scheduled scaffold storage for {user_id}")
        except Exception as e:
            logger.error(f"Coordinated scaffold storage failed for {user_id}: {e}")
        finally:
            # Clean up completed task
            self.pending_storage_tasks.pop(user_id, None)
    async def store_session_complete(self, user_id: str):
        """Store complete session data when user session ends"""
        try:
            if user_id not in self.session_changes or not self.session_changes[user_id]:
                logger.debug(f"No session changes to store for {user_id}")
                return
            # Get current scaffold state
            current_scaffold = await self.get_intimacy_scaffold(user_id)
            # Compile session summary
            session_summary = {
                "session_start": self.session_changes[user_id][0]["timestamp"],
                "session_end": datetime.now().isoformat(),
                "total_updates": len(self.session_changes[user_id]),
                "final_scaffold_state": {
                    "intimacy_score": current_scaffold.intimacy_score,
                    "relationship_depth": current_scaffold.relationship_depth,
                    "emotional_undercurrent": current_scaffold.emotional_undercurrent,
                    "conversation_count": current_scaffold.conversation_count,
                    "support_needs": current_scaffold.support_needs,
                    "inside_references": current_scaffold.inside_references
                },
                "session_progression": [
                    {
                        "timestamp": change["timestamp"],
                        "emotional_state": change["insights"].get("emotional_undercurrent"),
                        "intimacy_level": change["insights"].get("intimacy_progression", {}).get("current_intimacy_level")
                    }
                    for change in self.session_changes[user_id]
                ]
            }
            # Store session completion
            session_message = {
                "role": "system",
                "content": f"Session completed: {session_summary['total_updates']} scaffold updates"
            }
            await self.mem0_service.store_conversation_memory(
                messages=[session_message],
                user_id=user_id,
                metadata={
                    "type": "session_completion",
                    "timestamp": session_summary["session_end"],
                    "session_summary": session_summary,
                    "intimacy_level": "system_analysis"
                }
            )
            logger.info(f"Session completion stored for {user_id}: {session_summary['total_updates']} updates")
            # Clean up session data
            del self.session_changes[user_id]
        except Exception as e:
            logger.error(f"Error storing session completion for {user_id}: {e}")
    async def trigger_backup_storage(self, user_id: str):
        """Trigger backup storage of current scaffold state"""
        try:
            if user_id not in self.scaffold_cache:
                logger.debug(f"No cached scaffold to backup for {user_id}")
                return
            current_scaffold = self.scaffold_cache[user_id]["scaffold"]
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "backup_type": "scheduled_backup",
                "scaffold_state": {
                    "intimacy_score": current_scaffold.intimacy_score,
                    "relationship_depth": current_scaffold.relationship_depth,
                    "emotional_undercurrent": current_scaffold.emotional_undercurrent,
                    "conversation_count": current_scaffold.conversation_count,
                    "unresolved_threads": current_scaffold.unresolved_threads,
                    "support_needs": current_scaffold.support_needs
                }
            }
            backup_message = {
                "role": "system",
                "content": f"Scaffold backup: relationship_depth={current_scaffold.relationship_depth}, intimacy={current_scaffold.intimacy_score:.2f}"
            }
            await self.mem0_service.store_conversation_memory(
                messages=[backup_message],
                user_id=user_id,
                metadata={
                    "type": "scaffold_backup",
                    "timestamp": backup_data["timestamp"],
                    "backup_data": backup_data,
                    "intimacy_level": "system_analysis"
                }
            )
            logger.debug(f"Scaffold backup completed for {user_id}")
        except Exception as e:
            logger.error(f"Scaffold backup failed for {user_id}: {e}")

# Export a singleton instance for global use
intimacy_scaffold_manager = IntimacyScaffoldManager(IntimateMemoryService()) 