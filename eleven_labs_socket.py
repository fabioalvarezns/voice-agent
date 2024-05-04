import asyncio
from dotenv import load_dotenv
import websockets
import json
import base64
import shutil
import os
import subprocess
import time
from services.llamager import AsyncLLamager


load_dotenv()


class ElevenLabsSocket:
    def __init__(self, voice_id) -> None:
        self.eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.groq = AsyncLLamager('elevenlabs')
        self.voice_id = voice_id

    def __is_installed(self, lib_name):
        return shutil.which(lib_name) is not None

    async def __text_chunker(self, chunks):
        """Split text into chunks, ensuring to not break sentences."""

        splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
        buffer = ""

        async for text in chunks:
            if buffer and buffer.endswith(splitters):
                yield buffer + " "
                buffer = text
            elif text and text.startswith(splitters):
                yield buffer + text[0] + " "
                buffer = text[1:]
            else:
                buffer += text if text is not None else ""

        if buffer:
            yield buffer + " "

    async def __stream(self, audio_stream):
        """Stream audio data using mpv player."""
        if not self.__is_installed("ffplay"):
            raise ValueError(
                "ffplay not found, necessary to stream audio. "

            )

        player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
        # mpv_process = subprocess.Popen(
        #     ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        #     stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        # )

        player_process = subprocess.Popen(
            player_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print("Started streaming audio")
        async for chunk in audio_stream:
            if chunk:
                player_process.stdin.write(chunk)
                player_process.stdin.flush()

        if player_process.stdin:
            player_process.stdin.close()
        player_process.wait()

    async def __text_to_speech_input_streaming(self, voice_id, text_iterator):
        """Send text to ElevenLabs API and stream the returned audio."""
        uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_turbo_v2"

        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({
                "text": " ",
                "model_id": 'eleven_multilingual_v1',
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                "xi_api_key": self.eleven_labs_api_key,
            }))

            async def listen():
                """Listen to the websocket for audio data and stream it."""
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if data.get("audio"):
                            yield base64.b64decode(data["audio"])
                        elif data.get('isFinal'):
                            break
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection closed")
                        break

            listen_task = asyncio.create_task(self.__stream(listen()))
            start_time = time.time()
            text_ia = ''
            async for text in self.__text_chunker(text_iterator):
                text_ia = text_ia + text
                await websocket.send(json.dumps({"text": text, "try_trigger_generation": True}))
            finish_time = time.time()  # Record the time when the first byte is received
            time_total = int((finish_time - start_time) * 1000)
            print(f'LLM ({time_total}): {text_ia}')
            await self.groq.conversation_handler(text_ia, 'assistant', False)
            await websocket.send(json.dumps({"text": ""}))

            await listen_task

    async def chat_completion(self, query):
        """Retrieve text from OpenAI and pass it to the text-to-speech function."""
        # response = await aclient.chat.completions.create(model='gpt-4', messages=[{'role': 'user', 'content': query}],
        # temperature=1, stream=True)

        response = await self.groq.process(query, "user", False)

        async def text_iterator():
            async for chunk in response:
                delta = chunk.choices[0].delta
                yield delta.content

        await self.__text_to_speech_input_streaming(self.voice_id, text_iterator())


# Main execution
if __name__ == "__main__":
    eleven = ElevenLabsSocket('21m00Tcm4TlvDq8ikWAM')

    user_query = "cuentame una historia de la luna muy muy muy corta"
    asyncio.run(eleven.chat_completion(user_query))
