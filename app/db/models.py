from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.database import Base


class Contato(Base):
    __tablename__ = "contatos"

    id = Column(Integer, primary_key=True, index=True)
    contactId = Column(String, index=True)
    threadId = Column(String)
    assistenteAtual = Column(Integer, ForeignKey("assistentes.id"))
    lastMessage = Column(DateTime)
    recallCount = Column(Integer)
    appointmentConfirmation = Column(Boolean)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="contatos")


class Assistente(Base):
    __tablename__ = "assistentes"

    id = Column(Integer, primary_key=True, index=True)
    assistantId = Column(String)
    nome = Column(String)
    proposito = Column(String)
    atalho = Column(String)
    id_voz = Column(Integer, ForeignKey("vozes.id"))
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="assistentes", foreign_keys=[id_empresa])


class Voz(Base):
    __tablename__ = "vozes"

    id = Column(Integer, primary_key=True, index=True)
    voiceId = Column(String)
    stability = Column(Float)
    similarity_boost = Column(Float)
    style = Column(Float)

    assistente = relationship("Assistente", backref="voz")


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, index=True)
    nome = Column(String)
    token = Column(String, unique=True, nullable=False)
    fuso_horario = Column(String)
    message_client_type = Column(String)
    agenda_client_type = Column(String)
    recall_timeout_minutes = Column(Integer)
    final_recall_timeout_minutes = Column(Integer)
    recall_quant = Column(Integer)
    recall_ativo = Column(Boolean)
    confirmar_agendamentos_ativo = Column(Boolean)
    tipo_cancelamento_evento = Column(String)
    mensagem_erro_ia = Column(String)
    assistentePadrao = Column(Integer, ForeignKey("assistentes.id"))

    assistente = relationship("Assistente", backref="assistente_padrao", foreign_keys=[assistentePadrao])


class Agenda(Base):
    __tablename__ = "agendas"

    id = Column(Integer, primary_key=True, index=True)
    endereco = Column(String)
    atalho = Column(String)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="agenda")


class EvolutionAPIClient(Base):
    __tablename__ = "evolutionapi_clients"

    id = Column(Integer, primary_key=True, index=True)
    apiKey = Column(String)
    instanceName = Column(String)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="evolutionapi_client")


class DigisacClient(Base):
    __tablename__ = "digisac_clients"

    id = Column(Integer, primary_key=True, index=True)
    digisacSlug = Column(String)
    service_id = Column(String)
    digisacToken = Column(String)
    digisacDefaultUser = Column(String)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="digisac_client")


class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    atalho = Column(String)
    comentario = Column(String)
    departmentId = Column(String)
    userId = Column(String)
    id_digisac_client = Column(Integer, ForeignKey("digisac_clients.id"))

    digisac_client = relationship("DigisacClient", backref="departamentos")


class OutlookClient(Base):
    __tablename__ = "outlook_clients"

    id = Column(Integer, primary_key=True, index=True)
    clientId = Column(String)
    tenantId = Column(String)
    clientSecret = Column(String)
    duracaoEvento = Column(Integer)
    usuarioPadrao = Column(String)
    horaInicioAgenda = Column(String)
    horaFinalAgenda = Column(String)
    timeZone = Column(String)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="outlook_client")


class GoogleCalendarClient(Base):
    __tablename__ = "googlecalendar_clients"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String)
    private_key_id = Column(String)
    private_key = Column(String)
    client_email = Column(String)
    client_id = Column(String)
    client_x509_cert_url = Column(String)
    api_key = Column(String)
    duracao_evento = Column(Integer)
    hora_inicio_agenda = Column(String)
    hora_final_agenda = Column(String)
    timezone = Column(String)
    id_empresa = Column(Integer, ForeignKey("empresas.id"))

    empresa = relationship("Empresa", backref="googlecalendar_client")
