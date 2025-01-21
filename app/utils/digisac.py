import json
import os
import mimetypes
from io import BytesIO
from time import sleep
from typing import List

import requests

from app.schemas.digisac_schema import DigisacRequest
from app.utils.message_client import MessageClient, DadosContato


class Digisac(MessageClient):
    def __init__(self, slug: str, service_id: str, defaultUserId: str, defaultAssistantName: str, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.slug = slug
        self.base_url = f"https://{slug}.digisac.me/api/v1"
        self.service_id = service_id
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

    def obter_arquivo(self, request: DigisacRequest, apenas_url: bool = False):
        tentativas = 0
        url = ""
        endpoint = f"{self.base_url}/messages/{request.data.message.id}?include=file"

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
            if apenas_url:
                return url

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

    def obter_dados_contato(self, request: DigisacRequest):
        endpoint = f"{self.base_url}/contacts/{request.data.contactId}"
        resposta = requests.get(endpoint, headers=self.headers)

        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            dados_contato = DadosContato(contact_name=resposta_obj.get("name", ""), phone_number=resposta_obj.get("data", {}).get("number", ""))
            return dados_contato
        return None

    def obter_id_contato(self, telefone: str, nome_contato: str):
        id_contato = None

        endpoint = f"{self.base_url}/contacts"
        resposta = requests.get(endpoint, headers=self.headers, params={
            "where[data.number]": telefone,
            "where[serviceId]": self.service_id
        })

        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            if resposta_obj.get("total", 0) > 0:
                data = resposta_obj.get("data")
                if len(data) > 0:
                    id_contato = data[0].get("id", None)

        if id_contato is None:
            resposta_cadastro = requests.post(endpoint, headers=self.headers, data={
                "serviceId": self.service_id,
                "internalName": nome_contato,
                "alternativeName": nome_contato,
                "number": telefone
            })

            if resposta_cadastro.status_code == 200:
                resposta_cadastro_obj = json.loads(resposta_cadastro.content)
                id_contato = resposta_cadastro_obj.get("id", None)
        return id_contato

    def obter_ticket_ultima_mensagem(self, contact_id: str):
        endpoint = f"{self.base_url}/contacts/{contact_id}"
        resposta = requests.get(endpoint, headers=self.headers)

        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            return resposta_obj.get("currentTicketId", None), resposta_obj.get("lastMessageId", None)
        return None

    def obter_origem_mensagem(self, message_id: str):
        endpoint = f"{self.base_url}/messages/{message_id}"
        resposta = requests.get(endpoint, headers=self.headers)

        if resposta.status_code == 200:
            resposta_obj = json.loads(resposta.content)
            return resposta_obj.get("origin", None)
        return None
