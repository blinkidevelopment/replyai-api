from sqlalchemy.orm import Session

from app.db.models import Contato, Voz, Assistente, Empresa, DigisacClient, EvolutionAPIClient, Midia
from app.schemas.digisac_schema import DigisacRequest
from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.utils.assistant import Assistant
from app.utils.digisac import Digisac
from app.utils.eleven_labs import ElevenLabs
from app.utils.evolutionapi import EvolutionAPI
from app.utils.message_client import MessageClient


async def enviar_mensagem(mensagem: str, audio: bool, midia: str | None, contato: Contato, empresa: Empresa | None, message_client: MessageClient, assistente: Assistant, db: Session):
    msg_audio = None
    mediatype = ""

    if audio:
        if isinstance(message_client, Digisac):
            mediatype = "audio/mpeg"
        else:
            mediatype = "audio"
        assistente_db = db.query(Assistente).filter_by(assistantId=assistente.id).first()
        if assistente_db is not None:
            voz = db.query(Voz).filter_by(id=assistente_db.id_voz).first() #TODO: reescrever a mensagem antes de gerar o áudio
            if voz is not None:
                elevenlabs_client = ElevenLabs()
                msg_audio = await elevenlabs_client.gerar_audio(mensagem=mensagem, id_voz=voz.voiceId, stability=voz.stability, similarity_boost=voz.similarity_boost, style=voz.style)
    message_client.enviar_mensagem(mensagem=mensagem, base64=msg_audio, mediatype=mediatype, nome_arquivo=None, contact_id=contato.contactId, userId=None, origin="bot", nome_assistente=assistente.nome)

    if midia and empresa:
        midias_db = db.query(Midia).filter_by(atalho=midia, id_empresa=empresa.id).order_by(Midia.ordem).all()
        for midia_db in midias_db:
            conteudo = message_client.baixar_arquivo(midia_db.url)
            if conteudo:
                message_client.enviar_mensagem(mensagem="", base64=conteudo, mediatype=midia_db.mediatype, nome_arquivo=midia_db.nome, contact_id=contato.contactId, userId=None, origin="bot", nome_assistente=assistente.nome)


def criar_message_client(empresa: Empresa, db: Session):
    nome_assistente_padrao = db.query(Assistente).filter_by(id=empresa.assistentePadrao).with_entities(Assistente.nome).scalar()

    if empresa.message_client_type == "digisac":
        digisac_client_db = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
        if digisac_client_db:
            return Digisac(
                slug=digisac_client_db.digisacSlug,
                service_id=digisac_client_db.service_id,
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


async def obter_mensagem(request: DigisacRequest | EvolutionAPIRequest, message_client: MessageClient, assistente: Assistant):
    audio = False
    mensagem = ""
    imagem = ""

    if isinstance(request, DigisacRequest):
        if request.data.message.type == "audio" or request.data.message.type == "ptt":
            audio = True
        else:
            mensagem = request.data.message.text or ""
            if request.data.message.type == "image":
                imagem = message_client.obter_arquivo(request=request, apenas_url=True)
    elif isinstance(request, EvolutionAPIRequest):
        if request.data.message.audioMessage is not None:
            audio = True
        elif request.data.message.imageMessage is not None:
            mensagem = request.data.message.imageMessage.caption
            imagem = request.data.message.base64
        else:
            if request.data.message.extendedTextMessage:
                mensagem = request.data.message.extendedTextMessage.text
            else:
                mensagem = request.data.message.conversation or ""

    if audio:
        arquivo = message_client.obter_arquivo(request=request)
        if arquivo is not None:
            transcricao = await assistente.transcrever_audio(arquivo)
            mensagem = transcricao
    return mensagem, audio, imagem
