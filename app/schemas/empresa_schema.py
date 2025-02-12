from pydantic import BaseModel
from typing import List, Optional


class AsaasClientSchema(BaseModel):
    id: int
    token: str
    rotulo: str
    client_number: int

class RDStationCRMDealStageSchema(BaseModel):
    id: int
    atalho: str
    deal_stage_id: str
    user_id: Optional[str]
    deal_stage_inicial: bool

class RDStationCRMClientSchema(BaseModel):
    id: int
    token: str
    id_fonte_padrao: str
    estagios: Optional[List[RDStationCRMDealStageSchema]]

class AgendaSchema(BaseModel):
    id: int
    endereco: str
    atalho: str

class GoogleCalendarClientSchema(BaseModel):
    id: int
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    client_x509_cert_url: str
    api_key: str
    duracao_evento: int
    hora_inicio_agenda: str
    hora_final_agenda: str
    timezone: str

class OutlookClientSchema(BaseModel):
    id: int
    clientId: str
    tenantId: str
    clientSecret: str
    duracaoEvento: int
    usuarioPadrao: str
    horaInicioAgenda: str
    horaFinalAgenda: str
    timeZone: str

class EvolutionAPIClientSchema(BaseModel):
    id: int
    apiKey: str
    instanceName: str

class DepartamentoSchema(BaseModel):
    id: int
    atalho: str
    comentario: str
    departmentId: str
    userId: Optional[str]
    departamento_confirmacao: bool

class DigisacClientSchema(BaseModel):
    id: int
    digisacSlug: str
    digisacToken: str
    digisacDefaultUser: str
    service_id: str
    departamentos: Optional[List[DepartamentoSchema]]

    class Config:
        orm_mode = True

class VozSchema(BaseModel):
    id: int
    voiceId: str
    stability: float
    similarity_boost: float
    style: float

    class Config:
        orm_mode = True

class AssistenteSchema(BaseModel):
    id: int
    assistantId: str
    nome: str
    proposito: str
    atalho: str
    voz: Optional[VozSchema]

    class Config:
        orm_mode = True

class ColaboradorSchema(BaseModel):
    id: int
    nome: str
    apelido: str
    departamento: str

    class Config:
        orm_mode = True

class MidiaSchema(BaseModel):
    id: int
    url: str
    tipo: str
    mediatype: str
    nome: str
    atalho: str
    ordem: int

    class Config:
        orm_mode = True

class UsuarioSchema(BaseModel):
    id: int
    nome: str
    email: str
    ativo: bool
    admin: bool
    id_empresa: Optional[int] = None

    class Config:
        from_attributes = True

class EmpresaSchema(BaseModel):
    id: int
    nome: str
    slug: str
    token: str
    fuso_horario: str
    empresa_ativa: bool
    message_client_type: Optional[str]
    agenda_client_type: Optional[str]
    crm_client_type: Optional[str]
    financial_client_type: Optional[str]
    recall_timeout_minutes: Optional[int]
    final_recall_timeout_minutes: Optional[int]
    recall_quant: Optional[int]
    recall_ativo: Optional[bool]
    recall_confirmacao_ativo: Optional[bool]
    confirmar_agendamentos_ativo: Optional[bool]
    lembrar_vencimentos_ativo: Optional[bool]
    enviar_boleto_lembrar_vencimento: Optional[bool]
    cobrar_inadimplentes_ativo: Optional[bool]
    tipo_cancelamento_evento: Optional[str]
    mensagem_erro_ia: Optional[str]
    assistentes: List[AssistenteSchema]
    colaboradores: List[ColaboradorSchema]
    midias: List[MidiaSchema]
    vozes: List[VozSchema]
    assistentePadrao: Optional[int]
    agenda: Optional[List[AgendaSchema]]
    digisac_client: Optional[List[DigisacClientSchema]]
    evolutionapi_client: Optional[List[EvolutionAPIClientSchema]] = None
    outlook_client: Optional[List[OutlookClientSchema]]
    googlecalendar_client: Optional[List[GoogleCalendarClientSchema]]
    rdstationcrm_client: Optional[List[RDStationCRMClientSchema]]
    asaas_client: Optional[List[AsaasClientSchema]]

    class Config:
        orm_mode = True

class EmpresaMinSchema(BaseModel):
    id: int
    slug: str
    nome: str

    class Config:
        orm_mode = True

class ListaUsuariosSchema(BaseModel):
    has_more: bool
    next_cursor: Optional[int] = None
    limit: int
    data: List[UsuarioSchema]
