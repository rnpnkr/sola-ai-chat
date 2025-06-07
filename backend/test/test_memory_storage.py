import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the backend directory is in sys.path for module imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.conversation_memory_manager import ConversationMemoryManager
from memory.mem0_async_service import IntimateMemoryService

async def test_memory_storage():
    print("💾 Testing Memory Storage...")
    
    service = IntimateMemoryService()
    manager = ConversationMemoryManager(service)
    
    # Store a conversation
    result = await manager.store_intimate_conversation(
        user_message="I'm feeling lonely and missing home",
        ai_response="I understand that loneliness. Your feelings about home are valid.",
        user_id="test_user_456",
        emotional_context={"mood": "sad", "location": "away_from_home"}
    )
    
    print(f"Storage result: {result}")
    print("✅ Memory storage test complete!")

if __name__ == "__main__":
    asyncio.run(test_memory_storage()) 