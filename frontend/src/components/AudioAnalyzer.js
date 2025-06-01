// components/AudioAnalyzer.js

// This file will contain the Web Audio API logic for analyzing audio data.
// Based on the dev.to article: https://dev.to/ssk14/visualizing-audio-as-a-waveform-in-react-o67

class AudioAnalyzer {
    constructor(audioElement) {
        this.audioElement = audioElement;
        this.audioCtx = null;
        this.analyzer = null;
        this.source = null;
        this.dataArray = null;
        this.bufferLength = null;
    }

    init() {
        // 1. Create AudioContext and AnalyserNode
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this.analyzer = this.audioCtx.createAnalyser();
        this.analyzer.fftSize = 2048; // Set FFT size
        this.bufferLength = this.analyzer.frequencyBinCount;
        this.dataArray = new Uint8Array(this.bufferLength);

        // 2. Connect to audio source
        // Check if audioElement is provided and valid
        if (this.audioElement) {
             try {
                 this.source = this.audioCtx.createMediaElementSource(this.audioElement);
                 this.source.connect(this.analyzer);
                 this.analyzer.connect(this.audioCtx.destination); // Connect analyzer to destination to hear audio
             } catch (error) {
                 console.error("Error connecting audio element to AudioContext:", error);
                 this.source = null; // Ensure source is null if connection fails
             }
        } else {
            console.warn("Audio element not provided to AudioAnalyzer.");
        }
    }

    getFrequencyData() {
        if (this.analyzer) {
            // Get frequency data (or getByteTimeDomainData for waveform if needed)
            this.analyzer.getByteFrequencyData(this.dataArray); // Use this for bars based on frequency
            // this.analyzer.getByteTimeDomainData(this.dataArray); // Use this for raw waveform
            return { dataArray: this.dataArray, bufferLength: this.bufferLength };
        }
        return null;
    }

    // Method to disconnect or clean up if needed
    disconnect() {
        if (this.source) {
            this.source.disconnect();
        }
        if (this.analyzer) {
             this.analyzer.disconnect();
        }
        if (this.audioCtx) {
            this.audioCtx.close().catch(e => console.error("Error closing audio context:", e));
        }
        this.audioCtx = null;
        this.analyzer = null;
        this.source = null;
        this.dataArray = null;
        this.bufferLength = null;
    }
}

export default AudioAnalyzer; 