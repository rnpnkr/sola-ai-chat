# backend/main.py

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from fastapi.responses import StreamingResponse
import io
from services.background_service_manager import background_service_manager
import signal

# Import the function to create ElevenLabs components and the Conversation class
from backend.conversational_api.elevenlabs_service import create_conversation_components, ConversationStateManager, Conversation # Import Conversation
from memory.mem0_async_service import IntimateMemoryService
from backend.subconscious.background_processor import PersistentSubconsciousProcessor
from services.rag_service import rag_service
import logging
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,  # Or DEBUG for more verbosity
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
# Global variables for ElevenLabs components and state
elevenlabs_client = None
state_manager: ConversationStateManager = None
conversation_instance = None
conversation_started = False # Flag to track if conversation session is started
mem0_service = None
subconscious_processor = None

# ADD: Import memory health monitor
def _import_memory_health_monitor():
    # Delayed import to avoid circular import issues
    from services.memory_health_monitor import memory_health_monitor
    return memory_health_monitor

# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    logger.info("startup event")
    global elevenlabs_client, state_manager, conversation_instance, mem0_service, subconscious_processor
    # Get the running asyncio event loop
    loop = asyncio.get_event_loop()
    elevenlabs_client, state_manager, conversation_instance = create_conversation_components(loop=loop)
    # ADD: Initialize subconscious processing
    mem0_service = IntimateMemoryService()
    subconscious_processor = PersistentSubconsciousProcessor(mem0_service)
    print("Subconscious processing system initialized")
    if not conversation_instance:
        print("Failed to initialize ElevenLabs conversation components.")
    # ADD: Initialize memory health monitoring
    memory_health_monitor = _import_memory_health_monitor()
    await memory_health_monitor.start_monitoring()
    print("Memory health monitoring initialized")
    logger.info("initializing rag")
    await initialize_system()
# Function to run the ElevenLabs conversation session in a separate thread
def run_conversation_session(conv: Conversation):
    try:
        print("Starting ElevenLabs conversation session thread...")
        conv.start_session()
        # The ElevenLabs SDK handles its own loop/threading within start_session
        # We can optionally wait for it to end if needed, but for a persistent server,
        # we likely want it to keep running until the server stops or session explicitly ended.
        # conv.wait_for_session_end() # Avoid blocking the thread indefinitely unless necessary
        print("ElevenLabs conversation session thread ended.")
    except Exception as e:
        print(f"Exception in conversation session thread: {e}")
        # Handle exceptions, e.g., set state to indicate error
async def initialize_system():
    # Initialize RAG with therapeutic documents
        therapeutic_docs = [
            "https://www.unk.com/blog/3-loneliness-busting-cbt-techniques-for-social-anxiety/",
            # Add other therapeutic documents
        ]
        await rag_service.initialize_documents(therapeutic_docs)
        print("rag initalized")
        logger.info("🚀 Therapeutic RAG system initialized")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted.")

    global conversation_started

    if not conversation_instance or not state_manager:
        print("ElevenLabs components not initialized. Closing WebSocket.")
        await websocket.close()
        return

    # Set the current client's websocket in the state manager
    await state_manager.set_websocket(websocket)

    # Start the conversation session in a separate thread only once
    if not conversation_started:
        print("Starting ElevenLabs conversation session for the first time...")
        conversation_thread = threading.Thread(
            target=run_conversation_session,
            args=(conversation_instance,)
        )
        conversation_thread.daemon = True # Allow the main program to exit even if this thread is running
        conversation_thread.start()
        conversation_started = True
        print("Conversation session thread started.")

    try:
        # Keep the WebSocket connection open to send messages from the state manager
        # We can wait here for messages from the frontend if needed for future features
        while True:
            # Example: receive text data from frontend
            # data = await websocket.receive_text()
            # print(f"Received message from client: {data}")
            await asyncio.sleep(0.1) # Small sleep to keep the loop non-blocking

    except Exception as e:
        # This exception likely occurs when the client disconnects
        print(f"WebSocket connection error or closed: {e}")
    finally:
        print("WebSocket connection closed.")
        # The Conversation session might still be running in the background thread.
        # If we need to stop it when the WebSocket closes, we would need more sophisticated
        # session management (e.g., tracking active clients, stopping session when last client disconnects)
        # For now, the background thread will continue running.
        # await state_manager.on_session_end() # This would incorrectly signal end if other clients connect later


# Optional: Add a root endpoint for testing
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Sola AI Chat Backend is running. Connect to /ws for conversation."}

# Import the LangGraph pipeline for visualization
def get_langgraph_png():
    try:
        from backend.agents.langgraph_orchestrator import langgraph_pipeline
        graph = langgraph_pipeline.get_graph()
        png_bytes = graph.draw_mermaid_png()
        return png_bytes
    except Exception as e:
        # Return a simple PNG with error text if visualization fails
        import PIL.Image, PIL.ImageDraw, PIL.ImageFont
        img = PIL.Image.new('RGB', (600, 100), color=(255, 255, 255))
        d = PIL.ImageDraw.Draw(img)
        d.text((10, 40), f"Graph viz error: {str(e)}", fill=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf.read()

@app.get("/graph", tags=["Graph"])
async def get_graph_png():
    """
    Returns a PNG image of the current LangGraph pipeline for visualization.
    """
    png_bytes = get_langgraph_png()
    return StreamingResponse(io.BytesIO(png_bytes), media_type="image/png")

async def shutdown_handler():
    """Gracefully shutdown background services"""
    print("Shutting down background services...")
    await background_service_manager.shutdown_all()

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(shutdown_handler())
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

setup_signal_handlers()

# ADD: New /health/memory endpoint
@app.get("/health/memory", tags=["Health"])
async def get_memory_health():
    """Get memory system health status"""
    memory_health_monitor = _import_memory_health_monitor()
    return await memory_health_monitor.get_health_report()

# To run this file with uvicorn:
# uvicorn main:app --reload 