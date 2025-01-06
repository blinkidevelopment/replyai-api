from sqlalchemy.orm import Session

from app.db.models import Empresa, OutlookClient, DigisacClient, Assistente
from app.services.mensagem_service import criar_message_client
from app.utils.outlook import Outlook


async def obter_empresa(slug: str, token: str, db: Session):
    empresa: Empresa | None = db.query(Empresa).filter_by(slug=slug, token=token).first()

    if empresa is not None:
        message_client = criar_message_client(empresa, db)

        agenda_client_db = db.query(OutlookClient).filter_by(id_empresa=empresa.id).first()
        agenda_client = Outlook(clientId=agenda_client_db.clientId, tenantId=agenda_client_db.tenantId, clientSecret=agenda_client_db.clientSecret,
                                duracaoEvento=agenda_client_db.duracaoEvento, usuarioPadrao=agenda_client_db.usuarioPadrao, horaInicioAgenda=agenda_client_db.horaInicioAgenda,
                                horaFinalAgenda=agenda_client_db.horaFinalAgenda, timeZone=agenda_client_db.timeZone)

        return empresa, message_client, agenda_client
    return None