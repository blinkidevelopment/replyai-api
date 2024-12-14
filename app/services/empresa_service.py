from sqlalchemy.orm import Session

from app.db.models import Empresa, OutlookClient, DigisacClient, Assistente
from app.utils.digisac import Digisac
from app.utils.outlook import Outlook


async def obter_empresa(slug: str, token: str, db: Session):
    empresa = db.query(Empresa).filter_by(slug=slug, token=token).first()

    if empresa is not None:
        message_client_db = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
        agenda_client_db = db.query(OutlookClient).filter_by(id_empresa=empresa.id).first()
        nome_assistente_padrao = db.query(Assistente).filter_by(id=empresa.assistentePadrao).with_entities(Assistente.nome).scalar()

        message_client = Digisac(slug=message_client_db.digisacSlug, defaultUserId=message_client_db.digisacDefaultUser,
                                 defaultAssistantName=nome_assistente_padrao, token=message_client_db.digisacToken)
        agenda_client = Outlook(clientId=agenda_client_db.clientId, tenantId=agenda_client_db.tenantId, clientSecret=agenda_client_db.clientSecret,
                                duracaoEvento=agenda_client_db.duracaoEvento, usuarioPadrao=agenda_client_db.usuarioPadrao, horaInicioAgenda=agenda_client_db.horaInicioAgenda,
                                horaFinalAgenda=agenda_client_db.horaFinalAgenda, timeZone=agenda_client_db.timeZone)
        return empresa, message_client, agenda_client
    return None