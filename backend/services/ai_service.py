# """
# AI Response Services
# """
# from openai import AzureOpenAI, OpenAI
# from config import AZURE_OPENAI_CONFIG
#
#
# class AzureOpenAIService:
#     def __init__(self, config=None):
#         self.config = config or AZURE_OPENAI_CONFIG
#         self.client = AzureOpenAI(
#             api_key=self.config["api_key"],
#             api_version=self.config["api_version"],
#             azure_endpoint=self.config["endpoint"]
#         )
#
#     def get_response(self, text):
#         """
#         Get AI response from Azure OpenAI
#
#         Args:
#             text (str): Input text
#
#         Returns:
#             str: AI response or None if failed
#         """
#         print("🤖 Getting response from Azure OpenAI...")
#
#         try:
#             response = self.client.chat.completions.create(
#                 model=self.config["model"],
#                 messages=[
#                     {"role": "system", "content": self.config["system_message"]},
#                     {"role": "user", "content": text}
#                 ],
#                 max_tokens=self.config.get("max_tokens", 150),
#                 temperature=self.config.get("temperature", 0.7)
#             )
#
#             ai_response = response.choices[0].message.content
#             print(f"💬 AI Response: {ai_response}")
#             return ai_response
#
#         except Exception as e:
#             print(f"❌ Azure OpenAI error: {e}")
#             return None
#
#
# class OpenAIService:
#     """Alternative OpenAI service (non-Azure)"""
#
#     def __init__(self, config=None):
#         self.config = config
#         self.client = OpenAI(api_key=config.get("api_key") if config else None)
#
#     def get_response(self, text):
#         """Get response from OpenAI"""
#         print("🤖 Getting response from OpenAI...")
#
#         try:
#             response = self.client.chat.completions.create(
#                 model=self.config.get("model", "gpt-3.5-turbo"),
#                 messages=[
#                     {"role": "system", "content": self.config.get("system_message", "You are a helpful assistant.")},
#                     {"role": "user", "content": text}
#                 ],
#                 max_tokens=self.config.get("max_tokens", 150),
#                 temperature=self.config.get("temperature", 0.7)
#             )
#
#             ai_response = response.choices[0].message.content
#             print(f"💬 AI Response: {ai_response}")
#             return ai_response
#
#         except Exception as e:
#             print(f"❌ OpenAI error: {e}")
#             return None
#
#
# class AnthropicService:
#     """Example Claude AI service"""
#
#     def __init__(self, config=None):
#         self.config = config
#         # Initialize Anthropic client here
#
#     def get_response(self, text):
#         # Implement Claude AI response
#         pass
#
#
# class LocalLLMService:
#     """Example local LLM service (Ollama, etc.)"""
#
#     def __init__(self, config=None):
#         self.config = config
#         # Initialize local LLM here
#
#     def get_response(self, text):
#         # Implement local LLM response
#         pass

#

from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class OpenRouterService:
    """OpenRouter service - Access 100+ AI models through one API"""

    def __init__(self, config=None):
        from config import OPENROUTER_CONFIG
        self.config = config or OPENROUTER_CONFIG

        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.config["api_key"]
        )

    def get_response(self, text):
        """Get response from OpenRouter (any supported model)"""
        model_name = self.config.get("model", "openai/gpt-3.5-turbo")
        print(f"🤖 Getting response from OpenRouter using {model_name}...")

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self.config.get("system_message", "You are a helpful assistant.")},
                    {"role": "user", "content": text}
                ],
                max_tokens=self.config.get("max_tokens", 150),
                temperature=self.config.get("temperature", 0.7),
                # Optional: Add extra headers for OpenRouter
                extra_headers={
                    "HTTP-Referer": self.config.get("site_url", "http://localhost:3000"),
                    "X-Title": self.config.get("site_name", "Voice Assistant"),
                }
            )

            ai_response = response.choices[0].message.content
            print(f"💬 AI Response: {ai_response}")
            return ai_response

        except Exception as e:
            print(f"❌ OpenRouter error: {e}")
            return None

    async def get_streaming_response(self, text):
        """Get streaming response from OpenRouter"""
        model_name = self.config["model"]  # Always use model from config (OPENROUTER_MODEL from .env)
        print(f"🤖 Streaming from OpenRouter using {model_name}...")
        try:
            stream = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self.config.get("system_message", "You are a helpful assistant.")},
                    {"role": "user", "content": text}
                ],
                max_tokens=self.config.get("max_tokens", 150),
                temperature=self.config.get("temperature", 0.7),
                stream=True,  # ENABLE STREAMING
                extra_headers={
                    "HTTP-Referer": self.config.get("site_url", "http://localhost:3000"),
                    "X-Title": self.config.get("site_name", "Voice Assistant"),
                }
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    logger.info(f"[OpenRouter Streaming] Token: {chunk.choices[0].delta.content}")
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"❌ OpenRouter streaming error: {e}")
            yield f"Error: {str(e)}"


class AnthropicService:
    """Example Claude AI service"""

    def __init__(self, config=None):
        self.config = config
        # Initialize Anthropic client here

    def get_response(self, text):
        # Implement Claude AI response
        pass


class LocalLLMService:
    """Example local LLM service (Ollama, etc.)"""

    def __init__(self, config=None):
        self.config = config
        # Initialize local LLM here

    def get_response(self, text):
        # Implement local LLM response
        pass

# --- GROQ FAST INFERENCE SERVICE ---
try:
    from groq import Groq, AsyncGroq
except ImportError:
    Groq = None
    AsyncGroq = None

class GroqService:
    """
    GroqService: Fast LLM inference using Groq's LPU-accelerated API.
    Supports both sync and async (streaming) completions.
    """
    def __init__(self, config=None):
        from config import GROQ_CONFIG  # Import the config
        self.config = config or GROQ_CONFIG  # Use GROQ_CONFIG instead of environment directly
        
        if Groq is None:
            raise ImportError("groq Python package is not installed. Run 'pip install groq'.")
        self.client = Groq(api_key=self.config["api_key"])

    def get_response(self, text):
        """Get a fast LLM response from Groq (sync)."""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.config.get("system_message", "You are a helpful assistant.")},
                    {"role": "user", "content": text}
                ],
                model=self.config["model"]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GroqService error: {e}")
            return None

    async def get_streaming_response(self, text):
        """Get a streaming response from Groq (async)."""
        if AsyncGroq is None:
            raise ImportError("groq Python package is not installed. Run 'pip install groq'.")
        
        client = AsyncGroq(api_key=self.config["api_key"])
        try:
            # Enable REAL streaming with stream=True
            stream = await client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.config.get("system_message", "You are a helpful assistant.")},
                    {"role": "user", "content": text}
                ],
                model=self.config["model"],
                stream=True,  # THIS IS THE CRITICAL FIX
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 1000)
            )
            
            # Stream actual tokens as they arrive
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    logger.debug(f"[Groq Streaming] Token: {content}")
                    yield content
                    
        except Exception as e:
            logger.error(f"GroqService streaming error: {e}")
            yield f"Error: {str(e)}"