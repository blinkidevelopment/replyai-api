import json

import requests

from app.utils.crm_client import CRMClient


class RDStationCRM(CRMClient):
    def __init__(self, token: str, user_id: str, deal_stage_id: str, deal_source_id: str):
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.base_url = "https://crm.rdstation.com/api/v1"
        self.token = token
        self.deal_stage_inicial_user_id = user_id
        self.deal_stage_inicial_id = deal_stage_id
        self.deal_source_id = deal_source_id

    def criar_lead(self, nome_negociacao: str, nome_contato: str, telefone_contato: str):
        endpoint = f"{self.base_url}/deals?token={self.token}"

        request = {
            "deal": {
                "name": nome_negociacao,
                "rating": 1,
                "user_id": self.deal_stage_inicial_user_id,
                "deal_stage_id": self.deal_stage_inicial_id
            },
            "deal_source": {
                "_id": self.deal_source_id
            },
            "contacts": [
                {
                    "name": nome_contato,
                    "phones": [
                        {
                            "phone": telefone_contato,
                            "type": "cellphone"
                        }
                    ]
                }
            ]
        }

        resposta = requests.post(endpoint, headers=self.headers, json=request)
        resposta = json.loads(resposta.content)
        return resposta.get("id", None)

    def mudar_etapa(self, deal_id: str, deal_stage_id: str, user_id: str | None):
        endpoint = f"{self.base_url}/deals/{deal_id}?token={self.token}"

        request = {
            "deal_stage_id": deal_stage_id
        }

        if user_id:
            request["deal"] = {
                "user_id": user_id
            }

        resposta = requests.put(endpoint, headers=self.headers, json=request)

        if resposta.status_code == 200:
            return True
        return False
