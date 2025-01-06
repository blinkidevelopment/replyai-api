from datetime import datetime

import pytz
from sqlalchemy.orm import Session

from app.db.models import Contato, Assistente, Empresa
from app.schemas.digisac_schema import DigisacRequest
from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.utils.assistant import Assistant


async def obter_criar_contato(request: DigisacRequest | EvolutionAPIRequest, empresa: Empresa, db: Session):
    if isinstance(request, DigisacRequest):
        contact_id = request.data.contactId
    elif isinstance(request, EvolutionAPIRequest):
        contact_id = request.data.key.remoteJid
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
                appointmentConfirmation=False
            )
            db.add(contato)
            db.commit()
            db.refresh(contato)
    else:
        contato.lastMessage = datetime.now(timezone)
        db.commit()
        assistente_db = db.query(Assistente).filter_by(id=contato.assistenteAtual, id_empresa=empresa.id).first()
    assistente = Assistant(nome=assistente_db.nome, id=assistente_db.assistantId)
    return contato, assistente