import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import asyncio
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
@patch("memory.mem0_async_service.IntimateMemoryService")
@patch("subconscious.graph_query_service.GraphQueryService")
async def test_organic_intimacy_scaffold(mock_graph_cls, mock_mem0_cls):
    """Verify that IntimacyScaffoldManager builds scaffold with organic graph data."""

    # --------------------------------------------------
    # Mock Mem0 service search helpers
    # --------------------------------------------------
    mock_mem0 = mock_mem0_cls.return_value

    # Relationship context – include unresolved thread indicators
    mock_mem0.search_relationship_context = AsyncMock(return_value={
        "results": [
            {"memory": "I am worried about my presentation tomorrow."},
            {"memory": "Remember our last trip to the lake? It was fun."},
        ]
    })

    # Trust evolution – 3 trust events
    mock_mem0.search_trust_evolution = AsyncMock(return_value={
        "results": [
            {"memory": "I really trust you with this secret."},
            {"memory": "I feel safe talking to you."},
            {"memory": "I rely on your advice."},
        ]
    })

    # --------------------------------------------------
    # Mock GraphQueryService helpers
    # --------------------------------------------------
    mock_graph = mock_graph_cls.return_value
    mock_graph.discover_relationship_patterns.return_value = {
        "SUPPORTS": [{"from": ["User"], "to": ["Emotion"], "frequency": 4}],
        "SHARED_MEMORY": [{"from": ["Event"], "to": ["Event"], "frequency": 3}],
    }
    mock_graph.get_organic_emotional_context.return_value = [
        "anxious about upcoming event", "joy after success", "connection built on trust"
    ]

    # --------------------------------------------------
    # Build scaffold
    # --------------------------------------------------
    from subconscious.intimacy_scaffold import IntimacyScaffoldManager

    scaffold_manager = IntimacyScaffoldManager(mock_mem0)  # graph service auto-fetched
    scaffold_manager.graph_query_service = mock_graph  # override with mock instance

    scaffold = await scaffold_manager.get_intimacy_scaffold("scaffold_test_user")

    # Assertions – ensure new organic fields populated
    assert scaffold.relationship_depth in {"growing_trust", "intimate_companionship"}
    assert "reassurance" in scaffold.support_needs
    assert scaffold.unresolved_threads, "Unresolved threads should be detected"
    assert scaffold.inside_references, "Inside references should be detected"
    assert 0.3 <= scaffold.intimacy_score <= 1.0 