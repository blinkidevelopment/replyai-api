import base64
from abc import ABC, abstractmethod

import requests


class MessageClient(ABC):
    @abstractmethod
    def enviar_mensagem(self, **kwargs):
        pass

    @abstractmethod
    def obter_dados_contato(self, **kwargs):
        pass

    @abstractmethod
    def obter_id_contato(self, telefone: str, nome_contato: str):
        pass

    @abstractmethod
    def obter_arquivo(self, **kwargs):
        pass

    @abstractmethod
    def baixar_arquivo(self, url: str):
        try:
            resposta = requests.get(url)
            resposta.raise_for_status()

            conteudo = base64.b64encode(resposta.content).decode('utf-8')
            return conteudo
        except requests.exceptions.RequestException as e:
            print(f"Erro ao baixar o arquivo: {e}")
            return None


class DadosContato:
    def __init__(self, contact_name: str, phone_number: str):
        self.contact_name = contact_name
        self.phone_number = phone_number

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            contact_name=data["contact_name"],
            phone_number=data["phone_number"]
        )

    def to_dict(self):
        return {
            "contactName": self.contact_name,
            "phoneNumber": self.phone_number
        }

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=2)