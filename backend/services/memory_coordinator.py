import asyncio
from typing import Dict, List, Optional, Set
import logging
from datetime import datetime
from collections import defaultdict
from memory.mem0_async_service import IntimateMemoryService
from services.memory_context_enhancer import MemoryContextEnhancer
from services.chat_service import chat_service
import time
import hashlib

logger = logging.getLogger(__name__)

class MemoryCoordinator:
    """Coordinates memory operations to prevent duplicates and optimize batching"""
    def __init__(self, mem0_service: IntimateMemoryService):
        self.mem0_service = mem0_service
        self.memory_enhancer = MemoryContextEnhancer()
        self.pending_operations = defaultdict(list)  # user_id -> list of operations
        self.processing_locks = {}  # user_id -> asyncio.Lock
        self.batch_timers = {}  # user_id -> asyncio.Task
        self.operation_deduplication = {}  # content_hash -> operation_id
        # Configuration
        self.batch_window_ms = 2000  # 2 seconds batching window (slightly increased)
        self.max_batch_size = 5  # aligned with new batching guidance
        self.max_concurrent_users = 10
        # Track recent conversation hashes to avoid duplicate UPDATE storm
        self.recent_hashes: Dict[str, float] = {}
    async def schedule_memory_operation(
        self, 
        user_id: str, 
        operation_type: str,
        content: Dict,
        priority: int = 1
    ) -> str:
        """Schedule a memory operation with deduplication and batching"""
        # Create content hash for deduplication
        content_hash = self._create_content_hash(content)
        # Check for duplicate operations
        if content_hash in self.operation_deduplication:
            existing_op_id = self.operation_deduplication[content_hash]
            logger.debug(f"Deduplicated memory operation: {content_hash}")
            return existing_op_id
        # Create operation
        operation_id = f"{user_id}_{operation_type}_{datetime.now().timestamp()}"
        operation = {
            "id": operation_id,
            "user_id": user_id,
            "type": operation_type,
            "content": content,
            "priority": priority,
            "timestamp": datetime.now(),
            "content_hash": content_hash
        }
        # Store for deduplication
        self.operation_deduplication[content_hash] = operation_id
        # Get or create user lock
        if user_id not in self.processing_locks:
            self.processing_locks[user_id] = asyncio.Lock()
        # Add to pending operations
        async with self.processing_locks[user_id]:
            self.pending_operations[user_id].append(operation)
            # Start batch timer if not already running
            if user_id not in self.batch_timers:
                self.batch_timers[user_id] = asyncio.create_task(
                    self._batch_processor(user_id)
                )
        logger.debug(f"Scheduled memory operation: {operation_id}")
        return operation_id
    async def _batch_processor(self, user_id: str):
        """Process batched operations for a user with enhanced error handling"""
        try:
            # Wait for batch window
            await asyncio.sleep(self.batch_window_ms / 1000.0)
            async with self.processing_locks[user_id]:
                if not self.pending_operations[user_id]:
                    return
                # Get operations to process
                operations = self.pending_operations[user_id][:self.max_batch_size]
                self.pending_operations[user_id] = self.pending_operations[user_id][self.max_batch_size:]
                if not operations:
                    return
                logger.info(f"Processing {len(operations)} batched memory operations for {user_id}")
                # Group operations by type for efficient processing
                grouped_ops = defaultdict(list)
                for op in operations:
                    grouped_ops[op["type"]].append(op)
                # Process each group with individual error handling
                failed_operations = []
                for op_type, ops in grouped_ops.items():
                    try:
                        await self._process_operation_group(op_type, ops)
                        logger.debug(f"Successfully processed {len(ops)} {op_type} operations")
                    except Exception as e:
                        logger.error(f"Failed to process {op_type} operations: {e}")
                        failed_operations.extend(ops)
                # Retry failed operations with exponential backoff
                if failed_operations:
                    await self._handle_failed_operations(user_id, failed_operations)
                # Clean up deduplication cache for successfully processed operations
                successful_ops = [op for op in operations if op not in failed_operations]
                for op in successful_ops:
                    self.operation_deduplication.pop(op["content_hash"], None)
                # Schedule next batch if there are more operations
                if self.pending_operations[user_id]:
                    self.batch_timers[user_id] = asyncio.create_task(
                        self._batch_processor(user_id)
                    )
                else:
                    self.batch_timers.pop(user_id, None)
        except Exception as e:
            logger.error(f"Critical batch processor error for {user_id}: {e}")
        finally:
            # Cleanup timer reference
            self.batch_timers.pop(user_id, None)
    async def _process_operation_group(self, operation_type: str, operations: List[Dict]):
        """Process a group of similar operations efficiently"""
        if operation_type == "conversation_memory":
            await self._batch_conversation_memories(operations)
        elif operation_type == "scaffold_update":
            await self._batch_scaffold_updates(operations)
        elif operation_type == "relationship_evolution":
            await self._batch_relationship_evolution(operations)
        elif operation_type == "graph_relationship":
            await self._batch_graph_relationships(operations)
        else:
            # Fallback: process individually
            for op in operations:
                await self._process_individual_operation(op)
    async def _batch_conversation_memories(self, operations: List[Dict]):
        """Enhanced batch process conversation memory operations"""
        for op in operations:
            try:
                content = op["content"]
                messages = content["messages"]
                # Extract user and AI messages
                user_message = ""
                ai_response = ""
                for msg in messages:
                    if msg["role"] == "user":
                        user_message = msg["content"]
                    elif msg["role"] == "assistant":
                        ai_response = msg["content"]
                # ENHANCE: Apply context enhancement before storage
                if user_message and ai_response:
                    enhancement = await self.memory_enhancer.enhance_conversation_for_memory(
                        user_message=user_message,
                        ai_response=ai_response,
                        emotional_context=content["metadata"].get("emotional_context", {})
                    )
                    # Replace messages with enhanced versions
                    enhanced_messages = [
                        {"role": "user", "content": enhancement["enhanced_user_message"]},
                        {"role": "assistant", "content": enhancement["enhanced_ai_response"]}
                    ]
                    # Add memory facts as system message for Mem0
                    if enhancement.get("memory_facts"):
                        enhanced_messages.append({
                            "role": "system",
                            "content": f"MEMORY_FACTS: {'; '.join(enhancement['memory_facts'])} | EMOTIONAL_TONE: {enhancement.get('emotional_tone', 'neutral')} | SIGNIFICANCE: {enhancement.get('conversation_significance', 'medium')}"
                        })
                    logger.info(f"🔍 [DEBUG] Sending to Mem0 - Enhanced messages: {enhanced_messages}")
                    logger.info(f"🔍 [DEBUG] Sending to Mem0 - Metadata: {content['metadata']}")
                    # Store enhanced version
                    result = await self.mem0_service.store_conversation_memory(
                        messages=enhanced_messages,
                        user_id=op["user_id"],
                        metadata={
                            **content["metadata"],
                            "context_enhanced": enhancement["enhancement_applied"],
                            "original_user_message": user_message,
                            "enhancement_facts": enhancement.get("memory_facts", [])
                        }
                    )
                    logger.info(f"🔍 [DEBUG] Mem0 storage result: {result}")
                else:
                    # Fallback to original storage
                    logger.info(f"🔍 [DEBUG] Sending to Mem0 - Original messages: {content['messages']}")
                    logger.info(f"🔍 [DEBUG] Sending to Mem0 - Metadata: {content['metadata']}")
                    result = await self.mem0_service.store_conversation_memory(
                        messages=content["messages"],
                        user_id=op["user_id"],
                        metadata=content["metadata"]
                    )
                    logger.info(f"🔍 [DEBUG] Mem0 storage result: {result}")
                # After successful storage, add verification
                asyncio.create_task(self._verify_memory_storage(op["user_id"], op["id"]))
                logger.debug(f"Processed enhanced conversation memory: {op['id']}")
            except Exception as e:
                logger.error(f"Failed to process enhanced conversation memory {op['id']}: {e}")
    async def _verify_memory_storage(self, user_id: str, operation_id: str):
        """Verify that memory was actually stored successfully"""
        try:
            # Wait a moment for storage to complete
            await asyncio.sleep(1.0)
            
            # Search for recently stored memory
            search_results = await self.mem0_service.search_intimate_memories(
                query="recent conversation",
                user_id=user_id,
                limit=1
            )
            
            if search_results.get("results"):
                logger.info(f"✅ Memory storage verified for operation {operation_id}")
                return True
            else:
                logger.error(f"❌ Memory storage verification FAILED for operation {operation_id}")
                # TODO: Add to retry queue or dead letter queue
                return False
                
        except Exception as e:
            logger.error(f"❌ Memory storage verification error: {e}")
            return False
    async def _batch_scaffold_updates(self, operations: List[Dict]):
        """Batch process scaffold update operations"""
        # Group by user for more efficient updates
        user_updates = defaultdict(list)
        for op in operations:
            user_updates[op["user_id"]].append(op)
        for user_id, user_ops in user_updates.items():
            try:
                # Merge multiple scaffold updates for same user
                merged_content = self._merge_scaffold_updates([op["content"] for op in user_ops])
                # Single storage operation for all updates
                scaffold_message = {
                    "role": "system",
                    "content": f"Batched scaffold updates: {len(user_ops)} operations"
                }
                await self.mem0_service.store_conversation_memory(
                    messages=[scaffold_message],
                    user_id=user_id,
                    metadata={
                        "type": "batched_scaffold_update",
                        "timestamp": datetime.now().isoformat(),
                        "batch_insights": merged_content,
                        "intimacy_level": "system_analysis"
                    }
                )
                logger.info(f"Processed {len(user_ops)} batched scaffold updates for {user_id}")
            except Exception as e:
                logger.error(f"Failed to process scaffold updates for {user_id}: {e}")
    async def _batch_relationship_evolution(self, operations: List[Dict]):
        """Batch process relationship evolution operations"""
        # Similar to scaffold updates but for relationship data
        for op in operations:
            try:
                content = op["content"]
                await self.mem0_service.store_conversation_memory(
                    messages=content["messages"],
                    user_id=op["user_id"],
                    metadata=content["metadata"]
                )
                logger.debug(f"Processed relationship evolution: {op['id']}")
            except Exception as e:
                logger.error(f"Failed to process relationship evolution {op['id']}: {e}")
    async def _process_individual_operation(self, operation: Dict):
        """Fallback for individual operation processing"""
        try:
            content = operation["content"]
            if "messages" in content and "metadata" in content:
                await self.mem0_service.store_conversation_memory(
                    messages=content["messages"],
                    user_id=operation["user_id"],
                    metadata=content["metadata"]
                )
            logger.debug(f"Processed individual operation: {operation['id']}")
        except Exception as e:
            logger.error(f"Failed to process individual operation {operation['id']}: {e}")
    def _merge_scaffold_updates(self, updates: List[Dict]) -> Dict:
        """Merge multiple scaffold updates into a single comprehensive update"""
        merged = {
            "emotional_states": [],
            "communication_preferences": {},
            "support_needs": set(),
            "intimacy_progressions": [],
            "update_count": len(updates)
        }
        for update in updates:
            if "emotional_undercurrent" in update:
                merged["emotional_states"].append(update["emotional_undercurrent"])
            if "communication_preferences" in update:
                merged["communication_preferences"].update(update["communication_preferences"])
            if "support_needs" in update:
                if isinstance(update["support_needs"], list):
                    merged["support_needs"].update(update["support_needs"])
            if "intimacy_progression" in update:
                merged["intimacy_progressions"].append(update["intimacy_progression"])
        # Convert sets back to lists for JSON serialization
        merged["support_needs"] = list(merged["support_needs"])
        return merged
    def _create_content_hash(self, content: Dict) -> str:
        """Create a hash for content deduplication"""
        import hashlib
        import json
        # Create a normalized string representation
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()[:16]
    async def flush_pending_operations(self, user_id: Optional[str] = None):
        """Force flush pending operations (useful for shutdown)"""
        if user_id:
            if user_id in self.batch_timers:
                self.batch_timers[user_id].cancel()
                await self._batch_processor(user_id)
        else:
            # Flush all users
            for uid in list(self.batch_timers.keys()):
                await self.flush_pending_operations(uid)
    def get_stats(self) -> Dict:
        """Get coordinator statistics"""
        return {
            "pending_operations": {uid: len(ops) for uid, ops in self.pending_operations.items()},
            "active_timers": len(self.batch_timers),
            "deduplication_cache_size": len(self.operation_deduplication),
            "active_users": len(self.processing_locks)
        }
    async def _handle_failed_operations(self, user_id: str, failed_ops: List[Dict]):
        """Handle failed operations with exponential backoff"""
        try:
            # Wait before retry
            await asyncio.sleep(2.0)
            # Retry individual operations
            for op in failed_ops:
                try:
                    await self._process_individual_operation(op)
                    logger.info(f"Successfully retried operation {op['id']}")
                except Exception as e:
                    logger.error(f"Final retry failed for operation {op['id']}: {e}")
                    # Could add to dead letter queue here
        except Exception as e:
            logger.error(f"Error in retry handler for {user_id}: {e}")
    async def store_chat_and_memory(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store both chat and memory in parallel"""
        # ------------------------------------------------------------------
        # Duplicate conversation guard (10-minute window)
        # ------------------------------------------------------------------
        content_hash = self._generate_content_hash(user_message, ai_response, user_id)
        if content_hash in self.recent_hashes:
            if time.time() - self.recent_hashes[content_hash] < 600:
                logger.info(f"Skipping duplicate conversation within 10 minutes for {user_id}")
                return "duplicate_skipped"

        # Record hash timestamp
        self.recent_hashes[content_hash] = time.time()

        # Store chat immediately (high priority)
        chat_task = asyncio.create_task(
            chat_service.store_chat(
                user_id=user_id,
                session_id=session_id,
                user_message=user_message,
                ai_response=ai_response,
                metadata=metadata
            )
        )
        
        # Schedule memory operation (background)
        memory_operation_id = await self.schedule_memory_operation(
            user_id=user_id,
            operation_type="conversation_memory",
            content={
                "messages": [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": ai_response}
                ],
                "metadata": {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                }
            }
        )
        
        # Wait for chat storage to complete
        await chat_task
        
        return memory_operation_id

    # ------------------------------------------------------------------
    # Deduplication helpers
    # ------------------------------------------------------------------
    def _generate_content_hash(self, user_message: str, ai_response: str, user_id: str) -> str:
        """Generate a robust hash that is stable for a 1-hour window.

        This prevents the same user_message/ai_response pair from being stored
        repeatedly within a short period while still allowing legitimate
        repetitions in the future (after the window expires)."""
        normalized_user = user_message.strip().lower()
        normalized_ai = ai_response.strip().lower()
        time_window = int(time.time() // 3600)  # 1-hour buckets
        hash_input = f"{user_id}|{normalized_user}|{normalized_ai}|{time_window}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def _batch_graph_relationships(self, operations: List[Dict]):
        """Batch create graph relationships using GraphRelationshipBuilder."""
        try:
            from backend.subconscious.graph_builder import GraphRelationshipBuilder
            builder = GraphRelationshipBuilder()
            for op in operations:
                content = op["content"]
                rel_type = content.get("relationship_type")
                user_id = op["user_id"]
                if rel_type == "feels":
                    builder.add_feels(user_id, content.get("emotion"), content.get("intensity"))
                elif rel_type == "triggered_by":
                    builder.add_triggered_by(user_id, content.get("emotion"), content.get("event"))
                elif rel_type == "disclosure":
                    builder.add_disclosure_relationship(user_id, content.get("event"), content.get("intimacy_level"))
                elif rel_type == "connection":
                    builder.add_emotional_connection(user_id, content.get("emotion1"), content.get("emotion2"), content.get("connection_type", "leads_to"))
            builder.close()
        except Exception as e:
            logger.error(f"Graph relationship batching failed: {e}")
            # Re-raise to put operations back for retry
            raise

# Global instance
memory_coordinator = None

def get_memory_coordinator() -> MemoryCoordinator:
    """Get global memory coordinator instance"""
    global memory_coordinator
    if memory_coordinator is None:
        mem0_service = IntimateMemoryService()
        memory_coordinator = MemoryCoordinator(mem0_service)
    return memory_coordinator 