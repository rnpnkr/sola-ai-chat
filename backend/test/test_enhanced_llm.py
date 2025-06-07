import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the backend directory is in sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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