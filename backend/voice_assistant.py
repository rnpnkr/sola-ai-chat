"""
Voice Assistant - Main Application
Modular design allows easy swapping of services
"""
import os
from deepgram_service import DeepgramService
from ai_service import AzureOpenAIService
from tts_service import ElevenLabsService


class VoiceAssistant:
    def __init__(self, stt_service=None, ai_service=None, tts_service=None):
        """
        Initialize Voice Assistant with pluggable services

        Args:
            stt_service: Speech-to-Text service instance
            ai_service: AI response service instance
            tts_service: Text-to-Speech service instance
        """
        # Use default services if none provided
        self.stt_service = stt_service or DeepgramService()
        self.ai_service = ai_service or AzureOpenAIService()
        self.tts_service = tts_service or ElevenLabsService()

    def process_audio(self, input_audio_path, output_audio_path="ai_response.mp3"):
        """
        Process audio through the full pipeline

        Args:
            input_audio_path (str): Path to input audio file
            output_audio_path (str): Path for output audio file

        Returns:
            dict: Results from each step
        """
        results = {
            "input_file": input_audio_path,
            "transcript": None,
            "ai_response": None,
            "output_file": None,
            "success": False
        }

        if not os.path.exists(input_audio_path):
            print(f"❌ Input audio file '{input_audio_path}' not found!")
            return results

        try:
            print(f"🚀 Starting voice assistant pipeline...")
            print(f"📁 Input: {input_audio_path}")

            # Step 1: Speech to Text
            transcript = self.stt_service.transcribe(input_audio_path)
            results["transcript"] = transcript

            if not transcript:
                print("❌ Failed to transcribe audio")
                return results

            # Step 2: Get AI Response
            ai_response = self.ai_service.get_response(transcript)
            results["ai_response"] = ai_response

            if not ai_response:
                print("❌ Failed to get AI response")
                return results

            # Step 3: Text to Speech
            output_file = self.tts_service.text_to_speech(ai_response, output_audio_path)
            results["output_file"] = output_file

            if output_file:
                results["success"] = True
                print(f"🎉 Pipeline completed successfully!")
                print(f"📁 Output: {output_file}")
            else:
                print("❌ Failed to generate speech")

            return results

        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return results


def main():
    """Main function with easy service swapping examples"""

    # Example 1: Use default services (Deepgram + Azure OpenAI + ElevenLabs)
    print("=== Using Default Services ===")
    assistant = VoiceAssistant()
    result = assistant.process_audio("output.mp3", "ai_response_default.mp3")

    # Example 2: Mix and match services
    # print("\n=== Using Mixed Services ===")
    # from ai_service import OpenAIService
    # from tts_service import AzureTTSService
    #
    # custom_assistant = VoiceAssistant(
    #     stt_service=DeepgramService(),      # Keep Deepgram
    #     ai_service=OpenAIService(),         # Switch to regular OpenAI
    #     tts_service=AzureTTSService()       # Switch to Azure TTS
    # )
    # result = custom_assistant.process_audio("output1.mp3", "ai_response_custom.mp3")

    # Print results
    if result["success"]:
        print(f"\n✅ Success!")
        print(f"📝 Transcript: {result['transcript']}")
        print(f"🤖 AI Response: {result['ai_response']}")
        print(f"🔊 Audio saved: {result['output_file']}")
    else:
        print(f"\n❌ Pipeline failed")


if __name__ == "__main__":
    main()