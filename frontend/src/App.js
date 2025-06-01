// frontend/src/App.js

import React, { useState, useEffect, useRef } from 'react';
import AudioVisualizer from './components/AudioVisualizer';
import './App.css'; // Assuming you might want App-specific styles

function App() {
  // State to track if the agent is speaking (controlled by backend via WebSocket)
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  // Removed: State to hold the WebSocket connection (not directly used in render)
  
  const audioRef = useRef(null); // Ref to the audio element

  // Effect to manage the WebSocket connection
  useEffect(() => {
    // Establish WebSocket connection
    // Replace 'localhost' and port with your backend server address if different
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      console.log('WebSocket connected.');
      // Removed: setWebsocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        
        // Update speaking state based on backend message
        if (message.state === 'SPEAKING') {
          setIsAgentSpeaking(true);
        } else {
          setIsAgentSpeaking(false);
        }
        
        // TODO: Handle other states (LISTENING, THINKING, IDLE) if needed for other UI elements

      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      // Removed: setWebsocket(null);
      // Attempt to reconnect or show a disconnected state to the user if necessary
    };

    // Cleanup function to close the WebSocket connection when the component unmounts
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []); // Empty dependency array means this effect runs once on mount and cleans up on unmount

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sola AI Conversation</h1>
        {/* 
          This is a placeholder audio element.
          In a real app, the src would be dynamically set 
          or audio data would be streamed from the ElevenLabs backend.
        */}
        <audio ref={audioRef} controls src="/placeholder_audio.mp3" /> {/* You'll need a placeholder audio file in public/ */}

        {/* 
          Integrate the AudioVisualizer component.
          Pass the speaking state and the audio element.
        */}
        <AudioVisualizer isAgentSpeaking={isAgentSpeaking} audioElement={audioRef.current} />

        {/* Add other UI elements here for conversation input/output */}
      </header>
    </div>
  );
}

export default App; 