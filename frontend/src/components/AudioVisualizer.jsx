// components/AudioVisualizer.jsx

import React, { useState, useEffect, useRef } from 'react';
import AudioAnalyzer from './AudioAnalyzer';
import WaveformCanvas from './WaveformCanvas';

// This is the main component to tie together the audio analysis and canvas rendering.
// It will receive the speaking state and an audio element (or ref).

const AudioVisualizer = ({ isAgentSpeaking, audioElement }) => {
    const [analyzer, setAnalyzer] = useState(null);
    const audioRef = useRef(null); // Use ref if audioElement prop is not the direct element

    // If audioElement is passed as a prop, use it directly. Otherwise, assume it's via ref.
    const currentAudioElement = audioElement || audioRef.current;

    useEffect(() => {
        if (currentAudioElement) {
            // Initialize the analyzer when the audio element is available
            const audioAnalyzer = new AudioAnalyzer(currentAudioElement);
            audioAnalyzer.init();
            setAnalyzer(audioAnalyzer);

            // Clean up the analyzer when the component unmounts or audio element changes
            return () => {
                audioAnalyzer.disconnect();
                setAnalyzer(null);
            };
        } else {
             // Clean up if audio element becomes unavailable
             if(analyzer) {
                 analyzer.disconnect();
                 setAnalyzer(null);
             }
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentAudioElement]); // Re-run effect if audioElement prop or ref.current changes

    return (
        <div>
            {/* Render the canvas only if analyzer is initialized */}
            {analyzer && (
                <WaveformCanvas analyzer={analyzer} isSpeaking={isAgentSpeaking} />
            )}
            {/* 
             Optional: if you need to render an audio element managed by this component,
             uncomment the line below and ensure audioElement prop is NOT used.
             <audio ref={audioRef} src="your-audio-source.mp3" controls />
            */}
        </div>
    );
};

export default AudioVisualizer; 