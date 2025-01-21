import io
import base64
from typing import List

from PIL import Image
from fastapi import UploadFile
import httpx
from openai import OpenAI
import os
import time


class Assistant:
    def __init__(self, nome: str, id: str):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(http_client=CustomHTTPClient())
        self.nome = nome
        self.id = id
        self.mensagens = []
        self.arquivos = []
        self.extensoes_audio = {
            "audio/mpeg": "mp3",
            "audio/wav": "wav",
            "audio/x-m4a": "m4a",
            "audio/m4a": "m4a",
            "audio/ogg": "oga",
            "audio/vorbis": "oga",
            "application/octet-stream": "oga"
        }

    def adicionar_mensagens(self, mensagens: list, id_arquivos: list, thread_id: str | None):
        for mensagem in mensagens:
            mensagem_base = {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": mensagem
                    }
                ]
            }

            if len(id_arquivos) > 0:
                mensagem_base["attachments"] = [
                    {
                        "file_id": arquivo,
                        "tools": [
                            {
                                "type": "file_search"
                            }
                        ]
                    } for arquivo in id_arquivos
                ]

            if thread_id is None:
                self.mensagens.append(mensagem_base)
            else:
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    **mensagem_base
                )

    def adicionar_imagens(self, id_imagens: list[str], thread_id: str | None):
        for imagem in id_imagens:
            if imagem.startswith("http"):
                mensagem_base = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": imagem
                            }
                        }
                    ]
                }
            else:
                mensagem_base = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_file",
                            "image_file": {
                                "file_id": imagem,
                                "detail": "high"
                            }
                        }
                    ]
                }

            if thread_id is None:
                self.mensagens.append(mensagem_base)
            else:
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    **mensagem_base
                )

    def subir_imagens(self, imagens: list):
        id_imagens = []

        for i, imagem in enumerate(imagens):
            if isinstance(imagem, str):
                if imagem.startswith("http"):
                    id_imagens.append(imagem)
                    continue
                else:
                    img_data = base64.b64decode(imagem)
                    imagem = Image.open(io.BytesIO(img_data))

            img_bytes = io.BytesIO()
            imagem.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            img_bytes.name = f'imagem_{i+1}.png'

            response = self.client.files.create(
                file=img_bytes,
                purpose="vision"
            )

            id_imagens.append(response.id)
        return id_imagens

    async def subir_arquivos(self, arquivos: list):
        id_arquivos = []

        for i, arquivo in enumerate(arquivos):
            conteudo = await arquivo.read()
            pdf_bytes = io.BytesIO(conteudo)
            pdf_bytes.seek(0)
            pdf_bytes.name = f'arquivo_{i+1}.pdf'

            response = self.client.files.create(
                file=pdf_bytes,
                purpose="assistants"
            )

            id_arquivos.append(response.id)
        return id_arquivos

    async def transcrever_audio(self, audio: dict):
        if audio.get("mimetype", "") in self.extensoes_audio:
            audio_bytes = audio.get("file_stream")
            audio_bytes.seek(0)
            audio_bytes.name = audio.get("filename")

            try:
                transcricao = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bytes
                )

                return transcricao.text
            except Exception as e:
                raise ValueError(f"Erro ao transcrever áudio: {str(e)}")
        else:
            raise ValueError("O arquivo de áudio não é compatível")

    def excluir_imagens(self, id_imagens: list):
        for imagem in id_imagens:
            self.client.files.delete(imagem)

    def adicionar_arquivos(self, arquivos: List[UploadFile]):
        for arquivo in arquivos:
            self.arquivos.append(arquivo)

    async def processar_arquivos(self):
        id_arquivos = []

        if len(self.arquivos) > 0:
            for arquivo in self.arquivos:
                if arquivo.content_type.startswith("audio/"):
                    await self.transcrever_audio(arquivo)
        return id_arquivos

    def criar_rodar_thread(self, thread_id: str | None = None):
        max_tentantivas = 5
        tentativa = 0

        while tentativa < max_tentantivas:
            tentativa += 1

            try:
                if thread_id:
                    runs = self.client.beta.threads.runs.list(
                        thread_id=thread_id,
                        limit=1,
                        order="desc"
                    )

                    if runs.data[0].status in ["queued", "in_progress", "cancelling"]:
                        time.sleep(15)
                        continue

                    run = self.client.beta.threads.runs.create(
                        assistant_id=self.id,
                        thread_id=thread_id
                    )
                else:
                    run = self.client.beta.threads.create_and_run(
                        assistant_id=self.id,
                        thread={
                            "messages": self.mensagens
                        }
                    )

                while run.status not in ["completed", "canceled", "failed", "expired"]:
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=run.thread_id,
                        run_id=run.id
                    )
                    time.sleep(2)

                if run.status in ["canceled", "failed", "expired"]:
                    print(f"Tentativa {tentativa}: Erro na geração de resposta (status: {run.status}). Tentando novamente...")
                    time.sleep(10)
                    continue

                resultado = self.client.beta.threads.messages.list(
                    thread_id=run.thread_id
                )

                return resultado.data[0].content[0].text.value, run.thread_id
            except Exception as e:
                print(f"Tentantiva {tentativa}: Ocorreu um erro inesperado: {e}")
                time.sleep(10)
                continue
        raise Exception(f"AIResponseError: Falha ao gerar uma resposta após {max_tentantivas} tentativas")

    def listar_mensagens_thread(self, thread_id: str):
        mensagens = self.client.beta.threads.messages.list(thread_id)
        return mensagens

    def obter_arquivo(self, file_id: str):
        try:
            conteudo = self.client.files.content(file_id)
            return conteudo
        except:
            raise ValueError("Não foi possível baixar o arquivo")
        
    def rodar_instrucao(self, thread_id: str, instrucoes: str):
        run = self.client.beta.threads.runs.create(
            assistant_id=self.id,
            thread_id=thread_id,
            instructions=instrucoes
        )

        while run.status != "completed":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=run.thread_id,
                run_id=run.id
            )
            time.sleep(2)

        resultado = self.client.beta.threads.messages.list(
            thread_id=run.thread_id
        )

        return resultado.data[0].content[0].text.value


