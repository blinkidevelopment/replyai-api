import json

from sqlalchemy.orm import Session

from app.db.models import Assistente, Empresa, AsaasClient
from app.utils.asaas import Asaas
from app.utils.assistant import Assistant, Instrucao, RespostaFinanceiro


async def extrair_dados_cobranca(
        acao: str,
        nome_cliente: str,
        telefone: str,
        data_atual: str,
        data_vencimento: str,
        descricao_boleto: str,
        empresa: Empresa,
        db: Session
):
    instrucao = Instrucao(
        acao=acao,
        dados={
            "nome_cliente": nome_cliente,
            "telefone": telefone,
            "data_vencimento": data_vencimento,
            "data_atual": data_atual,
            "descricao_boleto": descricao_boleto
        }
    )

    assistente_db = db.query(Assistente).filter_by(proposito="cobrar", id_empresa=empresa.id).first()

    try:
        if assistente_db is not None:
            assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
            assistente.adicionar_mensagens(mensagens=[instrucao.__str__()], id_arquivos=[], thread_id=None)
            resposta, thread_id = assistente.criar_rodar_thread()
            resposta_obj = RespostaFinanceiro.from_dict(json.loads(resposta))
            return resposta_obj, thread_id
    except Exception as e:
        print(e)
    return {}, None


def criar_financial_client(empresa: Empresa, db: Session):
    if empresa.financial_client_type == "asaas":
        asaas_client_db = db.query(AsaasClient).filter_by(id_empresa=empresa.id).first()
        if asaas_client_db:
            return Asaas(
                token=asaas_client_db.token
            )
