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

# --- Node implementations ---

async def stt_node(state: ConversationState, config=None):
    """
    Use file-based Deepgram transcription via DeepgramService.
    Adds file cleanup and enhanced error propagation via WebSocket.
    """
    temp_file = f"/tmp/audio_{state['client_id']}.wav"
    manager = config.get("configurable", {}).get("manager") if config else None
    client_id = state["client_id"]
    start_time = time.time()
    try:
        # Send stt_processing status for STT time measurement
        if manager:
            await manager.send_status(client_id, "stt_processing")
        logger.info(f"[{client_id}] STT: Processing {len(state['audio_input'])} bytes")
        with open(temp_file, 'wb') as f:
            f.write(state["audio_input"])
        stt_service = DeepgramService()
        transcript = await asyncio.to_thread(stt_service.transcribe, temp_file)
        elapsed = time.time() - start_time
        elapsed_ms = int(elapsed * 1000)
        logger.info(f"[{client_id}] STT inference: {elapsed_ms} ms. Transcript: {transcript}")
        return {"transcript": transcript, "stt_time_ms": elapsed_ms}
    except Exception as e:
        if manager:
            await manager.send_error(client_id, f"STT failed: {str(e)}")
        logger.error(f"[{client_id}] STT: Error - {str(e)}")
        return {"transcript": "", "stt_time_ms": 0}
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

async def llm_node(state: ConversationState, config=None):
    """
    OpenRouter LLM with personality and streaming.
    Integrates PersonalityAgent (Neo) for prompt enhancement and response formatting.
    """
    try:
        from agents.personality_agent import PersonalityAgent, neo_config
        manager = config.get("configurable", {}).get("manager") if config else None
        client_id = state["client_id"]
        if manager:
            await manager.send_status(client_id, "llm_streaming")
        ai_service = OpenRouterService()
        personality_agent = PersonalityAgent(neo_config)
        enhanced_prompt = f"{personality_agent.system_prompt}\n\nUser: {state['transcript']}"
        logger.info(f"[{client_id}] LLM: Prompt: {enhanced_prompt}")
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
    return {"audio_output": audio_output, "tts_time_ms": elapsed_ms}

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