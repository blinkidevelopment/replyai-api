import os
import re
import base64
import mimetypes

import requests
from io import BytesIO

from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.utils.message_client import MessageClient, DadosContato


class EvolutionAPI(MessageClient):
    def __init__(self, api_key: str, instance: str, defaultAssistantName: str):
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
        self.instance = instance
        self.base_url = os.getenv("EVOLUTIONAPI_SERVER")
        self.defaultAssistantName = defaultAssistantName

    def enviar_mensagem(self, **kwargs):
        contact_id = kwargs.get("contact_id", "")
        mensagem = kwargs.get("mensagem")
        audio = kwargs.get("audio", None)
        nome_assistente = kwargs.get("nome_assistente", self.defaultAssistantName)
        numero = re.match(r"(\d+)@", contact_id).group(1)

        if audio is not None:
            endpoint = f"{self.base_url}/message/sendWhatsAppAudio/{self.instance}"
            request = {
                "number": numero,
                "audioMessage": {
                    "audio": audio
                },
                "options": {
                    "encoding": False
                }
            }
        else:
            endpoint = f"{self.base_url}/message/sendText/{self.instance}"
            request = {
                "number": numero,
                "textMessage": {
                    "text": f"*{nome_assistente}:*\n{mensagem or ''}"
                }
            }

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        return resposta

    def obter_dados_contato(self, request: EvolutionAPIRequest):
        return DadosContato(contact_name=request.data.pushName,
                            phone_number=re.match(r"(\d+)@", request.data.key.remoteJid).group(1))

    def obter_arquivo(self, request: EvolutionAPIRequest):
        audio_bytes = base64.b64decode(request.data.message.base64)
        file_stream = BytesIO(audio_bytes)
        mimetype = request.data.message.audioMessage.mimetype or request.data.message.imageMessage.mimetype
        extensao = mimetypes.guess_extension(mimetype.split(";")[0].strip()) or ""
        arquivo_nome = f"arquivo_baixado{extensao}"

        return {"filename": arquivo_nome, "mimetype": mimetype, "file_stream": file_stream}
