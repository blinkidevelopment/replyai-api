from pydantic import BaseModel, field_validator, Field
from typing import List, Optional, Literal


class InformacoesCriarEmpresa(BaseModel):
    nome: str
    slug: str
    fuso_horario: str
    openai_api_key: str
    empresa_ativa: bool

class InformacoesBasicas(BaseModel):
    nome: str
    fuso_horario: str
    empresa_ativa: bool

class InformacoesColaborador(BaseModel):
    id: Optional[int] = None
    nome: str
    apelido: Optional[str] = None
    departamento: Optional[str] = None

    @field_validator("apelido", "departamento", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor or None

    @field_validator("id", mode="before")
    @classmethod
    def int_vazio(cls, valor):
        if isinstance(valor, str) and valor.strip() == "":
            return None
        return valor

class InformacoesMidia(BaseModel):
    id: Optional[int] = None
    url: str
    tipo: str
    mediatype: str
    nome: str
    atalho: str
    ordem: int

    @field_validator("id", mode="before")
    @classmethod
    def int_vazio(cls, valor):
        if isinstance(valor, str) and valor.strip() == "":
            return None
        return valor

class InformacoesAssistentes(BaseModel):
    assistente_padrao: Optional[int] = None

    @field_validator("assistente_padrao", mode="before")
    @classmethod
    def int_vazio(cls, valor):
        if isinstance(valor, str) and valor.strip() == "":
            return None
        return valor

class InformacoesAssistente(BaseModel):
    id: Optional[int] = None
    nome: str
    assistant_id: str
    proposito: str
    atalho: str
    voz: int

class InformacoesVoz(BaseModel):
    id: Optional[int] = None
    voice_id: str
    stability: float
    similarity_boost: float
    style: float

class InformacoesMensagens(BaseModel):
    tipo_cliente: Literal["digisac", "evolution"]
    tempo_recall_min: int
    tempo_recall_final_min: int
    quant_recalls: int
    ativar_recall: bool
    mensagem_erro_ia: Optional[str] = None

    @field_validator("mensagem_erro_ia", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor or None

class InformacoesEvolutionAPI(BaseModel):
    api_key: str
    instance_name: str

class InformacoesDigisac(BaseModel):
    slug: str
    token: str
    user_id: str
    service_id: str

class InformacoesDepartamento(BaseModel):
    id: Optional[int] = None
    atalho: str
    comentario: str
    department_id: str
    user_id: Optional[str] = None
    departamento_confirmacao: bool

    @field_validator("user_id", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor or None

class InformacoesAgenda(BaseModel):
    tipo_cliente: Optional[Literal["outlook", "google_calendar"]]
    tipo_cancelamento_evento: str
    ativar_confirmacao: bool

    @field_validator("tipo_cliente", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor if valor.strip() else None

class InformacoesAgendaUnica(BaseModel):
    id: Optional[int] = None
    endereco: str
    atalho: str

class InformacoesOutlook(BaseModel):
    client_id: str
    tenant_id: str
    client_secret: str
    duracao_evento: int
    usuario_padrao: str
    hora_inicial: str
    hora_final: str
    fuso_horario: str

class InformacoesGoogleCalendar(BaseModel):
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    client_x509_cert_url: str
    api_key: str
    duracao_evento: int
    hora_inicial: str
    hora_final: str
    fuso_horario: str

class InformacoesCRM(BaseModel):
    tipo_cliente: Optional[Literal["rdstation"]]

    @field_validator("tipo_cliente", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor if valor.strip() else None

class InformacoesRDStationCRMClient(BaseModel):
    token: str
    id_fonte_padrao: str

class InformacoesRDStationDealStage(BaseModel):
    id: Optional[int] = None
    atalho: str
    deal_stage_id: str
    user_id: Optional[str] = None
    estagio_inicial: bool

    @field_validator("user_id", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor if valor.strip() else None

class InformacoesFinanceiras(BaseModel):
    tipo_cliente: Optional[Literal["asaas"]]
    lembrar_vencimentos: bool
    cobrar_inadimplentes: bool

    @field_validator("tipo_cliente", mode="before")
    @classmethod
    def string_vazia(cls, valor):
        return valor if valor.strip() else None

class InformacoesAsaas(BaseModel):
    token: str
    rotulo: str
    numero_cliente: int
