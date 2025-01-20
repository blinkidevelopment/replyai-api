import requests
import json

from app.utils.financial_client import FinancialClient


class Asaas(FinancialClient):
    def __init__(self, token: str):
        self.headers = {
            "accept": "application/json",
            "access_token": token
        }
        self.base_url = "https://api.asaas.com/v3"

    def listar_cobrancas(self, due_date_le: str | None = None, due_date_ge: str | None = None, status: str | None = None, limit: str | None = None):
        endpoint = f"{self.base_url}/payments"
        params = {}

        if due_date_le:
            params["dueDate[le]"] = due_date_le
        if due_date_ge:
            params["dueDate[ge]"] = due_date_ge
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit

        resposta = requests.get(endpoint, headers=self.headers, params=params)
        resposta = json.loads(resposta.content)
        return resposta

    def obter_cliente(self, id_cliente: str):
        endpoint = f"{self.base_url}/customers/{id_cliente}"

        resposta = requests.get(endpoint, headers=self.headers)
        resposta = json.loads(resposta.content)
        return resposta