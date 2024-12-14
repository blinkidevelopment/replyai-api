from app.schemas.digisac_schema import DigisacRequest
from app.utils.assistant import Assistant
from app.utils.digisac import Digisac


async def transcrever_audio_digisac(request: DigisacRequest, digisac_client: Digisac, assistente: Assistant):
    audio = False

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
    return mensagem, audio