class Resposta:
    def __init__(self, atividade: str, departamento: str, mensagem: str, agenda: str, assistente: str):
        self.atividade = atividade
        self.departamento = departamento
        self.mensagem = mensagem
        self.agenda = agenda
        self.assistente = assistente

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            atividade=data["atividade"],
            departamento=data["departamento"],
            mensagem=data["mensagem"],
            agenda=data["agenda"],
            assistente=data["assistente"]
        )


class RespostaDataSugerida:
    def __init__(self, data_sugerida: str, tag: str, mensagem: str):
        self.data_sugerida = data_sugerida
        self.tag = tag
        self.mensagem = mensagem

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data_sugerida=data["data_sugerida"],
            tag=data["tag"],
            mensagem=data["mensagem"]
        )


class RespostaAgendamento:
    def __init__(self, data_hora_agendamento: str, titulo_evento: str, descricao: str, localizacao: str, tag: str, mensagem: str):
        self.data_hora_agendamento = data_hora_agendamento
        self.titulo_evento = titulo_evento
        self.descricao = descricao
        self.localizacao = localizacao
        self.tag = tag
        self.mensagem = mensagem

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data_hora_agendamento=data["data_hora_agendamento"],
            titulo_evento=data["titulo_evento"],
            descricao=data["descricao"],
            localizacao=data["localizacao"],
            tag=data["tag"],
            mensagem=data["mensagem"]
        )


class RespostaConfirmacao:
    def __init__(self, cliente: str, telefone: str, resposta_confirmacao: Resposta):
        self.cliente = cliente
        self.telefone = telefone
        self.resposta_confirmacao = resposta_confirmacao

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            cliente=data["cliente"],
            telefone=data["telefone"],
            resposta_confirmacao=Resposta.from_dict(data["resposta_confirmacao"])
        )


class RespostaTituloAgenda:
    def __init__(self, endereco_agenda: str, titulo: str):
        self.endereco_agenda = endereco_agenda
        self.titulo = titulo

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            endereco_agenda=data["endereco_agenda"],
            titulo=data["titulo"]
        )


class RespostaTituloAgendaDataNova:
    def __init__(self, endereco_agenda: str, titulo: str, data_nova: str):
        self.endereco_agenda = endereco_agenda
        self.titulo = titulo
        self.data_nova = data_nova

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            endereco_agenda=data["endereco_agenda"],
            titulo=data["titulo"],
            data_nova=data["data_nova"]
        )


class RespostaFinanceiro:
    def __init__(self, telefone: str, resposta: Resposta):
        self.telefone = telefone
        self.resposta = resposta

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            telefone=data["telefone"],
            resposta=Resposta.from_dict(data["resposta"])
        )


class Instrucao:
    def __init__(self, acao: str, dados: dict | None):
        self.acao = acao
        self.dados = dados

    def to_dict(self):
        obj = {"acao": self.acao}
        if self.dados is not None:
            obj["dados"] = self.dados

        return obj

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=2)



class CustomHTTPClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        kwargs.pop("proxies", None)
        super().__init__(*args, **kwargs)