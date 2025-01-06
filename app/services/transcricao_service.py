from app.schemas.digisac_schema import DigisacRequest
from app.schemas.evolutionapi_schema import EvolutionAPIRequest
from app.utils.assistant import Assistant
from app.utils.digisac import Digisac
from app.utils.message_client import MessageClient


async def transcrever_audio_digisac(request: DigisacRequest | EvolutionAPIRequest, digisac_client: Digisac, assistente: Assistant):
    audio = False

    if isinstance(request, DigisacRequest):
        if request.data.message.type == "audio" or request.data.message.type == "ptt":
            audio = True
            arquivo = digisac_client.obter_arquivo(request.data.message.id)

            if arquivo is not None:
                transcricao = await assistente.transcrever_audio(arquivo)
                mensagem = transcricao
            else:
                mensagem = ""
        else:
            mensagem = request.data.message.text or ""
    elif isinstance(request, EvolutionAPIRequest):
        mensagem = ""
    return mensagem, audio


async def transcrever_audio(request: DigisacRequest | EvolutionAPIRequest, message_client: MessageClient, assistente: Assistant):
    audio = False
    mensagem = ""

    if isinstance(request, DigisacRequest):
        if request.data.message.type == "audio" or request.data.message.type == "ptt":
            audio = True
        else:
            mensagem = request.data.message.text or ""
    elif isinstance(request, EvolutionAPIRequest):
        if request.data.message.audioMessage is not None:
            audio = True
        else:
            mensagem = request.data.message.conversation or ""

    if audio:
        arquivo = message_client.obter_arquivo(request=request)
        if arquivo is not None:
            transcricao = await assistente.transcrever_audio(arquivo)
            mensagem = transcricao
    return mensagem, audio
