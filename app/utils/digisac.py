import json
import os
import mimetypes
from io import BytesIO
from time import sleep
from typing import List

import requests

from app.utils.message_client import MessageClient, DadosContato


class Digisac(MessageClient):
    def __init__(self, slug: str, defaultUserId: str, defaultAssistantName: str, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.slug = slug
        self.base_url = f"https://{slug}.digisac.me/api/v1"
        self.defaultUserId = defaultUserId
        self.defaultAssistantName = defaultAssistantName

    def enviar_mensagem(self, mensagem: str | None, audio: str | None, contact_id: str, userId: str | None, origin: str, nome_assistente: str | None):
        endpoint = f"{self.base_url}/messages"

        request = {
            "text": f"*{nome_assistente or self.defaultAssistantName}:*\n{mensagem or ''}",
            "type": "chat",
            "contactId": contact_id,
            "userId": userId or self.defaultUserId,
            "origin": origin
        }

        if audio is not None:
            file = {
                "base64": audio,
                "mimetype": "audio/mpeg",
                "name": "resposta"
            }
            request["file"] = file
            request["text"] = ""

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        return resposta

    def transferir(self, contactId: str, departmentId: str, userId: str | None, byUserId: str | None, comments: str | None):
        endpoint = f"{self.base_url}/contacts/{contactId}/ticket/transfer"

        request = {
            "departmentId": departmentId,
            "byUserId": byUserId or self.defaultUserId,
            "comments": comments or ""
        }

        if userId is not None:
            request["userId"] = userId

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        return resposta

    def adicionar_tag(self, contactId: str, tagIds: List[str]):
        endpoint = f"{self.base_url}/contacts/{contactId}"

        request = {
            "tagIds": tagIds
        }

        resposta = requests.put(endpoint, headers=self.headers, json=request)
        return resposta

    def encerrar_chamado(self, contactId: str, ticketTopicIds: List[str], comments: str | None, byUserId: str | None):
        endpoint = f"{self.base_url}/contacts/{contactId}/ticket/close"

        request = {
            "ticketTopicIds": ticketTopicIds,
            "comments": comments or "",
            "byUserId": byUserId or self.defaultUserId
        }

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        return resposta

    def obter_arquivo(self, messageId: str):
        tentativas = 0
        url = ""
        endpoint = f"{self.base_url}/messages/{messageId}?include=file"

        while url == "" and tentativas < 5:
            try:
                resposta = requests.get(endpoint, headers=self.headers)
            except:
                sleep(10)
                tentativas+=1
                break

            if resposta.status_code == 200:
                if resposta.json().get("file", {}).get("url", "") == "":
                    sleep(10)
                    tentativas+=1
                else:
                    url = resposta.json().get("file", {}).get("url", "")
            else:
                tentativas +=1

        if url != "":
            arquivo = requests.get(url)

            if arquivo.status_code == 200:
                file_name = arquivo.headers.get("Content-Disposition", "").split("filename=")[-1].strip('"')
                if file_name:
                    extensao = os.path.splitext(file_name)[1]
                else:
                    mime_type = arquivo.headers.get("Content-Type", "application/octet-stream")
                    extensao = mimetypes.guess_extension(mime_type) or ""

                mime_type = mimetypes.types_map.get(extensao, "application/octet-stream")

                file_stream = BytesIO(arquivo.content)
                arquivo_nome = f"arquivo_baixado{extensao}"

                return {"filename": arquivo_nome, "mimetype": mime_type, "file_stream": file_stream}
            return None
        return None

    def obter_dados_contato(self, contactId: str):
        endpoint = f"{self.base_url}/contacts/{contactId}"
        resposta = requests.get(endpoint, headers=self.headers)

        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            dados_contato = DadosContato(contact_name=resposta_obj.get("name", ""), phone_number=resposta_obj.get("data", {}).get("number", ""))
            return dados_contato
        return None
