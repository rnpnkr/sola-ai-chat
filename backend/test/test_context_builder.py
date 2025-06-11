import pytest

pytest.skip("Skipping legacy context builder test – to be updated.", allow_module_level=True)

# Below imports retained for reference
import asyncio  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

# Load env if needed
load_dotenv()  # noqa: E402

import sys
import os

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