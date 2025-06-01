# Tech Context

## Technologies Used
- Frontend/Mobile: bolt.new, React Native (planned), React (used for basic frontend structure), HTML5 Canvas (for visualization)
- Backend/AI: Eleven Labs (voice), FastAPI (web server), WebSockets (via FastAPI/uvicorn), mem0 (planned), Supabase (planned), OpenAI/Anthropic (planned), Pinecone/Weaviate (planned), PyAudio (used by DefaultAudioInterface)
- Additional Services: RevenueCat (planned), Sentry (planned), Analytics (planned)

## Development Setup
- Requires both Python and Node.js environments.
- Backend dependencies managed with `pip` and `requirements.txt`.
- Frontend dependencies managed with `npm` or `yarn` and `package.json`.
- Backend runs using `uvicorn`.
- Frontend runs using `react-scripts`.
- Environment variables (`.env`) required for ElevenLabs API key and Agent ID.

## Technical Constraints
- Real-time processing for voice remains a key constraint.
- Efficient memory management for long-term context (mem0 integration).
- Ensuring privacy and security of user data.
- ElevenLabs Python SDK limitations regarding direct audio output tracking and explicit state callbacks necessitate workarounds.

## Dependencies
- Backend: `elevenlabs`, `fastapi`, `uvicorn`, `python-multipart`, `python-dotenv`, `pyaudio`
- Frontend: `react`, `react-dom`, `react-scripts` 