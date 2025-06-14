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
    "punctuate": os.getenv("DEEPGRAM_PUNCTUATE", "true").lower() == "true",
    "enabled": os.getenv("DEEPGRAM_STREAMING_ENABLED", "true").lower() == "true",
    "endpointing_ms": int(os.getenv("DEEPGRAM_ENDPOINTING_MS", "500")),
    "utterance_end_ms": int(os.getenv("DEEPGRAM_UTTERANCE_END_MS", "1000")),
    "interim_results": os.getenv("DEEPGRAM_INTERIM_RESULTS", "true").lower() == "true",
    "sample_rate": int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
    "channels": int(os.getenv("AUDIO_CHANNELS", "1"))
}


# ElevenLabs Configuration
ELEVENLABS_CONFIG = {
    "api_key": os.getenv("ELEVENLABS_API_KEY", ""),
    "voice_id": os.getenv("ELEVENLABS_VOICE_ID", ""),
    "stability": float(os.getenv("ELEVENLABS_STABILITY", "0.75")),
    "similarity_boost": float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", "0.75"))
}


# OpenRouter Configuration
OPENROUTER_CONFIG = {
    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
    "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"),
    "max_tokens": int(os.getenv("OPENROUTER_MAX_TOKENS", "150")),
    "temperature": float(os.getenv("OPENROUTER_TEMPERATURE", "0.7")),
    "system_message": os.getenv("OPENROUTER_SYSTEM_MESSAGE",
                                "You are a helpful assistant. Keep responses concise and conversational."),
    "site_url": os.getenv("OPENROUTER_SITE_URL", "http://localhost:3000"),
    "site_name": os.getenv("OPENROUTER_SITE_NAME", "Voice Assistant")
}

# Add Groq configuration section if not present
GROQ_CONFIG = {
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),  # Fast model
    "max_tokens": int(os.getenv("GROQ_MAX_TOKENS", "1000")),
    "temperature": float(os.getenv("GROQ_TEMPERATURE", "0.7")),
    "system_message": "You are a helpful AI companion. Keep responses concise and conversational."
}

# Memory Enhancement Configuration
MEMORY_ENHANCEMENT_CONFIG = {
    "model": os.getenv("OPENROUTER_MODEL_MEMORY_ENHANCER", "meta-llama/llama-3.1-8b-instruct:free"),
    "max_tokens": 200,
    "temperature": 0.3,
    "enabled": os.getenv("MEMORY_ENHANCEMENT_ENABLED", "true").lower() == "true"
}

SUPABASE_CONFIG = {
    "url": os.getenv("SUPABASE_URL", ""),
    "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    "project_id": os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
}

# Neo4j Configuration (graph store)
NEO4J_CONFIG = {
    "uri": os.getenv("NEO4J_URI", ""),
    "username": os.getenv("NEO4J_USERNAME", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", ""),
    "database": os.getenv("NEO4J_DATABASE", "neo4j"),
}
