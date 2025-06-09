from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import asyncio
from services.elevenlabs_streaming import ElevenLabsStreamingService
import os
from langgraph.config import get_stream_writer
import time
from services.deepgram_service import DeepgramService
from services.ai_service import OpenRouterService, GroqService
import logging
from services.deepgram_streaming_service import DeepgramStreamingService
import uuid
import wave, contextlib, io, struct
from memory.mem0_async_service import IntimateMemoryService
from memory.memory_context_builder import MemoryContextBuilder
from memory.conversation_memory_manager import ConversationMemoryManager
from subconscious.intimacy_scaffold import IntimacyScaffoldManager
from subconscious.anticipatory_engine import AnticippatoryIntimacyEngine
from services.background_service_manager import background_service_manager
from datetime import datetime

logger = logging.getLogger(__name__)

# Define the conversation state schema
class ConversationState(TypedDict):
    audio_input: bytes
    transcript: str
    ai_response: str
    audio_output: bytes
    personality_type: str
    client_id: str
    user_id: str

# --- Service instantiation ---
elevenlabs_streaming_service = ElevenLabsStreamingService()

# Initialize memory services
mem0_service = IntimateMemoryService()
memory_context_builder = MemoryContextBuilder(mem0_service)

# NEW: Initialize intimacy services
intimacy_scaffold_manager = IntimacyScaffoldManager(mem0_service)
anticipatory_engine = AnticippatoryIntimacyEngine(mem0_service, intimacy_scaffold_manager)

# --- Node implementations ---

async def stt_node(state: ConversationState, config=None):
    """
    Handles Speech-to-Text. Prioritizes streaming transcript but can
    fall back to file-based STT if enabled.
    """
    fallback_file_stt = False # Set to True to enable file-based fallback
    manager = config.get("configurable", {}).get("manager") if config else None
    client_id = state["client_id"]

    # If transcript already exists (provided by streaming STT), use it
    transcript = state.get("transcript", "")
    if transcript:
        logger.info(f"[{client_id}] Using streaming transcript: '{transcript}'. Skipping file-based STT.")
        # DO NOT send 'transcription_complete' here, it's handled by the streaming flow
        return {"transcript": transcript, "stt_time_ms": 0}

    # If no streaming transcript and fallback is disabled, return empty
    if not fallback_file_stt:
        logger.warning(f"[{client_id}] No streaming transcript and file-based STT fallback is disabled. Returning empty transcript.")
        return {"transcript": "", "stt_time_ms": 0}
    
    # --- Fallback to File-Based STT (if enabled) ---
    logger.info(f"[{client_id}] No streaming transcript found. Running file-based STT as fallback.")
    
    audio_input = state["audio_input"]
    # Use original file-based service
    file_stt_service = DeepgramService()
    try:
        if manager:
            await manager.send_status(client_id, "stt_processing")
        # Create temp file for audio processing
        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        session_id = str(uuid.uuid4())
        input_path = os.path.join(temp_dir, f"input_{session_id}.wav")
        # Save audio data as a proper WAV file (16-bit PCM, 16 kHz, mono)
        try:
            with wave.open(input_path, 'wb') as wf:
                wf.setnchannels(1)          # mono
                wf.setsampwidth(2)          # 16-bit samples
                wf.setframerate(16000)      # 16 kHz sample rate
                wf.writeframes(audio_input)
        except Exception as wav_err:
            logger.error(f"[{client_id}] Failed to write WAV header: {wav_err}. Falling back to raw bytes.")
            # Fallback: write raw bytes (may fail but at least not crash)
            with open(input_path, 'wb') as f:
                f.write(audio_input)
        start_time = time.time()
        # Use file-based transcription
        transcript = await asyncio.to_thread(
            file_stt_service.transcribe, input_path
        )
        elapsed = time.time() - start_time
        stt_time_ms = int(elapsed * 1000)
        if manager:
            await manager.send_status(client_id, "transcription_complete", {"transcript": transcript})
        logger.info(f"[{client_id}] File-based STT complete: {stt_time_ms} ms. Transcript: {transcript}")
        # Cleanup temp file
        try:
            os.remove(input_path)
        except:
            pass
        return {"transcript": transcript or "", "stt_time_ms": stt_time_ms}
    except Exception as e:
        if manager:
            await manager.send_error(client_id, f"STT failed: {str(e)}")
        logger.error(f"[{client_id}] STT Error: {str(e)}")
        return {"transcript": "", "stt_time_ms": 0}

