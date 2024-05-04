import requests
import shutil
import subprocess
import time
from utils import (
    request,
    general
)


class TextToSpeech:
    def __init__(self, eleven_key):
        self.eleven_key = eleven_key

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        return shutil.which(lib_name) is not None

    def get_player(self):
        if not self.is_installed("ffplay"):
            raise ValueError("ffplay not found, necessary to stream audio.")

        player_command = general.get_player_commands()

        return subprocess.Popen(
            player_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def send_request(self, text: str, service: str):
        voice_id = request.default_voice_id(service)
        url = request.get_url(voice_id, service)
        headers = request.get_headers(self.eleven_key, service)
        payload = request.get_payload(text, service)
        return requests.post(url, json=payload, headers=headers)

    def speak(self, text: str, service: str, chunk_size: int = 1024):
        player = self.get_player()

        # Record the time before sending the request
        start_time = time.time()
        first_byte_time = None

        response = self.send_request(text, service)
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                if first_byte_time is None:
                    first_byte_time = general.calculate_first_byte(start_time)

                player.stdin.write(chunk)
                player.stdin.flush()

        if player.stdin:
            player.stdin.close()
        player.wait()
