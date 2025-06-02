"""
Configuration file for Voice Assistant
Loads all settings from .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Deepgram Configuration
DEEPGRAM_CONFIG = {
    "api_key": os.getenv("DEEPGRAM_API_KEY", ""),
    "language": os.getenv("DEEPGRAM_LANGUAGE", "en"),
    "punctuate": os.getenv("DEEPGRAM_PUNCTUATE", "true").lower() == "true"
}

# Azure OpenAI Configuration
AZURE_OPENAI_CONFIG = {
    "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
    "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini"),
    "max_tokens": int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "150")),
    "temperature": float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7")),
    "system_message": os.getenv("AZURE_OPENAI_SYSTEM_MESSAGE",
                                "You are a helpful assistant. Keep responses concise and conversational.")
}

# ElevenLabs Configuration
ELEVENLABS_CONFIG = {
    "api_key": os.getenv("ELEVENLABS_API_KEY", ""),
    "voice_id": os.getenv("ELEVENLABS_VOICE_ID", ""),
    "stability": float(os.getenv("ELEVENLABS_STABILITY", "0.75")),
    "similarity_boost": float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", "0.75"))
}

# Optional: Regular OpenAI Configuration (for switching)
OPENAI_CONFIG = {
    "api_key": os.getenv("OPENAI_API_KEY", ""),
    "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "150")),
    "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
    "system_message": os.getenv("OPENAI_SYSTEM_MESSAGE",
                                "You are a helpful assistant. Keep responses concise and conversational.")
}


# Validation function
def validate_config():
    """Validate that required environment variables are set"""
    required_vars = [
        "DEEPGRAM_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_VOICE_ID"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease add them to your .env file")
        return False

    print("✅ All required environment variables are set")
    return True