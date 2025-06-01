// components/WaveformCanvas.jsx

import React, { useRef, useEffect } from 'react';

// This file will handle the canvas rendering of the waveform.
// Based on the dev.to article: https://dev.to/ssk14/visualizing-audio-as-a-waveform-in-react-o67

const WaveformCanvas = ({ analyzer, isSpeaking }) => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const canvasCtx = canvas.getContext('2d');

        const draw = () => {
            if (!analyzer || !isSpeaking) {
                // Clear canvas when not speaking
                canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
                return;
            }

            const { dataArray, bufferLength } = analyzer.getFrequencyData();
            if (!dataArray) return;

            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 2.5; // Adjust multiplier for spacing
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = dataArray[i] / 2; // Adjust amplitude

                // Simple color gradient based on height (can be customized)
                const gradient = canvasCtx.createLinearGradient(0, canvas.height, 0, 0);
                gradient.addColorStop(1, 'red');
                gradient.addColorStop(0.5, 'yellow');
                gradient.addColorStop(0, 'green');
                canvasCtx.fillStyle = gradient; // Use gradient fill
                // canvasCtx.fillStyle = 'rgb(' + (barHeight + 100) + ',50,50)'; // Example static color

                canvasCtx.fillRect(x, canvas.height - barHeight / 2, barWidth, barHeight / 2); // Draw half bar mirrored
                canvasCtx.fillRect(x, canvas.height - (canvas.height - barHeight/2), barWidth, barHeight / 2); // Draw half bar mirrored


                x += barWidth + 1; // Spacing between bars
            }

            requestAnimationFrame(draw);
        };

        // Start drawing only if speaking state is true initially
        if (isSpeaking) {
             draw();
        }

        // Cleanup function
        return () => {
            // Any cleanup needed when component unmounts or isSpeaking changes to false
            // The draw loop naturally stops when isSpeaking is false
        };

    }, [analyzer, isSpeaking]); // Redraw effect when analyzer or isSpeaking changes

    return (
        <canvas ref={canvasRef} width="300" height="150" /> // Set appropriate width and height
    );
};

export default WaveformCanvas; 