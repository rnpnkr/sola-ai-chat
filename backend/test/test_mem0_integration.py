import asyncio
from dotenv import load_dotenv
import os

load_dotenv() 

from memory.mem0_async_service import IntimateMemoryService

async def test_mem0_integration():
    print("\U0001F9E0 Testing Mem0 Integration...")
    
    try:
        service = IntimateMemoryService()
        print("✅ Mem0 service initialized")
        
        # Test storage
        test_messages = [
            {"role": "user", "content": "I feel really lonely today and miss my family"},
            {"role": "assistant", "content": "I understand that loneliness can feel overwhelming. Tell me more about what you're experiencing."}
        ]
        
        print("📝 Testing memory storage...")
        store_result = await service.store_conversation_memory(
            messages=test_messages,
            user_id="test_user_123",
            metadata={
                "timestamp": "2025-01-01T12:00:00Z",
                "emotional_context": {"loneliness": "high", "family_missing": True},
                "intimacy_level": "medium"
            }
        )
        print(f"Storage result: {store_result}")
        
        # Wait a moment for indexing
        await asyncio.sleep(2)
        
        # Test search
        print("🔍 Testing memory search...")
        search_result = await service.search_intimate_memories(
            query="feeling lonely and missing family",
            user_id="test_user_123",
            limit=3
        )
        print(f"Search results: {search_result}")
        
        if search_result.get("results"):
            print("✅ Mem0 integration test PASSED!")
            return True
        else:
            print("⚠️ Storage worked but search returned no results (may need indexing time)")
            return False
            
    except Exception as e:
        print(f"❌ Mem0 integration test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mem0_integration())
    if success:
        print("\n🎉 Ready for Phase 2: Memory Context Builder")
    else:
        print("\n🔧 Fix Mem0 configuration before proceeding") 