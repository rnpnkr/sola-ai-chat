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