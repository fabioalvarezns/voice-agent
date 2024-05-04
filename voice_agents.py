import os
import asyncio
from services.speech_to_text import SpeechToText
from services.text_to_speech import TextToSpeech
from services.llamager import LLamager
from eleven_labs_socket import ElevenLabsSocket


class ConversationManager:
    """
    A class to manage the conversations, using text to speech, llm and speech to text.
    init:
    - transcription_response: str: The transcription response of the conversation.
    - llm: str: The llm client for the conversation.
    - tts: TextToSpeech: The text to speech client for the conversation.
    -tts_socket: ElevenLabsSocket: The text to speech socket client for the conversation.
    - stt: SpeechToText: the speech to text client for the conversation.
    """
    def __init__(self):
        self.transcription_response = ""
        self.llm = LLamager('elevenlabs')
        self.tts = TextToSpeech(os.getenv("ELEVENLABS_API_KEY"))
        self.tts_socket = ElevenLabsSocket('21m00Tcm4TlvDq8ikWAM')
        self.stt = SpeechToText(os.getenv("DEEPGRAM_API_KEY"))

    async def voice_agent(self):
        def handle_full_sentence(full_sentence):
            self.transcription_response = full_sentence

        # Loop indefinitely until "goodbye" is detected
        while True:
            await self.stt.transcript(handle_full_sentence, self.llm)

            if "goodbye" in self.transcription_response.lower():
                break

            llm_response = self.llm.process(
                self.transcription_response,
                "user",
                False,
            )

            self.tts.speak(llm_response, "elevenlabs")

            # Reset transcription_response for the next loop iteration
            self.transcription_response = ""

    async def voice_agent_socket(self):
        def handle_full_sentence(full_sentence):
            self.transcription_response = full_sentence

        # Loop indefinitely until "goodbye" is detected
        while True:
            await self.stt.transcript(handle_full_sentence, self.llm)

            # Check for "goodbye" to exit the loop
            if "goodbye" in self.transcription_response.lower():
                break

            await self.tts_socket.chat_completion(self.transcription_response)

            # Reset transcription_response for the next loop iteration
            self.transcription_response = ""


if __name__ == "__main__":
    manager = ConversationManager()

    # asyncio.run(manager.voice_agent())
    asyncio.run(manager.voice_agent_socket())