async def llm_node(state: ConversationState, config=None):
    """
    OpenRouter LLM with personality, memory, and intimacy scaffold.
    Enhanced with subconscious understanding for intimate responses.
    """
    try:
        from agents.personality_agent import PersonalityAgent, neo_config
        manager = config.get("configurable", {}).get("manager") if config else None
        client_id = state["client_id"]
        user_id = state.get("user_id", client_id)
        if manager:
            await manager.send_status(client_id, "llm_streaming")
        #ai_service = OpenRouterService()
        ai_service = GroqService() 
        personality_agent = PersonalityAgent(neo_config)
        # Existing: Get memory-informed context
        intimate_context = await memory_context_builder.build_intimate_context(
            current_message=state["transcript"],
            user_id=user_id
        )
        # NEW: Get intimacy scaffold for subconscious understanding
        intimacy_scaffold = await intimacy_scaffold_manager.get_intimacy_scaffold(user_id)
        # NEW: Get anticipatory response guidance
        response_guidance = await anticipatory_engine.generate_response_guidance(
            user_id=user_id,
            current_message=state["transcript"]
        )
        # NEW: Enhanced prompt with subconscious understanding
        subconscious_prompt = f"""{personality_agent.system_prompt}

{intimate_context}

SUBCONSCIOUS UNDERSTANDING:
Emotional Undercurrent: {intimacy_scaffold.emotional_undercurrent}
Communication Style: {intimacy_scaffold.communication_dna.get('style', 'adaptive')}
Relationship Depth: {intimacy_scaffold.relationship_depth}
Current Emotional Mode: {intimacy_scaffold.emotional_availability_mode}
Intimacy Score: {intimacy_scaffold.intimacy_score:.2f}
Support Needs: {', '.join(intimacy_scaffold.support_needs) if intimacy_scaffold.support_needs else 'general presence'}

UNRESOLVED THREADS:
{chr(10).join(f'• {thread}' for thread in intimacy_scaffold.unresolved_threads) if intimacy_scaffold.unresolved_threads else '• No pending concerns'}

RESPONSE GUIDANCE:
Tone: {response_guidance.get('tone', 'warm_conversational')}
Depth: {response_guidance.get('depth_level', 'friendly_supportive')}
Approach: {response_guidance.get('emotional_approach', 'adaptive_mirroring')}

Current conversation: {state['transcript']}

Respond with the intuitive understanding of someone who truly knows this person's emotional landscape, current needs, and relationship dynamic."""
        response = ""
        start_time = time.time()
        token_count = 0
        if hasattr(ai_service, 'get_streaming_response'):
            response_chunks = []
            async for chunk in ai_service.get_streaming_response(subconscious_prompt):
                response_chunks.append(chunk)
                token_count += 1
                if manager:
                    await manager.send_message(client_id, {
                        "type": "token_stream",
                        "content": chunk
                    })
            response = "".join(response_chunks)
        else:
            response = await asyncio.to_thread(
                ai_service.get_response,
                subconscious_prompt
            )
            token_count = len(response.split())
        elapsed = time.time() - start_time
        elapsed_ms = int(elapsed * 1000)
        logger.info(f"[{client_id}] LLM inference: {elapsed_ms} ms. Tokens: {token_count}. Intimacy: {intimacy_scaffold.intimacy_score:.2f}")
        response = personality_agent.format_response(response)
        return {"ai_response": response, "llm_time_ms": elapsed_ms}
    except Exception as e:
        logger.error(f"[{client_id}] Enhanced LLM: Error - {str(e)}")
        return {"ai_response": "I'm here for you, let me gather my thoughts...", "llm_time_ms": 0}

async def tts_node(state: ConversationState, config=None):
    """
    Text-to-speech node. Streams audio using ElevenLabsStreamingService.
    Background processing is now handled by parallel subconscious_node.
    """
    manager = config.get("configurable", {}).get("manager") if config else None
    client_id = state["client_id"]
    user_id = state.get("user_id", client_id)
    if manager:
        await manager.send_status(client_id, "tts_generating")
    writer = get_stream_writer()
    audio_chunks = []
    start_time = time.time()
    def collect_chunk(chunk: bytes):
        audio_chunks.append(chunk)
        writer({"audio_chunk": chunk})
    await elevenlabs_streaming_service.stream_tts(state["ai_response"], collect_chunk)
    elapsed = time.time() - start_time
    elapsed_ms = int(elapsed * 1000)
    logger.info(f"[{client_id}] TTS inference: {elapsed_ms} ms. Chunks: {len(audio_chunks)}. Final size: {sum(len(c) for c in audio_chunks)} bytes")
    audio_output = b"".join(audio_chunks)
    # KEEP the long-term background processing trigger (3-minute cycles)
    try:
        started = await background_service_manager.ensure_user_background_processing(user_id)
        if started:
            logger.info(f"Ensured long-term background processing for {user_id}")
    except Exception as e:
        logger.error(f"Failed to ensure background processing for {user_id}: {e}")
    return {
        "audio_output": audio_output,
        "tts_time_ms": elapsed_ms
    }

async def subconscious_node(state: ConversationState, config=None):
    """
    Parallel subconscious processing - updates scaffolds AND stores conversation memory
    """
    try:
        client_id = state["client_id"]
        user_id = state.get("user_id", client_id)
        # Skip if no meaningful conversation to analyze
        if not state.get("transcript", "").strip() or not state.get("ai_response", "").strip():
            logger.debug(f"Skipping subconscious analysis for {user_id} - insufficient conversation data")
            return {}
        logger.info(f"Starting subconscious processing for {user_id}")
        # Real-time relationship analysis
        analysis_insights = await _perform_real_time_analysis(user_id, state)
        # Update scaffold with tiered storage
        await intimacy_scaffold_manager.update_scaffold_real_time(user_id, analysis_insights)
        logger.info(f"Completed subconscious processing for {user_id}")
        return {}
    except Exception as e:
        logger.error(f"Subconscious processing error for {client_id}: {e}")
        return {}

