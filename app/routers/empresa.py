from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session, joinedload

from app.db.database import obter_sessao
from app.db.models import Empresa, Assistente, DigisacClient, EvolutionAPIClient, Departamento, OutlookClient, \
    GoogleCalendarClient, RDStationCRMClient, RDStationCRMDealStage, AsaasClient, Agenda, Usuario
from app.routers.usuario import obter_usuario_logado
from app.schemas.atualizacao_empresa_schema import InformacoesBasicas, InformacoesMensagens, InformacoesDigisac, \
    InformacoesEvolutionAPI, InformacoesDepartamento, InformacoesAgenda, InformacoesOutlook, InformacoesGoogleCalendar, \
    InformacoesAssistentes, InformacoesCRM, InformacoesRDStationCRMClient, InformacoesRDStationDealStage, \
    InformacoesFinanceiras, InformacoesAsaas, InformacoesAssistente, InformacoesAgendaUnica
from app.schemas.empresa_schema import EmpresaSchema, AgendaSchema, DepartamentoSchema, AssistenteSchema, \
    DigisacClientSchema, EvolutionAPIClientSchema, OutlookClientSchema, GoogleCalendarClientSchema, \
    RDStationCRMClientSchema, RDStationCRMDealStageSchema, AsaasClientSchema

# TODO: implementar services
router = APIRouter(dependencies=[Depends(obter_usuario_logado)])

@router.get("/") # TODO: retornar apenas nome, slug e id da empresa
async def obter_todas_empresas(usuario: Usuario = Depends(obter_usuario_logado), db: Session = Depends(obter_sessao)):
    if not usuario.id_empresa:
        empresas = db.query(Empresa).all()
    else:
        empresas = db.query(Empresa).filter_by(id=usuario.id_empresa).all()
    return empresas

@router.get("/{slug}", response_model=EmpresaSchema) # TODO: restringir apenas às empresas que o usuário pode ver
async def obter_empresa(slug: str, db: Session = Depends(obter_sessao)):
    empresa = (
        db.query(Empresa)
        .options(
            joinedload(Empresa.digisac_client),
            joinedload(Empresa.evolutionapi_client),
            joinedload(Empresa.assistentes),
        )
        .filter_by(slug=slug)
        .first()
    )

    return empresa

