import io
from typing import List

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

    def adicionar_imagens(self, id_imagens: list, thread_id: str | None):
        for imagem in id_imagens:
            if thread_id is None:
                self.mensagens.append(
                    {
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
                )
            else:
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=[
                        {
                            "type": "image_file",
                            "image_file": {
                                "file_id": imagem,
                                "detail": "high"
                            }
                        }
                    ]
                )

    def subir_imagens(self, imagens: list):
        id_imagens = []

        for i, imagem in enumerate(imagens):
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

    def criar_rodar_thread(self):
        run = self.client.beta.threads.create_and_run(
            assistant_id=self.id,
            thread={
                "messages": self.mensagens
            }
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

        return resultado.data[0].content[0].text.value, run.thread_id

    def rodar_thread(self, thread_id: str):
        run = self.client.beta.threads.runs.create(
            assistant_id=self.id,
            thread_id=thread_id
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
    def __init__(self, data_hora_agendamento: str, titulo_evento: str, tag: str, mensagem: str):
        self.data_hora_agendamento = data_hora_agendamento
        self.titulo_evento = titulo_evento
        self.tag = tag
        self.mensagem = mensagem

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data_hora_agendamento=data["data_hora_agendamento"],
            titulo_evento=data["titulo_evento"],
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


class DadosData:
    def __init__(self, hoje: str, sugestao_inicial: str, numero_semana: str, semana_par_impar: str):
        self.hoje = hoje
        self.sugestao_inicial = sugestao_inicial
        self.numero_semana = numero_semana
        self.semana_par_impar = semana_par_impar

    def to_dict(self):
        return {
            "hoje": self.hoje,
            "sugestao_inicial": self.sugestao_inicial,
            "numero_semana": self.numero_semana,
            "semana_par_impar": self.semana_par_impar,
        }


class DadosAgenda:
    def __init__(self, data_sugerida: str, disponibilidade: str, horario_inicial: str, horario_final: str, intervalo_tempo: int):
        self.data_sugerida = data_sugerida
        self.disponibilidade = disponibilidade
        self.horario_inicial = horario_inicial
        self.horario_final = horario_final
        self.intervalo_tempo = intervalo_tempo

    def to_dict(self):
        return {
            "data_sugerida": self.data_sugerida,
            "disponibilidade": self.disponibilidade,
            "horario_inicial": self.horario_inicial,
            "horario_final": self.horario_final,
            "intervalo_tempo": self.intervalo_tempo,
        }


class DadosEvento:
    def __init__(self, email_agenda: str, titulo: str, local: str, data_hora_inicio: str, data_hora_fim: str, data_hora_atual: str):
        self.email_agenda = email_agenda
        self.titulo = titulo
        self.local = local
        self.data_hora_inicio = data_hora_inicio
        self.data_hora_fim = data_hora_fim
        self.data_hora_atual = data_hora_atual

    def to_dict(self):
        return {
            "email_agenda": self.email_agenda,
            "titulo": self.titulo,
            "local": self.local,
            "data_hora_inicio": self.data_hora_inicio,
            "data_hora_fim": self.data_hora_fim,
            "data_hora_atual": self.data_hora_atual
        }


class DadosEventoFechado:
    def __init__(self, titulo: str, disponibilidade: str):
        self.titulo_evento = titulo
        self.disponibilidade = disponibilidade

    def to_dict(self):
        return {
            "disponibilidade": self.disponibilidade,
            "titulo_evento": self.titulo_evento
        }


class Instrucao:
    def __init__(self, acao: str, dados: DadosData | DadosAgenda | DadosEvento | DadosEventoFechado | None):
        self.acao = acao
        self.dados = dados

    def to_dict(self):
        obj = {"acao": self.acao}
        if self.dados is not None:
            obj["dados"] = self.dados.to_dict()

        return obj

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=2)


class CustomHTTPClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        kwargs.pop("proxies", None)
        super().__init__(*args, **kwargs)