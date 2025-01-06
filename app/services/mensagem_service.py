from sqlalchemy.orm import Session

from app.db.models import Contato, Voz, Assistente, Empresa, DigisacClient, EvolutionAPIClient
from app.utils.assistant import Assistant
from app.utils.digisac import Digisac
from app.utils.eleven_labs import ElevenLabs
from app.utils.evolutionapi import EvolutionAPI
from app.utils.message_client import MessageClient


async def enviar_mensagem(mensagem: str, audio: bool, contato: Contato, message_client: MessageClient, assistente: Assistant, db: Session):
    msg_audio = None

    if audio:
        assistente_db = db.query(Assistente).filter_by(assistantId=assistente.id).first()
        if assistente_db is not None:
            voz = db.query(Voz).filter_by(id=assistente_db.id_voz).first() #TODO: reescrever a mensagem antes de gerar o áudio
            if voz is not None:
                elevenlabs_client = ElevenLabs()
                msg_audio = await elevenlabs_client.gerar_audio(mensagem=mensagem, id_voz=voz.voiceId, stability=voz.stability, similarity_boost=voz.similarity_boost, style=voz.style)
    message_client.enviar_mensagem(mensagem=mensagem, audio=msg_audio, contact_id=contato.contactId, userId=None, origin="bot", nome_assistente=assistente.nome)


def criar_message_client(empresa: Empresa, db: Session):
    nome_assistente_padrao = db.query(Assistente).filter_by(id=empresa.assistentePadrao).with_entities(Assistente.nome).scalar()

    if empresa.message_client_type == "digisac":
        digisac_client_db = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
        if digisac_client_db:
            return Digisac(
                slug=digisac_client_db.digisacSlug,
                defaultUserId=digisac_client_db.digisacDefaultUser,
                defaultAssistantName=nome_assistente_padrao,
                token=digisac_client_db.digisacToken
            )
    elif empresa.message_client_type == "evolution":
        evolutionapi_client_db = db.query(EvolutionAPIClient).filter_by(id_empresa=empresa.id).first()
        if evolutionapi_client_db:
            return EvolutionAPI(
                api_key=evolutionapi_client_db.apiKey,
                defaultAssistantName=nome_assistente_padrao,
                instance=evolutionapi_client_db.instanceName
            )
    else:
        raise ValueError(f"Tipo de MessageClient desconhecido: {empresa.message_client_type}")
    return None
