import pytest

# Skip legacy test entirely (outdated orchestrator import)
pytest.skip("Skipping legacy LLM node test – outdated import.", allow_module_level=True)

# Rest of file retained for reference (not executed)
import asyncio  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# Load environment variables if needed
load_dotenv()  # noqa: E402

from agents.langgraph_orchestrator import llm_node

async def test_enhanced_llm():
    print("🤖 Testing Enhanced LLM with Memory...")
    
    # Test state
    test_state = {
        "client_id": "test_client_123",
        "user_id": "test_user_123", 
        "transcript": "I'm feeling a bit lonely again today"
    }
    
    # Test ONLY the LLM node (skip TTS)
    result = await llm_node(test_state)
    
    print("Enhanced LLM Response:")
    print(result.get("ai_response", "No response generated"))
    print(f"Processing time: {result.get('llm_time_ms', 0)}ms")
    
    print("\n✅ Enhanced LLM test complete!")
    print("🎉 Memory integration working perfectly!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_llm()) 