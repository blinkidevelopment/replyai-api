from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.db.database import obter_sessao
from app.db.models import Empresa, Assistente, DigisacClient, EvolutionAPIClient, Departamento, OutlookClient, \
    GoogleCalendarClient, RDStationCRMClient, RDStationCRMDealStage, AsaasClient, Agenda, Usuario, Voz
from app.routers.usuario import obter_usuario_logado
from app.schemas.atualizacao_empresa_schema import InformacoesBasicas, InformacoesMensagens, InformacoesDigisac, \
    InformacoesEvolutionAPI, InformacoesDepartamento, InformacoesAgenda, InformacoesOutlook, InformacoesGoogleCalendar, \
    InformacoesAssistentes, InformacoesCRM, InformacoesRDStationCRMClient, InformacoesRDStationDealStage, \
    InformacoesFinanceiras, InformacoesAsaas, InformacoesAssistente, InformacoesAgendaUnica, InformacoesVoz
from app.schemas.empresa_schema import EmpresaSchema, AgendaSchema, DepartamentoSchema, AssistenteSchema, \
    DigisacClientSchema, EvolutionAPIClientSchema, OutlookClientSchema, GoogleCalendarClientSchema, \
    RDStationCRMClientSchema, RDStationCRMDealStageSchema, AsaasClientSchema, VozSchema, EmpresaMinSchema


async def verificar_permissao_empresa(
    slug: str,
    db: Session = Depends(obter_sessao),
    usuario: Usuario = Depends(obter_usuario_logado)
):
    empresa = db.query(Empresa).filter_by(slug=slug).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    if usuario.id_empresa is not None and usuario.id_empresa != empresa.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para acessar esta empresa")

    return empresa


# TODO: implementar services
router = APIRouter(dependencies=[Depends(obter_usuario_logado)])

@router.get("/", response_model=List[EmpresaMinSchema])
async def obter_todas_empresas(usuario: Usuario = Depends(obter_usuario_logado), db: Session = Depends(obter_sessao)):
    if not usuario.id_empresa:
        empresas = db.query(Empresa).all()
    else:
        empresas = db.query(Empresa).filter_by(id=usuario.id_empresa).all()
    return empresas

