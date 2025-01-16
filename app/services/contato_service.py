from datetime import datetime, timedelta

import pytz
from sqlalchemy.orm import Session

from app.db.models import Contato, Assistente, Empresa, Departamento
from app.schemas.digisac_schema import DigisacRequest
from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.utils.assistant import Assistant
from app.utils.crm_client import CRMClient
from app.utils.digisac import Digisac
from app.utils.message_client import MessageClient


async def obter_criar_contato(request: DigisacRequest | EvolutionAPIRequest | None, contact_id: str | None, empresa: Empresa, message_client: MessageClient, crm_client: CRMClient | None, db: Session):
    if isinstance(request, DigisacRequest):
        contact_id = request.data.contactId
    elif isinstance(request, EvolutionAPIRequest):
        contact_id = request.data.key.remoteJid
    elif contact_id is not None:
        contact_id = contact_id
    else:
        raise ValueError("O corpo da requisição é de formato inválido")

    timezone = pytz.timezone(empresa.fuso_horario)
    agora = datetime.now(timezone)
    dados_contato = None
    contato = db.query(Contato).filter_by(contactId=contact_id, id_empresa=empresa.id).first()

    if contato is None:
        dados_contato = message_client.obter_dados_contato(request=request)

        id_negociacao = None
        if crm_client:
            id_negociacao = crm_client.criar_lead(nome_negociacao=dados_contato.contact_name,
                                                  nome_contato=dados_contato.contact_name,
                                                  telefone_contato=dados_contato.phone_number)

        contato = await criar_contato(contact_id, id_negociacao, empresa, timezone, True, db)
    else:
        if not contato.receber_respostas_ia:
            last_message_fuso = contato.lastMessage.replace(tzinfo=agora.tzinfo)
            if contato.lastMessage and (agora - last_message_fuso >= timedelta(days=1)):
                await mudar_recebimento_ia(contato, empresa, True, db)
            else:
                return contato, None, None

        contato.lastMessage = agora
        contato.recallCount = 0

        if contato.assistenteAtual:
            assistente_db = db.query(Assistente).filter_by(id=contato.assistenteAtual, id_empresa=empresa.id).first()
        else:
            assistente_db = db.query(Assistente).filter_by(id=empresa.assistentePadrao, id_empresa=empresa.id).first()
            await atualizar_assistente_atual_contato(contato, assistente_db.id, db)
        db.commit()
    assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
    if not contato.threadId and dados_contato is None:
        dados_contato = message_client.obter_dados_contato(request=request)

    return contato, assistente, dados_contato


async def criar_contato(contact_id: str, id_negociacao: str | None, empresa: Empresa, timezone: pytz.timezone, receber_respostas_ia: bool, db: Session):
    assistente_db = db.query(Assistente).filter_by(id=empresa.assistentePadrao, id_empresa=empresa.id).first()

    if assistente_db is not None:
        contato = Contato(
            contactId=contact_id,
            threadId="",
            assistenteAtual=assistente_db.id,
            lastMessage=datetime.now(timezone),
            recallCount=0,
            appointmentConfirmation=False,
            deal_id=id_negociacao,
            receber_respostas_ia=receber_respostas_ia,
            id_empresa=empresa.id
        )
        db.add(contato)
        db.commit()
        db.refresh(contato)
        return contato
    return None



async def atualizar_assistente_atual_contato(contato: Contato, id_assistente: int, db: Session):
    contato.assistenteAtual = id_assistente
    db.commit()


async def atualizar_thread_contato(contato: Contato, thread_id: str, db: Session):
    contato.threadId = thread_id
    db.commit()


async def encerrar_contato(contato: Contato, message_client: MessageClient, db: Session):
    if isinstance(message_client, Digisac):
        message_client.encerrar_chamado(contactId=contato.contactId, ticketTopicIds=[], comments="", byUserId=None)
    await redefinir_contato(contato, db)


async def transferir_contato(message_client: Digisac, contato: Contato, departamento: Departamento):
    message_client.transferir(contactId=contato.contactId, departmentId=departamento.departmentId, userId=departamento.userId, byUserId=None, comments=departamento.comentario)
    pass


async def mudar_recebimento_ia(contato: Contato | str, empresa: Empresa, valor: bool, db: Session):
    if isinstance(contato, str):
        contato_db = db.query(Contato).filter_by(contactId=contato, id_empresa=empresa.id).first()
        if not contato_db:
            timezone = pytz.timezone(empresa.fuso_horario)
            await criar_contato(contato, None, empresa, timezone, valor, db)
            return True
    else:
        contato_db = contato

    if contato_db and contato_db.receber_respostas_ia != valor:
        contato_db.receber_respostas_ia = valor
        db.commit()
        return True
    return False


async def redefinir_contato(contato: Contato, db: Session):
    contato.threadId = None
    contato.assistenteAtual = None
    contato.lastMessage = None
    contato.recallCount = 0
    contato.appointmentConfirmation = False
    db.commit()
