# backend/main.py

import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading

# Import the function to create ElevenLabs components and the Conversation class
from elevenlabs_service import create_conversation_components, ConversationStateManager, Conversation # Import Conversation

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for ElevenLabs components and state
elevenlabs_client = None
state_manager: ConversationStateManager = None
conversation_instance = None
conversation_started = False # Flag to track if conversation session is started

# Initialize components on startup
@app.on_event("startup")
async def startup_event():
    global elevenlabs_client, state_manager, conversation_instance
    # Get the running asyncio event loop
    loop = asyncio.get_event_loop()
    elevenlabs_client, state_manager, conversation_instance = create_conversation_components(loop=loop)
    if not conversation_instance:
        print("Failed to initialize ElevenLabs conversation components.")
        # Consider exiting or disabling features if initialization fails

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

# To run this file with uvicorn:
# uvicorn main:app --reload 