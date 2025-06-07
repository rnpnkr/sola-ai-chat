import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the parent directory is in sys.path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.mem0_async_service import IntimateMemoryService
from memory.memory_context_builder import MemoryContextBuilder

async def test_context_builder():
    print("🧠 Testing Memory Context Builder...")
    
    service = IntimateMemoryService()
    context_builder = MemoryContextBuilder(service)
    
    # Test context building with existing memories
    context = await context_builder.build_intimate_context(
        current_message="I'm feeling better today, but still thinking about home",
        user_id="test_user_123"
    )
    
    print("Generated Context:")
    print(context)
    print("\n✅ Context Builder test complete!")

if __name__ == "__main__":
    asyncio.run(test_context_builder()) 