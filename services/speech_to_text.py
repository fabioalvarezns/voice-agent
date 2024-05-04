import asyncio
from services.llamager import LLamager, AsyncLLamager
from utils.deepgram import TranscriptCollector

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

transcript_collector = TranscriptCollector()


class SpeechToText:
    def __init__(self, deepgram_key):
        self.deepgram_key = deepgram_key

    @staticmethod
    def get_connection(deepgram_key: str):
        try:
            config = DeepgramClientOptions(options={"keepalive": "true"})
            client = DeepgramClient(deepgram_key, config)
            return client.listen.asynclive.v("1")

        except Exception as e:
            print(f"Unable to get deepgram connection: {e}")
            return

    @staticmethod
    def get_options():
        return LiveOptions(
            model="nova-2-general",
            punctuate=True,
            language="es-419",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            endpointing=300,
            smart_format=True,
        )

    async def transcript(self, callback, llm: LLamager | AsyncLLamager):
        # Event to signal transcription completion
        transcription_complete = asyncio.Event()
        try:
            dg_connection = self.get_connection(self.deepgram_key)
            print("Listening....")

            async def on_message(val, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                speech_final = "False"

                transcript_collector.add_part(sentence)
                full_sentence = transcript_collector.get_full_transcript()
                full_sentence = full_sentence.strip()

                if len(full_sentence) > 1 and speech_final == "False":
                    speech_final = llm.process(full_sentence, "user", True)
                    print(f"(stt) Validator:{full_sentence} | {speech_final}")

                if len(full_sentence) > 0 and speech_final != "False":
                    # This is the final part of the current sentence
                    # Call the callback with the full_sentence
                    callback(full_sentence)
                    transcript_collector.reset()

                    # Signal to stop transcription and exit
                    transcription_complete.set()

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = self.get_options()

            await dg_connection.start(options)

            # Open a microphone stream on the default input device
            microphone = Microphone(dg_connection.send)
            microphone.start()

            # Wait for the transcription to complete instead of looping indefinitely
            await transcription_complete.wait()

            # Wait for the microphone to close
            microphone.finish()

            # Indicate that we've finished
            await dg_connection.finish()

        except Exception as e:
            print(f"Could not open socket: {e}")
            return
