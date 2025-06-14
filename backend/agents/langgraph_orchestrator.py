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
from memory.memory_context_builder import MemoryContextBuilder
from memory.conversation_memory_manager import ConversationMemoryManager
from services.background_service_manager import background_service_manager
from datetime import datetime
from services.elevenlabs_websocket_service import ElevenLabsWebSocketService
from services.streaming_text_buffer import StreamingTextBuffer
from services.service_registry import ServiceRegistry
from contextlib import contextmanager

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
# elevenlabs_streaming_service = ElevenLabsStreamingService()

# Initialize memory services via registry (singleton)
mem0_service = ServiceRegistry.get_memory_service()
memory_context_builder = MemoryContextBuilder(mem0_service)

# Use shared scaffold manager via registry
from subconscious.anticipatory_engine import AnticippatoryIntimacyEngine

# NEW: Initialize intimacy services
intimacy_scaffold_manager = ServiceRegistry.get_scaffold_manager()
anticipatory_engine = AnticippatoryIntimacyEngine(mem0_service, intimacy_scaffold_manager)

# ---------------------------------------------------------------------------
# Memory layer toggle (set ENV var ENABLE_MEMORY_LAYER=false to fully disable)
# ---------------------------------------------------------------------------
ENABLE_MEMORY_LAYER = os.getenv("ENABLE_MEMORY_LAYER", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Utility: simple timing context manager for granular latency logging
# ---------------------------------------------------------------------------

@contextmanager
def time_section(section: str, client_id: str):
    """Log the execution time (in ms) of a code section identified by *section*."""
    start_ts = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = int((time.perf_counter() - start_ts) * 1000)
        logger.info(f"[{client_id}] ⏱️ {section} took {elapsed_ms} ms")

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

async def llm_tts_streaming_node(state: ConversationState, config=None):
    """
    Combined LLM + TTS streaming node for minimal latency
    Streams LLM tokens directly to ElevenLabs WebSocket
    """
    try:
        from voice_assistant import assistant
        from agents.personality_agent import PersonalityAgent, neo_config
        manager = config.get("configurable", {}).get("manager") if config else None
        client_id = state["client_id"]
        user_id = state.get("user_id", client_id)
        if manager:
            await manager.send_status(client_id, "llm_tts_streaming")
        # Initialize services
        ai_service = GroqService()
        personality_agent = PersonalityAgent(neo_config)
        elevenlabs_ws = ElevenLabsWebSocketService()
        text_buffer = StreamingTextBuffer(min_chunk_size=15, max_chunk_size=100)
        # --- Store TTS session in global assistant instance for interruption support ---
        assistant.active_tts_sessions[client_id] = elevenlabs_ws
        # Prepare context – now with granular latency tracking (skip when disabled)
        if ENABLE_MEMORY_LAYER:
            with time_section("build_intimate_context", client_id):
                intimate_context = await memory_context_builder.build_intimate_context(
                    current_message=state["transcript"],
                    user_id=user_id
                )
        else:
            intimate_context = ""  # Memory disabled

        # Retrieve intimacy scaffold (skip when disabled)
        if ENABLE_MEMORY_LAYER:
            with time_section("get_intimacy_scaffold", client_id):
                intimacy_scaffold = await intimacy_scaffold_manager.get_intimacy_scaffold(user_id)
        else:
            from subconscious.intimacy_scaffold import IntimacyScaffold  # lightweight import
            intimacy_scaffold = IntimacyScaffold()  # default empty scaffold

        # Anticipatory engine guidance can be heavy; also skip when memory disabled
        if ENABLE_MEMORY_LAYER:
            with time_section("anticipatory_engine_response_guidance", client_id):
                response_guidance = await anticipatory_engine.generate_response_guidance(
                    user_id=user_id,
                    current_message=state["transcript"]
                )
        else:
            response_guidance = ""
        # Build prompt (same as before)
        subconscious_prompt = f"""{personality_agent.system_prompt}

{intimate_context}

SUBCONSCIOUS UNDERSTANDING:
Emotional Undercurrent: {intimacy_scaffold.emotional_undercurrent}
Communication Style: {intimacy_scaffold.communication_dna.get('style', 'adaptive')}
Relationship Depth: {intimacy_scaffold.relationship_depth}
Current Emotional Mode: {intimacy_scaffold.emotional_availability_mode}
Intimacy Score: {intimacy_scaffold.intimacy_score:.2f}
Support Needs: {', '.join(intimacy_scaffold.support_needs) if intimacy_scaffold.support_needs else 'general presence'}

Current conversation: {state['transcript']}

Respond with the intuitive understanding of someone who truly knows this person's emotional landscape, current needs, and relationship dynamic.

Keep your responses short and concise.
"""
        # After building the prompt, add this debug logging:
        logger.info(f"🔍 [DEBUG] Complete LLM prompt being sent:")
        logger.info(f"🔍 [DEBUG] Intimate context: {intimate_context}")
        logger.info(f"🔍 [DEBUG] Full prompt length: {len(subconscious_prompt)} chars")

        # Setup audio streaming
        writer = get_stream_writer()
        audio_chunks = []
        chunk_count = 0
        def audio_callback(chunk: bytes):
            nonlocal chunk_count
            chunk_count += 1
            audio_chunks.append(chunk)
            writer({"audio_chunk": chunk})
            # Send to frontend
            if manager:
                import base64
                asyncio.create_task(manager.send_message(client_id, {
                    "type": "audio_chunk",
                    "audio_data": base64.b64encode(chunk).decode('utf-8'),
                    "chunk_number": chunk_count
                }))
        # Connect ElevenLabs WebSocket
        await elevenlabs_ws.connect_streaming_session(audio_callback)
        # Setup text streaming callback
        async def stream_text_to_tts(text_chunk: str):
            await elevenlabs_ws.stream_text_chunk(text_chunk)
        text_buffer.set_text_callback(stream_text_to_tts)
        # Stream LLM response and forward to TTS
        response = ""
        start_time = time.time()
        token_count = 0
        first_token_time = None

        if hasattr(ai_service, 'get_streaming_response'):
            async for chunk in ai_service.get_streaming_response(subconscious_prompt):
                if first_token_time is None:
                    first_token_time = time.time()
                    ttft = int((first_token_time - start_time) * 1000)
                    logger.info(f"🚀 [LATENCY] Time to first token: {ttft}ms")
                
                response += chunk
                token_count += 1
                
                # Log every 10th token to verify streaming
                if token_count % 10 == 0:
                    logger.info(f"[Streaming] Received {token_count} tokens, latest: '{chunk}'")
                # Send token to frontend
                if manager:
                    await manager.send_message(client_id, {
                        "type": "token_stream",
                        "content": chunk
                    })
                # Buffer token for TTS streaming
                await text_buffer.add_token(chunk)
        else:
            # Fallback for non-streaming AI services
            response = await asyncio.to_thread(ai_service.get_response, subconscious_prompt)
            token_count = len(response.split())
            # Send entire response to TTS
            await elevenlabs_ws.stream_text_chunk(response)
        # Finish streaming
        await text_buffer.finish()
        await elevenlabs_ws.flush_and_finish()
        elapsed = time.time() - start_time
        elapsed_ms = int(elapsed * 1000)
        logger.info(f"[{client_id}] Streaming complete: {elapsed_ms} ms. Tokens: {token_count}. Audio chunks: {chunk_count}")
        # Background processing trigger
        try:
            started = await background_service_manager.ensure_user_background_processing(user_id)
            if started:
                logger.info(f"Ensured long-term background processing for {user_id}")
        except Exception as e:
            logger.error(f"Failed to ensure background processing for {user_id}: {e}")
        # Send completion status
        if manager:
            await manager.send_status(client_id, "streaming_complete")
        # --- Cleanup TTS session tracking ---
        assistant.active_tts_sessions.pop(client_id, None)
        return {
            "ai_response": response,
            "audio_output": b"",  # Empty to avoid duplicate playback; chunks already streamed
            "llm_time_ms": elapsed_ms,
            "tts_time_ms": elapsed_ms
        }
    except Exception as e:
        # --- Cleanup on error ---
        assistant.active_tts_sessions.pop(client_id, None)
        logger.error(f"[{client_id}] Streaming error: {str(e)}")
        return {"ai_response": "I'm here for you, let me gather my thoughts...", "audio_output": b""}

async def subconscious_node(state: ConversationState, config=None):
    """Ensure background processing is running and store conversation memory"""
    try:
        from services.memory_coordinator import get_memory_coordinator
        from datetime import datetime
        client_id = state["client_id"]
        user_id = state.get("user_id", client_id)
        
        # FORCE background processing to start
        logger.info(f"🔄 Ensuring background processing for {user_id}")
        started = await background_service_manager.ensure_user_background_processing(user_id)
        if started:
            logger.info(f"✅ Background processing ensured for {user_id}")
        
        # Store conversation memory immediately (skip when memory layer disabled)
        if ENABLE_MEMORY_LAYER and state.get("transcript") and state.get("ai_response"):
            coordinator = get_memory_coordinator()
            memory_op_id = await coordinator.store_chat_and_memory(
                user_id=user_id,
                session_id=client_id,
                user_message=state["transcript"],
                ai_response=state["ai_response"],
                metadata={
                    "conversation_type": "voice_chat",
                    "timestamp": datetime.now().isoformat()
                }
            )
            logger.info(f"✅ Memory storage scheduled: {memory_op_id}")
        
        return {}
        
    except Exception as e:
        logger.error(f"❌ Subconscious processing error: {e}")
        return {}

# --- Build the graph ---
graph_builder = StateGraph(ConversationState)
graph_builder.add_node("stt_node", stt_node)
graph_builder.add_node("llm_tts_streaming_node", llm_tts_streaming_node)  # Combined node
graph_builder.add_node("subconscious_node", subconscious_node)

graph_builder.add_edge(START, "stt_node")
graph_builder.add_edge("stt_node", "llm_tts_streaming_node")
graph_builder.add_edge("llm_tts_streaming_node", "subconscious_node")
graph_builder.add_edge("llm_tts_streaming_node", END)
graph_builder.add_edge("subconscious_node", END)

langgraph_pipeline = graph_builder.compile()

# Example usage (async):
# async for chunk in langgraph_pipeline.astream(
#     {"audio_input": b"...", "transcript": "", "ai_response": "Hello!", "audio_output": b"", "personality_type": "Neo", "client_id": "user1"},
#     stream_mode="values"
# ):
#     print(chunk) 