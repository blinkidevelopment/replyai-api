import os
import re
import base64
import mimetypes
import threading

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
        base64 = kwargs.get("base64", None)
        mediatype = kwargs.get("mediatype", "")
        nome_arquivo = kwargs.get("nome_arquivo", "")
        nome_assistente = kwargs.get("nome_assistente", self.defaultAssistantName)
        numero = re.match(r"(\d+)@", contact_id).group(1)

        request = {
            "number": numero
        }

        if base64 is not None:
            if mediatype.startswith("audio/"):
                endpoint = f"{self.base_url}/message/sendWhatsAppAudio/{self.instance}"
                request["audioMessage"] = {"audio": base64}
                request["options"] = {"encoding": False}
            else:
                if mediatype.startswith("image/"):
                    mediatype = "image"
                elif mediatype.startswith("video/"):
                    mediatype = "video"
                else:
                    mediatype = "document"

                endpoint = f"{self.base_url}/message/sendMedia/{self.instance}"
                request["mediaMessage"] = {
                    "mediatype": mediatype,
                    "fileName": nome_arquivo,
                    "caption": mensagem,
                    "media": base64
                }
        else:
            endpoint = f"{self.base_url}/message/sendText/{self.instance}"
            request["textMessage"] = {"text": f"*{nome_assistente}:*\n{mensagem or ''}"}

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        return resposta

    def enviar_presenca(self, contact_id: str, audio: bool):
        numero = re.match(r"(\d+)@", contact_id).group(1)
        endpoint = f"{self.base_url}/chat/sendPresence/{self.instance}"
        request = {
            "number": numero,
            "options": {
                "delay": 80000,
                "presence": "recording" if audio else "composing"
            }
        }

        funcao = lambda url, json, headers : requests.post(url, json=json, headers=headers)
        threading.Thread(target=funcao, args=(endpoint, request, self.headers), daemon=True).start()

    def obter_dados_contato(self, request: EvolutionAPIRequest):
        return DadosContato(contact_name=request.data.pushName,
                            phone_number=re.match(r"(\d+)@", request.data.key.remoteJid).group(1))

    def obter_id_contato(self, telefone: str, nome_contato: str):
        return f"{telefone}@s.whatsapp.net"

    def obter_arquivo(self, request: EvolutionAPIRequest):
        audio_bytes = base64.b64decode(request.data.message.base64)
        file_stream = BytesIO(audio_bytes)
        mimetype = request.data.message.audioMessage.mimetype or request.data.message.imageMessage.mimetype
        extensao = mimetypes.guess_extension(mimetype.split(";")[0].strip()) or ""
        arquivo_nome = f"arquivo_baixado{extensao}"

        return {"filename": arquivo_nome, "mimetype": mimetype, "file_stream": file_stream}

    def baixar_arquivo(self, url: str):
        return super().baixar_arquivo(url)

    def criar_instancia(self, global_api_key: str, nome_instancia: str):
        endpoint = f"{self.base_url}/instance/create"

        request = {
            "instanceName": nome_instancia,
            "integration": "WHATSAPP-BAILEYS"
        }

        headers = {
            "apikey": global_api_key,
            "Content-Type": "application/json"
        }

        resposta = requests.post(endpoint, headers=headers, json=request)
        return resposta

    def retornar_instancia(self):
        endpoint = f"{self.base_url}/instance/fetchInstances"
        resposta = requests.get(endpoint, headers=self.headers, params={
            "instanceName": self.instance
        })
        return resposta

    def conectar_instancia(self):
        endpoint = f"{self.base_url}/instance/connect/{self.instance}"
        resposta = requests.get(endpoint, headers=self.headers)
        return resposta

    def reiniciar_instancia(self):
        endpoint = f"{self.base_url}/instance/restart/{self.instance}"
        resposta = requests.put(endpoint, headers=self.headers)
        return resposta

    def desligar_instancia(self):
        endpoint = f"{self.base_url}/instance/logout/{self.instance}"
        resposta = requests.delete(endpoint, headers=self.headers)
        return resposta

    def checar_conexao(self):
        endpoint = f"{self.base_url}/instance/connectionState/{self.instance}"
        resposta = requests.get(endpoint, headers=self.headers)
        return resposta

    def adicionar_webhook(self, webhook_url: str, habilitado: bool):
        endpoint = f"{self.base_url}/webhook/set/{self.instance}"

        request = {
            "url": webhook_url,
            "events": [
                "MESSAGES_UPSERT"
            ],
            "webhook_base64": True,
            "enabled": habilitado
        }

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        return resposta

    def listar_webhooks(self):
        endpoint = f"{self.base_url}/webhook/find/{self.instance}"
        resposta = requests.get(endpoint, headers=self.headers)
        return resposta
