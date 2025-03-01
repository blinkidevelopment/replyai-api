import base64
import os

from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs as el


class ElevenLabs:
    def __init__(self, api_key: str):
        self.client = el(api_key=api_key)

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

    def criar_voz(self, nome: str, descricao: str, arquivos: list[str]):
        voz = self.client.clone(name=nome, description=descricao, files=arquivos)
        return voz

    def obter_voz(self, voice_id: str):
        voz = self.client.voices.get(voice_id=voice_id)
        return voz if voz else None

    def editar_voz(self, voice_id: str, nome: str, descricao: str):
        try:
            self.client.voices.edit(
                voice_id=voice_id,
                name=nome,
                description=descricao
            )
            return True
        except Exception as e:
            print(f"Erro ao editar a voz da ElevenLabs: {e}")
            return False

    def excluir_voz(self, voice_id: str):
        try:
            self.client.voices.delete(
                voice_id=voice_id
            )
            return True
        except Exception as e:
            print(f"Erro ao excluir a voz da ElevenLabs: {e}")
            return False
