from sqlalchemy.orm import Session

from app.db.models import Contato, Voz, Assistente
from app.utils.assistant import Assistant
from app.utils.eleven_labs import ElevenLabs
from app.utils.message_client import MessageClient


async def enviar_mensagem(mensagem: str, audio: bool, contato: Contato, message_client: MessageClient, assistente: Assistant, db: Session):
    if audio:
        assistente_db = db.query(Assistente).filter_by(assistantId=assistente.id).first()

        if assistente_db is not None:
            voz = db.query(Voz).filter_by(id=assistente_db.id_voz).first() #TODO: reescrever a mensagem antes de gerar o áudio
            if voz is not None:
                elevenlabs_client = ElevenLabs()
                msg_audio = await elevenlabs_client.gerar_audio(mensagem=mensagem, id_voz=voz.voiceId, stability=voz.stability, similarity_boost=voz.similarity_boost, style=voz.style)
    else:
        msg_audio = None
    message_client.enviar_mensagem(mensagem=mensagem, audio=msg_audio, contact_id=contato.contactId, userId=None, origin="bot", nome_assistente=assistente.nome)