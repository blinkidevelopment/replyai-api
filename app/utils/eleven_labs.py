import base64
import os

from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs as el


class ElevenLabs:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.client = el(api_key=self.elevenlabs_api_key)

    async def gerar_audio(self, mensagem: str, id_voz: str, stability: float, similarity_boost: float, style: float):
        audio_iterator = self.client.generate(
            text=mensagem,
            model="eleven_turbo_v2_5",
            voice=Voice(
                voice_id=id_voz,
                settings=VoiceSettings(stability=stability, similarity_boost=similarity_boost, style=style, use_speaker_boost=True)
            )
        )

        audio_bytes = b"".join(audio_iterator)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return audio_base64