async def _perform_real_time_analysis(user_id: str, state: ConversationState) -> dict:
    """Perform immediate relationship analysis on current conversation"""
    user_message = state.get("transcript", "")
    ai_response = state.get("ai_response", "")
    # Quick emotional analysis of current exchange
    emotional_indicators = _analyze_current_emotional_state(user_message, ai_response)
    # Update communication DNA based on this interaction
    communication_updates = _analyze_communication_style(user_message)
    # Check for intimacy progression in this conversation
    intimacy_indicators = _assess_intimacy_progression(user_message, ai_response)
    # Look for unresolved threads or support needs
    support_needs = _identify_immediate_support_needs(user_message)
    return {
        "timestamp": datetime.now().isoformat(),
        "emotional_undercurrent": emotional_indicators.get("emotional_state", "neutral"),
        "communication_preferences": communication_updates,
        "intimacy_progression": intimacy_indicators,
        "support_needs": support_needs,
        "analysis_type": "real_time_conversation"
    }

def _analyze_current_emotional_state(user_message: str, ai_response: str) -> dict:
    user_lower = user_message.lower()
    if any(word in user_lower for word in ["sad", "worried", "stressed", "difficult", "upset"]):
        return {"emotional_state": "seeking_support", "intensity": "medium"}
    elif any(word in user_lower for word in ["happy", "excited", "great", "wonderful", "amazing"]):
        return {"emotional_state": "predominantly_positive", "intensity": "high"}
    elif any(word in user_lower for word in ["scared", "afraid", "vulnerable", "personal", "private"]):
        return {"emotional_state": "vulnerability_present", "intensity": "high"}
    else:
        return {"emotional_state": "exploring_connection", "intensity": "low"}

def _analyze_communication_style(user_message: str) -> dict:
    user_lower = user_message.lower()
    style_indicators = {}
    if len(user_message.split()) > 20:
        style_indicators["depth_preference"] = "detailed"
    elif len(user_message.split()) < 5:
        style_indicators["depth_preference"] = "concise"
    else:
        style_indicators["depth_preference"] = "moderate"
    if any(word in user_lower for word in ["feel", "feeling", "emotion", "heart"]):
        style_indicators["emotional_expression"] = "open"
    else:
        style_indicators["emotional_expression"] = "reserved"
    return style_indicators

def _assess_intimacy_progression(user_message: str, ai_response: str) -> dict:
    user_lower = user_message.lower()
    intimacy_level = "low"
    progression_indicators = []
    if any(phrase in user_lower for phrase in ["never told", "secret", "personal", "private"]):
        intimacy_level = "high"
        progression_indicators.append("deep_sharing")
    elif any(word in user_lower for word in ["worried", "concerned", "share", "open"]):
        intimacy_level = "medium"
        progression_indicators.append("personal_sharing")
    if any(phrase in user_lower for phrase in ["trust you", "comfortable", "feel safe"]):
        progression_indicators.append("trust_building")
    return {
        "current_intimacy_level": intimacy_level,
        "progression_indicators": progression_indicators
    }

def _identify_immediate_support_needs(user_message: str) -> list:
    user_lower = user_message.lower()
    support_needs = []
    if any(word in user_lower for word in ["work", "job", "boss", "deadline"]):
        support_needs.append("work_stress")
    if any(word in user_lower for word in ["family", "relationship", "friend"]):
        support_needs.append("relationship_concerns")
    if any(word in user_lower for word in ["tired", "exhausted", "overwhelmed"]):
        support_needs.append("emotional_overwhelm")
    if any(word in user_lower for word in ["decision", "choice", "unsure", "confused"]):
        support_needs.append("decision_support")
    return support_needs

# --- Build the graph ---
graph_builder = StateGraph(ConversationState)
graph_builder.add_node("stt_node", stt_node)
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tts_node", tts_node)
graph_builder.add_node("subconscious_node", subconscious_node)
graph_builder.add_edge(START, "stt_node")
graph_builder.add_edge("stt_node", "llm_node")
graph_builder.add_edge("llm_node", "tts_node")
graph_builder.add_edge("llm_node", "subconscious_node")
graph_builder.add_edge("tts_node", END)
graph_builder.add_edge("subconscious_node", END)

langgraph_pipeline = graph_builder.compile()

# Example usage (async):
# async for chunk in langgraph_pipeline.astream(
#     {"audio_input": b"...", "transcript": "", "ai_response": "Hello!", "audio_output": b"", "personality_type": "Neo", "client_id": "user1"},
#     stream_mode="values"
# ):
#     print(chunk) 