# Current Task: LangGraph Streaming Pipeline Implementation

## Task Summary
Implement a modular LangGraph streaming pipeline for the voice assistant backend. This includes a personality agent, LangGraph orchestrator with streaming nodes (STT, LLM, TTS), ElevenLabs WebSocket streaming, and integration into the main assistant service. The system must support real-time streaming at every node, emit progress/status updates via WebSocket, and preserve existing infrastructure.

## Key PRD Snippets & Requirements

### Dependencies
- Add to `requirements.txt`:
  - langgraph>=0.2.0
  - langchain>=0.3.0
  - langchain-openai>=0.2.0
  - pydantic>=2.0.0

### Core Files to Create
- `backend/agents/personality_agent.py` (PersonalityAgent class)
- `backend/agents/langgraph_orchestrator.py` (LangGraph pipeline with streaming nodes)
- `backend/services/elevenlabs_streaming.py` (WebSocket TTS streaming)
- Modify `voice_assistant.py` (replace with EnhancedVoiceAssistant)

### State Schema
```python
from typing_extensions import TypedDict
from typing import List

class ConversationState(TypedDict):
    audio_input: bytes
    transcript: str
    ai_response: str
    audio_output: bytes
    personality_type: str
    client_id: str
```

### Graph Structure
- STT Node → LLM Node → TTS Node
- Each node streams: status, tokens, audio

### WebSocket Message Extensions
- Add `langgraph_stream` message type for streaming endpoint

### Integration Points
- Preserve existing WebSocket infrastructure
- Add LangGraph as parallel processing path
- Stream at node, token, and audio levels
- Graceful error handling in each node

## Step-by-Step Breakdown

### 1. **First Step: Personality Agent**
- Create `backend/agents/personality_agent.py`
  - Implement `PersonalityAgent` and `PersonalityConfig`
  - Add system prompt and response formatting logic

### 2. **LangGraph Orchestrator**
- Create `backend/agents/langgraph_orchestrator.py`
  - Implement LangGraph pipeline with STT, LLM, TTS nodes
  - Use `StateGraph`, `stream_mode="messages"` for LLM, `stream_mode="values"` for state
  - Each node is async and streams updates

### 3. **ElevenLabs Streaming Service**
- Create `backend/services/elevenlabs_streaming.py`
  - Implement WebSocket streaming to ElevenLabs
  - Stream audio chunks back via callback

### 4. **Integrate into Main Assistant**
- Modify `voice_assistant.py`
  - Replace with `EnhancedVoiceAssistant`
  - Add `process_audio_stream_with_langgraph`
  - Add WebSocket handler for `langgraph_stream` message type

### 5. **Testing & Validation**
- Test each component incrementally
- Ensure streaming at every node and WebSocket status updates
- Handle errors gracefully

### 6. **Final Result**
- Fully modular, streaming LangGraph pipeline integrated into the backend
- Real-time progress/status/tokens/audio streamed to client via WebSocket
- Existing sequential path preserved; LangGraph is an alternative/parallel path

## Checkbox Tracker
- [ ] Add dependencies to `requirements.txt`
- [ ] Create `backend/agents/personality_agent.py`
- [ ] Create `backend/agents/langgraph_orchestrator.py`
- [ ] Create `backend/services/elevenlabs_streaming.py`
- [ ] Modify `voice_assistant.py` with EnhancedVoiceAssistant
- [ ] Add `langgraph_stream` WebSocket message type
- [ ] Test streaming at each node (status, tokens, audio)
- [ ] Ensure error handling in all nodes
- [ ] Validate end-to-end streaming pipeline

## What's Left to Build
- All steps above (none started yet)

## Current Status
- Task and requirements documented. Implementation not yet started.

## Known Issues
- None yet (to be discovered during implementation) 