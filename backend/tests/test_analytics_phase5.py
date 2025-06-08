import sys
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Ensure backend is in sys.path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.subconscious.relationship_insights import RelationshipInsightsEngine
from backend.subconscious.memory_analytics import AdvancedMemoryAnalytics

@pytest.fixture
def mock_mem0_service():
    service = MagicMock()
    service.search_intimate_memories = AsyncMock(return_value={
        "results": [
            {
                "memory": "We had a deep conversation about vulnerability and growth.",
                "metadata": {
                    "timestamp": "2024-06-01T12:00:00Z",
                    "intimacy_level": "high",
                    "subconscious_analysis": {
                        "relationship_depth": {"trust_level": "growing_trust", "conversation_count": 10},
                        "emotional_undercurrent": "vulnerability_present",
                        "analysis_summary": "Trust is building rapidly."
                    }
                }
            },
            {
                "memory": "Talked about work stress and coping strategies.",
                "metadata": {
                    "timestamp": "2024-06-02T12:00:00Z",
                    "intimacy_level": "medium",
                    "subconscious_analysis": {
                        "relationship_depth": {"trust_level": "established", "conversation_count": 20},
                        "emotional_undercurrent": "supportive",
                        "analysis_summary": "Relationship is stable."
                    }
                }
            }
        ]
    })
    return service

@pytest.fixture
def mock_scaffold_manager():
    manager = MagicMock()
    scaffold = MagicMock()
    scaffold.intimacy_score = 0.7
    scaffold.relationship_depth = "established"
    scaffold.emotional_availability_mode = "available"
    scaffold.conversation_count = 25
    scaffold.emotional_undercurrent = "vulnerability_present"
    scaffold.support_needs = ["work_stress"]
    scaffold.unresolved_threads = ["career", "family"]
    scaffold.inside_references = ["joke1", "joke2", "joke3"]
    manager.get_intimacy_scaffold = AsyncMock(return_value=scaffold)
    return manager

@pytest.mark.asyncio
async def test_relationship_insights_engine(mock_mem0_service, mock_scaffold_manager):
    engine = RelationshipInsightsEngine(mock_mem0_service, mock_scaffold_manager)
    user_id = "test_user"
    timeline = await engine.generate_intimacy_timeline(user_id)
    assert "timeline_points" in timeline
    journey = await engine.analyze_emotional_journey(user_id)
    assert "emotional_themes" in journey
    prediction = await engine.predict_relationship_evolution(user_id)
    assert "predictions" in prediction
    summary = await engine.get_relationship_summary(user_id)
    assert "overview" in summary

@pytest.mark.asyncio
async def test_advanced_memory_analytics(mock_mem0_service, mock_scaffold_manager):
    analytics = AdvancedMemoryAnalytics(mock_mem0_service, mock_scaffold_manager)
    user_id = "test_user"
    depth = await analytics.conversation_depth_scoring(user_id)
    assert "overall_depth_score" in depth
    patterns = await analytics.emotional_pattern_analysis(user_id)
    assert "emotional_cycles" in patterns
    health = await analytics.relationship_health_metrics(user_id)
    assert "overall_health_score" in health
    quality = await analytics.memory_quality_assessment(user_id)
    assert "memory_richness" in quality 