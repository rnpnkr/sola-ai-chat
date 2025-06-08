from openai import OpenAI
import os
import logging
from typing import Dict, List
import json
import re

logger = logging.getLogger(__name__)

class MemoryContextEnhancer:
    """Enhances conversation context for better Mem0 storage using OpenRouter"""
    def __init__(self):
        # Use the cheaper OpenRouter model for context enhancement
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.enhancement_model = os.getenv("OPENROUTER_MODEL_MEM0", "meta-llama/llama-3.1-8b-instruct:free")
        self.total_enhancements = 0
        self.successful_enhancements = 0
    async def enhance_conversation_for_memory(
        self, 
        user_message: str, 
        ai_response: str, 
        emotional_context: Dict = None
    ) -> Dict:
        """Enhance conversation context for Mem0 storage using structured JSON output"""
        # Define JSON schema for structured output
        enhancement_schema = {
            "type": "object",
            "properties": {
                "enhanced_user_message": {
                    "type": "string",
                    "description": "Enhanced user message with context markers like [EMOTIONAL_STATE], [RELATIONSHIP_CONCERN], etc."
                },
                "enhanced_ai_response": {
                    "type": "string", 
                    "description": "Enhanced AI response with support type markers like [EMOTIONAL_SUPPORT], [GUIDANCE], etc."
                },
                "memory_facts": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of 2-3 key facts worth remembering from this conversation"
                },
                "emotional_tone": {
                    "type": "string",
                    "enum": ["distressed", "anxious", "positive", "contemplative", "neutral", "vulnerable"],
                    "description": "Primary emotional tone of the conversation"
                },
                "conversation_significance": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "How significant this conversation is for memory storage"
                }
            },
            "required": ["enhanced_user_message", "enhanced_ai_response", "memory_facts", "emotional_tone", "conversation_significance"],
            "additionalProperties": False
        }
        enhancement_prompt = f"""Analyze this intimate AI companion conversation and enhance it for memory storage.

USER MESSAGE: "{user_message}"
AI RESPONSE: "{ai_response}"

Your task:
1. Add context markers to messages (like [EMOTIONAL_STATE], [RELATIONSHIP_CONCERN], [SUPPORT_PROVIDED])
2. Extract 2-3 key memory facts that an intimate AI companion should remember
3. Assess emotional tone and conversation significance

Focus on emotional context, relationship dynamics, personal situations, and support needs."""
        try:
            response = self.client.chat.completions.create(
                model=self.enhancement_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at analyzing intimate conversations for an AI companion. Extract emotional context, relationship information, and meaningful facts. Always provide valid JSON output."
                    },
                    {"role": "user", "content": enhancement_prompt}
                ],
                max_tokens=300,
                temperature=0.3,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "conversation_enhancement",
                        "strict": True,
                        "schema": enhancement_schema
                    }
                },
                extra_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost:3000"),
                    "X-Title": "Memory Context Enhancer",
                }
            )
            raw_content = response.choices[0].message.content
            logger.info(f"🔍 [DEBUG] Raw LLM response: {raw_content}")
            try:
                enhancement_json = json.loads(raw_content)
            except Exception:
                # Try to extract JSON from code block if present
                match = re.search(r'{[\s\S]*}', raw_content)
                if match:
                    enhancement_json = json.loads(match.group(0))
                else:
                    logger.error(f"❌ [DEBUG] Could not parse JSON from LLM response: {raw_content}")
                    raise
            logger.info(f"🔍 [DEBUG] Original user message: '{user_message}'")
            logger.info(f"🔍 [DEBUG] Original AI response: '{ai_response}'")
            logger.info(f"🔍 [DEBUG] Structured enhancement result: {enhancement_json}")
            return {
                "enhanced_user_message": enhancement_json["enhanced_user_message"],
                "enhanced_ai_response": enhancement_json["enhanced_ai_response"],
                "memory_facts": enhancement_json["memory_facts"],
                "emotional_tone": enhancement_json["emotional_tone"],
                "conversation_significance": enhancement_json["conversation_significance"],
                "enhancement_applied": True
            }
        except Exception as e:
            logger.error(f"❌ [DEBUG] Structured enhancement failed: {e}")
            logger.error(f"❌ [DEBUG] Falling back to basic enhancement for: '{user_message}'")
            return self._basic_enhancement(user_message, ai_response, emotional_context)
    def _basic_enhancement(self, user_message: str, ai_response: str, emotional_context: Dict) -> Dict:
        """Fallback basic enhancement if structured enhancement fails"""
        # Apply basic context markers based on keywords
        enhanced_user = user_message
        enhanced_ai = ai_response
        user_lower = user_message.lower()
        if any(word in user_lower for word in ["anxious", "worried", "scared", "stressed"]):
            emotional_tone = "anxious"
            enhanced_user = f"[EMOTIONAL_DISTRESS] {user_message}"
        elif any(word in user_lower for word in ["girlfriend", "boyfriend", "partner", "relationship"]):
            emotional_tone = "vulnerable"
            enhanced_user = f"[RELATIONSHIP_CONCERN] {user_message}"
        elif any(word in user_lower for word in ["happy", "excited", "great"]):
            emotional_tone = "positive"
            enhanced_user = f"[POSITIVE_EMOTION] {user_message}"
        else:
            emotional_tone = "neutral"
        if any(word in ai_response.lower() for word in ["breathe", "calm", "together"]):
            enhanced_ai = f"[EMOTIONAL_SUPPORT] {ai_response}"
        else:
            enhanced_ai = f"[GENERAL_SUPPORT] {ai_response}"
        return {
            "enhanced_user_message": enhanced_user,
            "enhanced_ai_response": enhanced_ai,
            "memory_facts": [f"User expressed {emotional_tone} emotions", "AI provided supportive response"],
            "emotional_tone": emotional_tone,
            "conversation_significance": "medium",
            "enhancement_applied": False
        } 