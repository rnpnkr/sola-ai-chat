import asyncio
import pytest
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory.mem0_async_service import IntimateMemoryService
from subconscious.emotional_archaeology import EmotionalArchaeology
from subconscious.relationship_evolution import RelationshipEvolutionTracker
from subconscious.background_processor import PersistentSubconsciousProcessor

@pytest.mark.asyncio
async def test_phase3_implementation():
    print("\U0001F9E0 Testing Phase 3: Subconscious Processing...")
    
    # Initialize services
    mem0_service = IntimateMemoryService()
    emotional_archaeology = EmotionalArchaeology(mem0_service)
    relationship_tracker = RelationshipEvolutionTracker(mem0_service)
    background_processor = PersistentSubconsciousProcessor(mem0_service)
    
    test_user_id = "test_user_subconscious"
    # Test Emotional Archaeology
    print("\U0001F50D Testing Emotional Archaeology...")
    vulnerability_patterns = await emotional_archaeology.mine_vulnerability_moments(test_user_id)
    joy_patterns = await emotional_archaeology.extract_joy_patterns(test_user_id)
    pain_patterns = await emotional_archaeology.map_pain_points(test_user_id)
    growth_arcs = await emotional_archaeology.track_growth_arcs(test_user_id)
    
    print(f"Vulnerability patterns found: {len(vulnerability_patterns)}")
    print(f"Joy patterns found: {len(joy_patterns)}")
    print(f"Pain patterns found: {len(pain_patterns)}")
    print(f"Growth arcs: {growth_arcs}")
    
    # Test Relationship Evolution
    print("\n\U0001F495 Testing Relationship Evolution...")
    trust_milestones = await relationship_tracker.track_trust_milestones(test_user_id)
    communication_patterns = await relationship_tracker.analyze_communication_patterns(test_user_id)
    relationship_phase = await relationship_tracker.detect_relationship_phases(test_user_id)
    inside_references = await relationship_tracker.track_inside_references(test_user_id)
    
    print(f"Trust level: {trust_milestones.get('trust_level', 'unknown')}")
    print(f"Communication style: {communication_patterns.get('comfort_preference', 'unknown')}")
    print(f"Relationship phase: {relationship_phase.get('phase', 'unknown')}")
    print(f"Inside references: {len(inside_references)}")
    
    # Test Background Processor (short run)
    print("\n\U0001F501 Testing Background Processor...")
    
    # Start background processing for 10 seconds
    processing_task = asyncio.create_task(
        background_processor.start_continuous_processing(test_user_id)
    )
    
    # Let it run for one cycle (should complete in ~10 seconds)
    await asyncio.sleep(10)
    
    # Stop processing
    background_processor.stop_processing(test_user_id)
    
    # Cancel the task
    processing_task.cancel()
    try:
        await processing_task
    except asyncio.CancelledError:
        pass
    
    print("\u2705 Phase 3 implementation test complete!")
    print("\n\U0001F3AF Subconscious processing foundation is ready!")

if __name__ == "__main__":
    asyncio.run(test_phase3_implementation()) 