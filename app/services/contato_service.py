from datetime import datetime

import pytz
from sqlalchemy.orm import Session

from app.db.models import Contato, Assistente, Empresa, Departamento
from app.schemas.digisac_schema import DigisacRequest
from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.utils.assistant import Assistant
from app.utils.digisac import Digisac
from app.utils.message_client import MessageClient


async def obter_criar_contato(request: DigisacRequest | EvolutionAPIRequest | None, contact_id: str | None, empresa: Empresa, db: Session):
    if isinstance(request, DigisacRequest):
        contact_id = request.data.contactId
    elif isinstance(request, EvolutionAPIRequest):
        contact_id = request.data.key.remoteJid
    elif contact_id is not None:
        contact_id = contact_id
    else:
        raise ValueError("O corpo da requisição é de formato inválido")

    timezone = pytz.timezone(empresa.fuso_horario)
    contato = db.query(Contato).filter_by(contactId=contact_id).first()

    if contato is None:
        assistente_db = db.query(Assistente).filter_by(id=empresa.assistentePadrao, id_empresa=empresa.id).first()

        if assistente_db is not None:
            contato = Contato(
                contactId=contact_id,
                threadId="",
                assistenteAtual=assistente_db.id,
                lastMessage=datetime.now(timezone),
                recallCount=0,
                appointmentConfirmation=False,
                id_empresa=empresa.id
            )
            db.add(contato)
            db.commit()
            db.refresh(contato)
    else:
        contato.lastMessage = datetime.now(timezone)
        contato.recallCount = 0
        if contato.assistenteAtual:
            assistente_db = db.query(Assistente).filter_by(id=contato.assistenteAtual, id_empresa=empresa.id).first()
        else:
            assistente_db = db.query(Assistente).filter_by(id=empresa.assistentePadrao, id_empresa=empresa.id).first()
            await atualizar_assistente_atual_contato(contato, assistente_db.id, db)
        db.commit()
    assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
    return contato, assistente


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


async def redefinir_contato(contato: Contato, db: Session):
    contato.threadId = None
    contato.assistenteAtual = None
    contato.lastMessage = None
    contato.recallCount = 0
    contato.appointmentConfirmation = False
    db.commit()