@router.put("/{slug}/informacoes_basicas", response_model=EmpresaSchema)
async def alterar_informacoes_basicas(slug: str, request: InformacoesBasicas, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresa.nome = request.nome
    empresa.fuso_horario = request.fuso_horario
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_assistentes", response_model=EmpresaSchema)
async def alterar_informacoes_assistentes(slug: str, request: InformacoesAssistentes, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    assistente = db.query(Assistente).filter_by(id=request.assistente_padrao, id_empresa=empresa.id, proposito="responder").first()
    if not assistente:
        raise HTTPException(status_code=404, detail="Assistente não encontrado para essa empresa")

    empresa.assistentePadrao = request.assistente_padrao
    db.commit()
    return empresa

@router.post("/{slug}/informacoes_assistentes/assistente")
async def adicionar_assistente(slug: str, request: InformacoesAssistente, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    assistente = Assistente(
        assistantId=request.assistant_id,
        nome=request.nome,
        proposito=request.proposito,
        atalho=request.atalho,
        id_voz=request.voz,
        id_empresa=empresa.id
    )

    db.add(assistente)
    db.commit()
    db.refresh(assistente)
    return assistente

@router.put("/{slug}/informacoes_assistentes/assistente", response_model=AssistenteSchema)
async def alterar_informacoes_assistentes(slug: str, request: InformacoesAssistente, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    assistente = db.query(Assistente).filter_by(id=request.id, id_empresa=empresa.id).first()
    if not assistente:
        raise HTTPException(status_code=404, detail="Assistente não encontrado para essa empresa")

    assistente.nome = request.nome
    assistente.assistantId = request.assistant_id
    assistente.proposito = request.proposito
    assistente.atalho = request.atalho
    assistente.id_voz = request.voz
    db.commit()
    return assistente

@router.put("/{slug}/informacoes_mensagens", response_model=EmpresaSchema)
async def alterar_informacoes_mensagens(slug: str, request: InformacoesMensagens, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresa.message_client_type = request.tipo_cliente
    empresa.recall_timeout_minutes = request.tempo_recall_min
    empresa.final_recall_timeout_minutes = request.tempo_recall_final_min
    empresa.recall_quant = request.quant_recalls
    empresa.recall_ativo = request.ativar_recall
    empresa.mensagem_erro_ia = request.mensagem_erro_ia
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_mensagens/digisac", response_model=DigisacClientSchema)
async def alterar_informacoes_digisac(slug: str, request: InformacoesDigisac, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    digisac_client = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
    if not digisac_client:
        raise HTTPException(status_code=404, detail="Cliente do Digisac não encontrado para essa empresa")

    digisac_client.digisacSlug = request.slug
    digisac_client.digisacToken = request.token
    digisac_client.digisacDefaultUser = request.user_id
    digisac_client.service_id = request.service_id
    db.commit()
    return digisac_client

@router.post("/{slug}/informacoes_mensagens/digisac/departamento")
async def adicionar_departamento(slug: str, request: InformacoesDepartamento, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    digisac_client = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
    if not digisac_client:
        raise HTTPException(status_code=404, detail="Cliente do Digisac não encontrado para essa empresa")

    departamento = Departamento(
        atalho=request.atalho,
        comentario=request.comentario,
        departmentId=request.department_id,
        userId=request.user_id,
        departamento_confirmacao=request.departamento_confirmacao,
        id_digisac_client=digisac_client.id
    )

    db.add(departamento)
    db.commit()
    db.refresh(departamento)
    return departamento

@router.put("/{slug}/informacoes_mensagens/digisac/departamento", response_model=DepartamentoSchema)
async def alterar_informacoes_departamento(slug: str, request: InformacoesDepartamento, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    digisac_client = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
    if not digisac_client:
        raise HTTPException(status_code=404, detail="Cliente do Digisac não encontrado para essa empresa")

    departamento = db.query(Departamento).filter_by(id=request.id, id_digisac_client=digisac_client.id).first()
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento não encontrado para essa cliente do Digisac")

    departamento.atalho = request.atalho
    departamento.comentario = request.comentario
    departamento.departmentId = request.department_id
    departamento.userId = request.user_id
    departamento.departamento_confirmacao = request.departamento_confirmacao
    db.commit()
    return departamento

@router.put("/{slug}/informacoes_mensagens/evolutionapi", response_model=EvolutionAPIClientSchema)
async def alterar_informacoes_digisac(slug: str, request: InformacoesEvolutionAPI, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    evolutionapi_client = db.query(EvolutionAPIClient).filter_by(id_empresa=empresa.id).first()

    if not evolutionapi_client:
        raise HTTPException(status_code=404, detail="Cliente do EvolutionAPI não encontrado para essa empresa")

    evolutionapi_client.apiKey = request.api_key
    evolutionapi_client.instanceName = request.instance_name
    db.commit()
    return evolutionapi_client

@router.put("/{slug}/informacoes_agenda", response_model=EmpresaSchema)
async def alterar_informacoes_agenda(slug: str, request: InformacoesAgenda, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresa.agenda_client_type = request.tipo_cliente
    empresa.tipo_cancelamento_evento = request.tipo_cancelamento_evento
    empresa.confirmar_agendamentos_ativo = request.ativar_confirmacao
    db.commit()
    return empresa

@router.post("/{slug}/informacoes_agenda/agenda")
async def adicionar_agenda(slug: str, request: InformacoesAgendaUnica, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    agenda = Agenda(
        endereco=request.endereco,
        atalho=request.atalho,
        id_empresa=empresa.id
    )

    db.add(agenda)
    db.commit()
    db.refresh(agenda)
    return agenda

@router.put("/{slug}/informacoes_agenda/agenda", response_model=AgendaSchema)
async def alterar_informacoes_agenda(slug: str, request: InformacoesAgendaUnica, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    agenda = db.query(Agenda).filter_by(id=request.id, id_empresa=empresa.id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda não encontrada para essa empresa")

    agenda.endereco = request.endereco
    agenda.atalho = request.atalho
    db.commit()
    return agenda

@router.put("/{slug}/informacoes_agenda/outlook", response_model=OutlookClientSchema)
async def alterar_informacoes_outlook(slug: str, request: InformacoesOutlook, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    outlook_client = db.query(OutlookClient).filter_by(id_empresa=empresa.id).first()
    if not outlook_client:
        raise HTTPException(status_code=404, detail="Cliente do Outlook não encontrado para essa empresa")

    outlook_client.clientId = request.client_id
    outlook_client.tenantId = request.tenant_id
    outlook_client.clientSecret = request.client_secret
    outlook_client.duracaoEvento = request.duracao_evento
    outlook_client.usuarioPadrao = request.usuario_padrao
    outlook_client.horaInicioAgenda = request.hora_inicial
    outlook_client.horaFinalAgenda = request.hora_final
    outlook_client.timeZone = request.fuso_horario
    db.commit()
    return outlook_client

@router.put("/{slug}/informacoes_agenda/googlecalendar", response_model=GoogleCalendarClientSchema)
async def alterar_informacoes_googlecalendar(slug: str, request: InformacoesGoogleCalendar, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    googlecalendar_client = db.query(GoogleCalendarClient).filter_by(id_empresa=empresa.id).first()
    if not googlecalendar_client:
        raise HTTPException(status_code=404, detail="Cliente do Google Calendar não encontrado para essa empresa")

    googlecalendar_client.project_id = request.project_id
    googlecalendar_client.private_key_id = request.private_key_id
    googlecalendar_client.private_key = request.private_key
    googlecalendar_client.client_email = request.client_email
    googlecalendar_client.client_id = request.client_id
    googlecalendar_client.client_x509_cert_url = request.client_x509_cert_url
    googlecalendar_client.api_key = request.api_key
    googlecalendar_client.duracao_evento = request.duracao_evento
    googlecalendar_client.hora_inicio_agenda = request.hora_inicial
    googlecalendar_client.hora_final_agenda = request.hora_final
    googlecalendar_client.timezone = request.fuso_horario
    db.commit()
    return googlecalendar_client

@router.put("/{slug}/informacoes_crm", response_model=EmpresaSchema)
async def alterar_informacoes_crm(slug: str, request: InformacoesCRM, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresa.crm_client_type = request.tipo_cliente
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_crm/rdstation", response_model=RDStationCRMClientSchema)
async def alterar_informacoes_rdstation(slug: str, request: InformacoesRDStationCRMClient, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    rdstationcrm_client = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
    if not rdstationcrm_client:
        raise HTTPException(status_code=404, detail="Cliente do RD Station CRM não encontrado para essa empresa")

    rdstationcrm_client.token = request.token
    rdstationcrm_client.id_fonte_padrao = request.id_fonte_padrao
    db.commit()
    return rdstationcrm_client

@router.post("/{slug}/informacoes_crm/rdstation/estagio")
async def adicionar_estagio(slug: str, request: InformacoesRDStationDealStage, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    rdstationcrm_client = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
    if not rdstationcrm_client:
        raise HTTPException(status_code=404, detail="Cliente do RD Station CRM não encontrado para essa empresa")

    estagio = RDStationCRMDealStage(
        atalho=request.atalho,
        deal_stage_id=request.deal_stage_id,
        user_id=request.user_id,
        deal_stage_inicial=request.estagio_inicial,
        id_rdstationcrm_client=rdstationcrm_client.id
    )

    db.add(estagio)
    db.commit()
    db.refresh(estagio)
    return estagio

@router.put("/{slug}/informacoes_crm/rdstation/estagio", response_model=RDStationCRMDealStageSchema)
async def alterar_informacoes_estagio(slug: str, request: InformacoesRDStationDealStage, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    rdstationcrm_client = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
    if not rdstationcrm_client:
        raise HTTPException(status_code=404, detail="Cliente do RD Station CRM não encontrado para essa empresa")

    deal_stage = db.query(RDStationCRMDealStage).filter_by(id=request.id, id_rdstationcrm_client=rdstationcrm_client.id).first()
    if not deal_stage:
        raise HTTPException(status_code=404, detail="Estágio não encontrado para esse cliente do RD Station CRM")

    deal_stage.atalho = request.atalho
    deal_stage.deal_stage_id = request.deal_stage_id
    deal_stage.user_id = request.user_id
    deal_stage.deal_stage_inicial = request.estagio_inicial
    db.commit()
    return deal_stage

@router.put("/{slug}/informacoes_financeiras", response_model=EmpresaSchema)
async def alterar_informacoes_financeiras(slug: str, request: InformacoesFinanceiras, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresa.financial_client_type = request.tipo_cliente
    empresa.lembrar_vencimentos_ativo = request.lembrar_vencimentos
    empresa.cobrar_inadimplentes_ativo = request.cobrar_inadimplentes
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_financeiras/asaas", response_model=AsaasClientSchema)
async def alterar_informacoes_asaas(slug: str, request: InformacoesAsaas, db: Session = Depends(obter_sessao)):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    asaas_client = db.query(AsaasClient).filter_by(id_empresa=empresa.id).first()
    if not asaas_client:
        raise HTTPException(status_code=404, detail="Cliente do Asaas não encontrado para essa empresa")

    asaas_client.token = request.token
    asaas_client.rotulo = request.rotulo
    asaas_client.client_number = request.numero_cliente
    db.commit()
    return asaas_client
