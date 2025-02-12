from datetime import datetime

import pytz

from app.db.database import retornar_sessao
from app.db.models import Assistente, Empresa


def obter_data_hora_atual(id_assistente: str):
    timezone = "UTC"

    with retornar_sessao() as db:
        assistente_db = db.query(Assistente).filter_by(assistantId=id_assistente).first()
        if assistente_db:
            empresa = db.query(Empresa).filter_by(id=assistente_db.id_empresa).first()
            if empresa:
                timezone = empresa.fuso_horario

    tz = pytz.timezone(timezone)
    now = datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")

    return {"current_datetime": now}
