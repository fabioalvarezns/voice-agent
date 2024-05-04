
def get_url(voice_id: str, service: str) -> str:
    match service:
        case 'elevenlabs':
            return f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        case 'deepgram':
            return (f"https://api.deepgram.com/v1/speak?model={voice_id}&performance=some&encoding=linear16"
                    f"&sample_rate=24000")
        case _:
            raise ValueError('an incorrect service was provided')


def default_voice_id(service: str) -> str:
    match service:
        case 'elevenlabs':
            return "AZnzlk1XvdvUeBnXmlld"
        case 'deepgram':
            return "aura-stella-en"
        case _:
            raise ValueError('an incorrect service was provided')


def get_headers(api_key: str, service: str) -> dict:
    match service:
        case 'elevenlabs':
            return {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
        case 'deepgram':
            return {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
        case _:
            raise ValueError('an incorrect service was provided')


def get_payload(text: str, service: str, model_id: str = "eleven_monolingual_v1"):
    match service:
        case 'elevenlabs':
            return {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

        case 'deepgram':
            return {"text": text}
        case _:
            raise ValueError('an incorrect service was provided')