@router.get("/{slug}", response_model=EmpresaSchema)
async def obter_empresa(
        slug: str,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    return empresa

@router.put("/{slug}/informacoes_basicas", response_model=EmpresaSchema)
async def alterar_informacoes_basicas(
        slug: str,
        request: InformacoesBasicas,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    empresa.nome = request.nome
    empresa.fuso_horario = request.fuso_horario
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_assistentes", response_model=EmpresaSchema)
async def alterar_informacoes_assistentes(
        slug: str,
        request: InformacoesAssistentes,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    assistente = db.query(Assistente).filter_by(id=request.assistente_padrao, id_empresa=empresa.id, proposito="responder").first()
    if not assistente:
        raise HTTPException(status_code=404, detail="Assistente não encontrado para essa empresa")

    empresa.assistentePadrao = request.assistente_padrao
    db.commit()
    return empresa

@router.post("/{slug}/informacoes_assistentes/assistente")
async def adicionar_assistente(
        slug: str,
        request: InformacoesAssistente,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_assistente(
        slug: str,
        request: InformacoesAssistente,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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

@router.post("/{slug}/informacoes_assistentes/voz")
async def adicionar_voz(
        slug: str,
        request: InformacoesVoz,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    voz = Voz(
        voiceId=request.voice_id,
        stability=request.stability,
        similarity_boost=request.similarity_boost,
        style=request.style,
        id_empresa=empresa.id
    )

    db.add(voz)
    db.commit()
    db.refresh(voz)
    return voz

@router.put("/{slug}/informacoes_assistentes/voz", response_model=VozSchema)
async def alterar_voz(
        slug: str,
        request: InformacoesVoz,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    voz = db.query(Voz).filter_by(id=request.id, id_empresa=empresa.id).first()
    if not voz:
        raise HTTPException(status_code=404, detail="Voz não encontrada para essa empresa")

    voz.voiceId = request.voice_id
    voz.stability = request.stability
    voz.similarity_boost = request.similarity_boost
    voz.style = request.style
    db.commit()
    return voz

@router.put("/{slug}/informacoes_mensagens", response_model=EmpresaSchema)
async def alterar_informacoes_mensagens(
        slug: str,
        request: InformacoesMensagens,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    empresa.message_client_type = request.tipo_cliente
    empresa.recall_timeout_minutes = request.tempo_recall_min
    empresa.final_recall_timeout_minutes = request.tempo_recall_final_min
    empresa.recall_quant = request.quant_recalls
    empresa.recall_ativo = request.ativar_recall
    empresa.mensagem_erro_ia = request.mensagem_erro_ia
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_mensagens/digisac", response_model=DigisacClientSchema)
async def alterar_informacoes_digisac(
        slug: str,
        request: InformacoesDigisac,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def adicionar_departamento(
        slug: str,
        request: InformacoesDepartamento,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_departamento(
        slug: str,
        request: InformacoesDepartamento,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_digisac(
        slug: str,
        request: InformacoesEvolutionAPI,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    evolutionapi_client = db.query(EvolutionAPIClient).filter_by(id_empresa=empresa.id).first()
    if not evolutionapi_client:
        raise HTTPException(status_code=404, detail="Cliente do EvolutionAPI não encontrado para essa empresa")

    evolutionapi_client.apiKey = request.api_key
    evolutionapi_client.instanceName = request.instance_name
    db.commit()
    return evolutionapi_client

@router.put("/{slug}/informacoes_agenda", response_model=EmpresaSchema)
async def alterar_informacoes_agenda(
        slug: str,
        request: InformacoesAgenda,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    empresa.agenda_client_type = request.tipo_cliente
    empresa.tipo_cancelamento_evento = request.tipo_cancelamento_evento
    empresa.confirmar_agendamentos_ativo = request.ativar_confirmacao
    db.commit()
    return empresa

@router.post("/{slug}/informacoes_agenda/agenda")
async def adicionar_agenda(
        slug: str,
        request: InformacoesAgendaUnica,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_agenda(
        slug: str,
        request: InformacoesAgendaUnica,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    agenda = db.query(Agenda).filter_by(id=request.id, id_empresa=empresa.id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda não encontrada para essa empresa")

    agenda.endereco = request.endereco
    agenda.atalho = request.atalho
    db.commit()
    return agenda

@router.put("/{slug}/informacoes_agenda/outlook", response_model=OutlookClientSchema)
async def alterar_informacoes_outlook(
        slug: str,
        request: InformacoesOutlook,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_googlecalendar(
        slug: str,
        request: InformacoesGoogleCalendar,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_crm(
        slug: str,
        request: InformacoesCRM,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    empresa.crm_client_type = request.tipo_cliente
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_crm/rdstation", response_model=RDStationCRMClientSchema)
async def alterar_informacoes_rdstation(
        slug: str,
        request: InformacoesRDStationCRMClient,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    rdstationcrm_client = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
    if not rdstationcrm_client:
        raise HTTPException(status_code=404, detail="Cliente do RD Station CRM não encontrado para essa empresa")

    rdstationcrm_client.token = request.token
    rdstationcrm_client.id_fonte_padrao = request.id_fonte_padrao
    db.commit()
    return rdstationcrm_client

@router.post("/{slug}/informacoes_crm/rdstation/estagio")
async def adicionar_estagio(
        slug: str,
        request: InformacoesRDStationDealStage,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_estagio(
        slug: str,
        request: InformacoesRDStationDealStage,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
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
async def alterar_informacoes_financeiras(
        slug: str,
        request: InformacoesFinanceiras,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    empresa.financial_client_type = request.tipo_cliente
    empresa.lembrar_vencimentos_ativo = request.lembrar_vencimentos
    empresa.cobrar_inadimplentes_ativo = request.cobrar_inadimplentes
    db.commit()
    return empresa

@router.put("/{slug}/informacoes_financeiras/asaas", response_model=AsaasClientSchema)
async def alterar_informacoes_asaas(
        slug: str,
        request: InformacoesAsaas,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    asaas_client = db.query(AsaasClient).filter_by(id_empresa=empresa.id).first()
    if not asaas_client:
        raise HTTPException(status_code=404, detail="Cliente do Asaas não encontrado para essa empresa")

    asaas_client.token = request.token
    asaas_client.rotulo = request.rotulo
    asaas_client.client_number = request.numero_cliente
    db.commit()
    return asaas_client
