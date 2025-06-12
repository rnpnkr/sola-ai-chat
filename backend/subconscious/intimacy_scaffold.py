from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import logging
from memory.mem0_async_service import IntimateMemoryService
import asyncio
from services.memory_coordinator import get_memory_coordinator
from services.service_registry import ServiceRegistry  # localized import to avoid cycles

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

    # Graph-derived relationship intelligence
    emotional_relationship_map: Optional[Dict[str, List[str]]] = field(default_factory=dict)
    trust_progression_path: Optional[List[str]] = field(default_factory=list)
    vulnerability_pattern_graph: Optional[List[str]] = field(default_factory=list)
    support_network_context: Optional[List[str]] = field(default_factory=list)
    relationship_depth_graph: Optional[Dict[str, float]] = field(default_factory=dict)

class IntimacyScaffoldManager:
    """Manages real-time access to relationship state with <150ms guarantee"""
    
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service
        self.graph_query_service = ServiceRegistry.get_graph_service()
        self.scaffold_cache = {}  # In-memory cache for <150ms access
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.pending_storage_tasks = {}  # Track async storage tasks
        self.session_changes = {}  # Track changes per session for batch storage
        self.user_locks: Dict[str, asyncio.Lock] = {}
        
    async def _get_user_lock(self, user_id: str) -> asyncio.Lock:
        """Return an asyncio.Lock unique to the user (created lazily)."""
        if user_id not in self.user_locks:
            self.user_locks[user_id] = asyncio.Lock()
        return self.user_locks[user_id]
    
    async def get_intimacy_scaffold(self, user_id: str) -> IntimacyScaffold:
        """Retrieve current relationship scaffold with <150ms guarantee"""
        try:
            lock = await self._get_user_lock(user_id)
            async with lock:
                # Check local cache first (<10ms access)
                if self._is_cached_fresh(user_id):
                    logger.debug(f"Cache hit for user {user_id}")
                    return self.scaffold_cache[user_id]["scaffold"]
            
            # Build from Mem0 data (~100-150ms)
            logger.debug(f"Cache miss for user {user_id}, building from Mem0")
            scaffold = await self._build_scaffold_from_mem0(user_id)
            
            # Cache for future access
            async with await self._get_user_lock(user_id):
                self._cache_scaffold(user_id, scaffold)
            
            return scaffold
            
        except Exception as e:
            logger.error(f"Error getting intimacy scaffold for {user_id}: {e}")
            return self._get_default_scaffold()
    
    async def update_scaffold_cache(self, user_id: str, new_insights: Dict):
        """Update cached scaffold with new background insights"""
        try:
            lock = await self._get_user_lock(user_id)
            async with lock:
                if user_id in self.scaffold_cache:
                    # Update existing scaffold with new insights
                    scaffold = self.scaffold_cache[user_id]["scaffold"]
                    scaffold = self._merge_insights_into_scaffold(scaffold, new_insights)
                    self._cache_scaffold(user_id, scaffold)
                    logger.debug(f"Updated cached scaffold for user {user_id}")
        except Exception as e:
            logger.error(f"Error updating scaffold cache for {user_id}: {e}")
    
    async def _build_scaffold_from_mem0(self, user_id: str) -> IntimacyScaffold:
        """Build intimacy scaffold driven by organic graph relationships."""
        try:
            # ----------------------------------------------------------
            # 🌱 ORGANIC GRAPH SEARCHES (Mem0 vector+graph hybrid)
            # ----------------------------------------------------------
            relationship_context = await self.mem0_service.search_relationship_context(
                user_id=user_id,
                limit=5,
            )

            trust_evolution = await self.mem0_service.search_trust_evolution(
                user_id=user_id,
                limit=3,
            )

            # ----------------------------------------------------------
            # 🧠 Graph traversal helpers (Neo4j direct)
            # ----------------------------------------------------------
            if self.graph_query_service:
                organic_patterns = self.graph_query_service.discover_relationship_patterns(user_id)
                emotional_context = self.graph_query_service.get_organic_emotional_context(user_id)
            else:
                organic_patterns = {}
                emotional_context = []

            return self._build_organic_scaffold(
                relationship_context,
                trust_evolution,
                organic_patterns,
                emotional_context,
                user_id,
            )

        except Exception as e:
            logger.error("Error building organic scaffold for %s: %s", user_id, e, exc_info=True)
            return self._get_default_scaffold()

    # ------------------------------------------------------------------
    # 🌿 Organic scaffold construction helpers (Phase 4)
    # ------------------------------------------------------------------

    def _build_organic_scaffold(
        self,
        relationship_context: Dict,
        trust_evolution: Dict,
        organic_patterns: Dict,
        emotional_context: List[str],
        user_id: str,
    ) -> IntimacyScaffold:
        """Construct IntimacyScaffold from organic graph data."""

        emotional_undercurrent = self._synthesize_emotional_undercurrent(emotional_context)
        relationship_depth = self._assess_organic_relationship_depth(trust_evolution, organic_patterns)
        communication_dna = self._extract_organic_communication_patterns(relationship_context, organic_patterns)
        support_needs = self._identify_organic_support_needs(relationship_context, emotional_context)
        unresolved_threads = self._extract_organic_unresolved_threads(relationship_context)
        conversation_count = len(relationship_context.get("results", [])) + len(trust_evolution.get("results", []))

        scaffold = IntimacyScaffold(
            emotional_undercurrent=emotional_undercurrent,
            unresolved_threads=unresolved_threads,
            communication_dna=communication_dna,
            relationship_depth=relationship_depth,
            emotional_availability_mode=self._determine_organic_emotional_mode(emotional_context),
            support_needs=support_needs,
            inside_references=self._extract_organic_inside_references(relationship_context),
            conversation_count=conversation_count,
            last_updated=datetime.now(),
        )

        # Compute intimacy score (simple heuristic for now)
        scaffold.intimacy_score = self._calculate_organic_intimacy_score(scaffold, organic_patterns)

        scaffold.emotional_relationship_map = {
            "organic_patterns": organic_patterns,
            "emotional_context": emotional_context,
        }

        return scaffold

    def _synthesize_emotional_undercurrent(self, emotional_context: List[str]) -> str:
        if not emotional_context:
            return "exploring_connection"
        counts: Dict[str, int] = {}
        for line in emotional_context:
            lower = line.lower()
            for theme in ["trust", "vulnerability", "joy", "anxiety", "growth", "support", "connection"]:
                if theme in lower:
                    counts[theme] = counts.get(theme, 0) + 1
        if not counts:
            return "building_connection"
        dominant = max(counts, key=counts.get)
        mapping = {
            "trust": "trust_deepening",
            "vulnerability": "vulnerability_present",
            "joy": "predominantly_positive",
            "anxiety": "working_through_challenges",
            "growth": "personal_development",
            "support": "mutual_support_building",
            "connection": "emotional_bonding",
        }
        return mapping.get(dominant, "evolving_relationship")

    def _assess_organic_relationship_depth(self, trust_evolution: Dict, organic_patterns: Dict) -> str:
        trust_events = len(trust_evolution.get("results", [])) if isinstance(trust_evolution, dict) else 0
        pattern_count = len(organic_patterns)
        if trust_events >= 5 or pattern_count > 10:
            return "intimate_companionship"
        if trust_events >= 2 or pattern_count > 3:
            return "growing_trust"
        return "initial_curiosity"

    def _extract_organic_communication_patterns(self, relationship_context: Dict, organic_patterns: Dict) -> Dict[str, str]:
        style = "adaptive"
        if isinstance(relationship_context, dict):
            texts = [m.get("memory", "") for m in relationship_context.get("results", []) if isinstance(m, dict)]
            avg_len = sum(len(t) for t in texts) / max(len(texts), 1) if texts else 0
            if avg_len > 120:
                style = "long_form"
            elif avg_len < 40:
                style = "concise"
        return {"style": style, "pattern_count": str(len(organic_patterns))}

    def _identify_organic_support_needs(self, relationship_context: Dict, emotional_context: List[str]) -> List[str]:
        needs = []
        combined = " ".join(emotional_context).lower()
        if "anxious" in combined or "worried" in combined:
            needs.append("reassurance")
        if "lonely" in combined:
            needs.append("companionship")
        if "happy" in combined and "share" in combined:
            needs.append("celebration")
        return needs[:3]

    def _extract_organic_unresolved_threads(self, relationship_context: Dict) -> List[str]:
        threads = []
        for res in relationship_context.get("results", []):
            text = res.get("memory", "").lower() if isinstance(res, dict) else str(res).lower()
            if any(w in text for w in ["worried", "anxious", "concerned"]):
                threads.append(text[:60])
        return threads[:3]

    def _determine_organic_emotional_mode(self, emotional_context: List[str]) -> str:
        joined = " ".join(emotional_context).lower()
        if any(w in joined for w in ["happy", "joy", "excited"]):
            return "celebrating"
        if any(w in joined for w in ["anxious", "worried", "sad", "lonely"]):
            return "seeking_support"
        return "exploring"

    def _extract_organic_inside_references(self, relationship_context: Dict) -> List[str]:
        refs = []
        for res in relationship_context.get("results", []):
            txt = res.get("memory", "") if isinstance(res, dict) else str(res)
            if "remember" in txt.lower() or "as we discussed" in txt.lower():
                refs.append(txt[:120])
        return refs[:5]

    def _calculate_organic_intimacy_score(self, scaffold: IntimacyScaffold, organic_patterns: Dict) -> float:
        score = 0.3  # baseline
        if scaffold.relationship_depth == "growing_trust":
            score += 0.2
        elif scaffold.relationship_depth == "intimate_companionship":
            score += 0.4
        score += min(len(organic_patterns) / 20, 0.2)
        score += 0.1 if scaffold.emotional_undercurrent == "trust_deepening" else 0
        return round(min(score, 1.0), 2)
    
    def _parse_scaffold_from_memories(self, relationship_insights: Dict, recent_conversations: Dict, user_id: str) -> IntimacyScaffold:
        """Parse Mem0 memories into IntimacyScaffold structure"""
        
        # Extract relationship insights from background analysis
        insights_data = relationship_insights.get("results", [])
        recent_results = recent_conversations.get("results", [])

        # Defensive check for inconsistent Mem0 API behavior
        if isinstance(insights_data, dict):
            insights_results = [insights_data]  # Wrap single dict in a list
        else:
            insights_results = insights_data

        if insights_results and isinstance(insights_results[0], dict):
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
            
            # ---- Graph-derived intelligence ---------------------------------
            try:
                scaffold.emotional_relationship_map = {
                    "recent_emotions": self.graph_query_service.get_recent_emotional_context(user_id)
                }
                scaffold.trust_progression_path = self.graph_query_service.analyze_trust_progression(user_id)
                scaffold.vulnerability_pattern_graph = self.graph_query_service.map_vulnerability_pattern(user_id)
                scaffold.support_network_context = self.graph_query_service.support_network_context(user_id)
                # Placeholder depth graph
                scaffold.relationship_depth_graph = {
                    "depth_score": scaffold.intimacy_score
                }
            except Exception as gerr:
                logger.warning("Graph enrichment failed for scaffold %s: %s", user_id, gerr)
            
            return scaffold
        
        else:
            # New user - build basic scaffold from recent conversations
            return self._build_basic_scaffold(recent_results, user_id)
    
    def _extract_unresolved_threads(self, recent_conversations: List) -> List[str]:
        """Extract ongoing conversation topics that need follow-up"""
        threads = []
        
        for conversation in recent_conversations:
            memory_text = ""
            if isinstance(conversation, dict):
                memory_text = conversation.get("memory", "").lower()
            elif isinstance(conversation, str):
                memory_text = conversation.lower()

            if not memory_text:
                continue

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
    
    def _determine_emotional_mode(self, analysis: Dict, recent_conversations: List) -> str:
        """Determine current emotional availability mode"""
        
        # Check recent emotional state - ADD SAFETY CHECK
        if recent_conversations and len(recent_conversations) > 0:
            recent_memory = ""
            first_conversation = recent_conversations[0]
            
            if isinstance(first_conversation, dict):
                recent_memory = first_conversation.get("memory", "").lower()
            elif isinstance(first_conversation, str):
                recent_memory = first_conversation.lower()
    
            if recent_memory:  # Only process if we have actual content
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
    
    def _build_basic_scaffold(self, recent_conversations: List, user_id: str) -> IntimacyScaffold:
        """Build basic scaffold for new users"""
        conversation_count = len(recent_conversations) if recent_conversations else 0
        
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
            self.user_locks.pop(user_id, None)
        else:
            self.scaffold_cache.clear()
            self.user_locks.clear()
    
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

# Export a singleton instance for global use via ServiceRegistry
intimacy_scaffold_manager = ServiceRegistry.get_scaffold_manager() 