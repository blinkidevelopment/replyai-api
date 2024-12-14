from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.schemas.digisac_schema import DigisacRequest
from app.services.contato_service import obter_criar_contato
from app.services.direcionamento_service import direcionar
from app.services.empresa_service import obter_empresa
from app.services.thread_service import rodar_criar_thread
from app.services.transcricao_service import transcrever_audio_digisac
from app.db.database import obter_sessao


router = APIRouter()

@router.post("/digisac/{slug}/{token}")
async def responder_digisac(request: DigisacRequest, slug: str, token:str, db: Session = Depends(obter_sessao)):
    resultado = False
    dados_empresa = await obter_empresa(slug, token, db)

    if dados_empresa is not None:
        empresa, message_client, agenda_client = dados_empresa
        contato, assistente = await obter_criar_contato(request.data.contactId, empresa, db)
        mensagem, audio = await transcrever_audio_digisac(request, message_client, assistente)
        if not contato.threadId:
            dados_contato = message_client.obter_dados_contato(request.data.contactId)
        else:
            dados_contato = None
        resposta = await rodar_criar_thread(mensagem, contato, dados_contato, assistente, db)
        await direcionar(resposta, audio, message_client, agenda_client, empresa, contato, assistente, db)
        resultado = True
    db.close()
    return resultado
