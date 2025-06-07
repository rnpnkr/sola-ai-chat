from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import asyncio
from services.elevenlabs_streaming import ElevenLabsStreamingService
import os
from langgraph.config import get_stream_writer
import time
from services.deepgram_service import DeepgramService
from services.ai_service import OpenRouterService
import logging
from services.deepgram_streaming_service import DeepgramStreamingService
import uuid
import wave, contextlib, io, struct
from memory.mem0_async_service import IntimateMemoryService
from memory.memory_context_builder import MemoryContextBuilder
from memory.conversation_memory_manager import ConversationMemoryManager

logger = logging.getLogger(__name__)

# Define the conversation state schema
class ConversationState(TypedDict):
    audio_input: bytes
    transcript: str
    ai_response: str
    audio_output: bytes
    personality_type: str
    client_id: str

# --- Service instantiation ---
elevenlabs_streaming_service = ElevenLabsStreamingService()

# Initialize memory services
mem0_service = IntimateMemoryService()
memory_context_builder = MemoryContextBuilder(mem0_service)

# --- Node implementations ---

async def stt_node(state: ConversationState, config=None):
    """
    TEMPORARY: Use file-based STT until streaming frontend is implemented
    """
    # If transcript already exists (provided by streaming STT), skip file-based STT
    transcript = state.get("transcript", "")
    if transcript:
        logger.info(f"[{state['client_id']}] Streaming transcript provided to stt_node: '{transcript}'. Skipping file-based STT.")
        return {"transcript": transcript, "stt_time_ms": 0}
    else:
        logger.info(f"[{state['client_id']}] No streaming transcript found in stt_node. Running file-based STT.")
    manager = config.get("configurable", {}).get("manager") if config else None
    client_id = state["client_id"]
    audio_input = state["audio_input"]
    # Use original file-based service
    from services.deepgram_service import DeepgramService
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
    OpenRouter LLM with personality and streaming.
    Integrates PersonalityAgent (Neo) for prompt enhancement and response formatting.
    """
    try:
        from agents.personality_agent import PersonalityAgent, neo_config
        manager = config.get("configurable", {}).get("manager") if config else None
        client_id = state["client_id"]
        user_id = state.get("user_id", client_id)
        if manager:
            await manager.send_status(client_id, "llm_streaming")
        ai_service = OpenRouterService()
        personality_agent = PersonalityAgent(neo_config)
        # NEW: Get memory-informed context
        intimate_context = await memory_context_builder.build_intimate_context(
            current_message=state["transcript"],
            user_id=user_id
        )
        # NEW: Enhanced prompt with memory context
        enhanced_prompt = f"""{personality_agent.system_prompt}
\n{intimate_context}\n\nCurrent conversation: {state['transcript']}\n\nRespond with the warmth and understanding of someone who truly knows this person."""
        response = ""
        start_time = time.time()
        token_count = 0
        if hasattr(ai_service, 'get_streaming_response'):
            response_chunks = []
            async for chunk in ai_service.get_streaming_response(enhanced_prompt):
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
                enhanced_prompt
            )
            token_count = len(response.split())
        elapsed = time.time() - start_time
        elapsed_ms = int(elapsed * 1000)
        logger.info(f"[{client_id}] LLM inference: {elapsed_ms} ms. Tokens: {token_count}")
        response = personality_agent.format_response(response)
        return {"ai_response": response, "llm_time_ms": elapsed_ms}
    except Exception as e:
        logger.error(f"[{client_id}] LLM: Error - {str(e)}")
        return {"ai_response": "Sorry, I encountered an error processing your request.", "llm_time_ms": 0}

async def tts_node(state: ConversationState, config=None):
    """
    Text-to-speech node. Streams audio using ElevenLabsStreamingService.
    Sends WebSocket status updates and streams audio chunks using LangGraph's get_stream_writer.
    Receives ai_response, returns audio_output (bytes).
    """
    manager = config.get("configurable", {}).get("manager") if config else None
    client_id = state["client_id"]
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

    # NEW: Background memory storage (add before return)
    user_id = state.get("user_id", client_id)
    conversation_memory_manager = ConversationMemoryManager(mem0_service)
    memory_task = asyncio.create_task(
        conversation_memory_manager.store_intimate_conversation(
            user_message=state["transcript"],
            ai_response=state["ai_response"],
            user_id=user_id,
            emotional_context={"session_id": client_id}
        )
    )

    return {
        "audio_output": audio_output,
        "tts_time_ms": elapsed_ms,
        "memory_storage_task": memory_task
    }

# --- Build the graph ---
graph_builder = StateGraph(ConversationState)
graph_builder.add_node("stt_node", stt_node)
graph_builder.add_node("llm_node", llm_node)
graph_builder.add_node("tts_node", tts_node)
graph_builder.add_edge(START, "stt_node")
graph_builder.add_edge("stt_node", "llm_node")
graph_builder.add_edge("llm_node", "tts_node")
graph_builder.add_edge("tts_node", END)

langgraph_pipeline = graph_builder.compile()

# Example usage (async):
# async for chunk in langgraph_pipeline.astream(
#     {"audio_input": b"...", "transcript": "", "ai_response": "Hello!", "audio_output": b"", "personality_type": "Neo", "client_id": "user1"},
#     stream_mode="values"
# ):
#     print(chunk) 