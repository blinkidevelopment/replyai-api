from datetime import datetime

import pytz

from app.db.database import retornar_sessao
from app.db.models import Assistente, Empresa, Colaborador


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


def obter_colaboradores(id_assistente: str):
    with retornar_sessao() as db:
        assistente_db = db.query(Assistente).filter_by(assistantId=id_assistente).first()
        if assistente_db:
            empresa = db.query(Empresa).filter_by(id=assistente_db.id_empresa).first()
            if empresa:
                colaboradores = db.query(Colaborador).filter_by(id_empresa=empresa.id).all()
                data = [
                    {"nome": colab.nome, "apelido": colab.apelido, "departamento": colab.departamento}
                    for colab in colaboradores
                ]

                return {"employees": data}
    return {"employees": ""}
