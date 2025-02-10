import secrets
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.db.database import obter_sessao
from app.db.models import Empresa, Assistente, DigisacClient, EvolutionAPIClient, Departamento, OutlookClient, \
    GoogleCalendarClient, RDStationCRMClient, RDStationCRMDealStage, AsaasClient, Agenda, Usuario, Voz, Colaborador, \
    Midia
from app.routers.usuario import obter_usuario_logado
from app.schemas.atualizacao_empresa_schema import InformacoesBasicas, InformacoesMensagens, InformacoesDigisac, \
    InformacoesEvolutionAPI, InformacoesDepartamento, InformacoesAgenda, InformacoesOutlook, InformacoesGoogleCalendar, \
    InformacoesAssistentes, InformacoesCRM, InformacoesRDStationCRMClient, InformacoesRDStationDealStage, \
    InformacoesFinanceiras, InformacoesAsaas, InformacoesAssistente, InformacoesAgendaUnica, InformacoesVoz, \
    InformacoesCriarEmpresa, InformacoesColaborador, InformacoesMidia
from app.schemas.empresa_schema import EmpresaSchema, AgendaSchema, DepartamentoSchema, AssistenteSchema, \
    DigisacClientSchema, EvolutionAPIClientSchema, OutlookClientSchema, GoogleCalendarClientSchema, \
    RDStationCRMClientSchema, RDStationCRMDealStageSchema, AsaasClientSchema, VozSchema, EmpresaMinSchema, \
    ColaboradorSchema, MidiaSchema


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

@router.post("/")
async def criar_empresa(
        request: InformacoesCriarEmpresa,
        usuario: Usuario = Depends(obter_usuario_logado),
        db: Session = Depends(obter_sessao)
):
    if not usuario.id_empresa:
        empresa = db.query(Empresa).filter_by(slug=request.slug).first()
        if not empresa:
            token = secrets.token_hex(32)
            empresa = Empresa(
                nome=request.nome,
                slug=request.slug,
                token=token,
                fuso_horario=request.fuso_horario,
                openai_api_key=request.openai_api_key
            )
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
            return empresa
    return None

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

@router.post("/{slug}/informacoes_basicas/colaborador")
async def adicionar_colaborador(
        slug: str,
        request: InformacoesColaborador,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    colaborador = Colaborador(
        nome=request.nome,
        apelido=request.apelido,
        departamento=request.departamento,
        id_empresa=empresa.id
    )

    db.add(colaborador)
    db.commit()
    db.refresh(colaborador)
    return colaborador

@router.put("/{slug}/informacoes_basicas/colaborador", response_model=ColaboradorSchema)
async def alterar_colaborador(
        slug: str,
        request: InformacoesColaborador,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    colaborador = db.query(Colaborador).filter_by(id=request.id, id_empresa=empresa.id).first()
    if not colaborador:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado para essa empresa")

    colaborador.nome = request.nome
    colaborador.apelido = request.apelido
    colaborador.departamento = request.departamento
    db.commit()
    return colaborador

@router.delete("/{slug}/informacoes_basicas/colaborador/{id}")
async def remover_colaborador(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    colaborador = db.query(Colaborador).filter_by(id=id, id_empresa=empresa.id).first()
    if colaborador:
        db.delete(colaborador)
        db.commit()
        return True
    return False

@router.post("/{slug}/informacoes_basicas/midia")
async def adicionar_midia(
        slug: str,
        request: InformacoesMidia,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    midia = Midia(
        url=request.url,
        tipo=request.tipo,
        mediatype=request.mediatype,
        nome=request.nome,
        atalho=request.atalho,
        ordem=request.ordem,
        id_empresa=empresa.id
    )

    db.add(midia)
    db.commit()
    db.refresh(midia)
    return midia

@router.put("/{slug}/informacoes_basicas/midia", response_model=MidiaSchema)
async def alterar_midia(
        slug: str,
        request: InformacoesMidia,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    midia = db.query(Midia).filter_by(id=request.id, id_empresa=empresa.id).first()
    if not midia:
        raise HTTPException(status_code=404, detail="Mídia não encontrada para essa empresa")

    midia.url = request.url
    midia.tipo = request.tipo
    midia.mediatype = request.mediatype
    midia.nome = request.nome
    midia.atalho = request.atalho
    midia.ordem= request.ordem

    db.commit()
    return midia

@router.delete("/{slug}/informacoes_basicas/midia/{id}")
async def remover_midia(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    midia = db.query(Midia).filter_by(id=id, id_empresa=empresa.id).first()
    if midia:
        db.delete(midia)
        db.commit()
        return True
    return False

@router.put("/{slug}/informacoes_assistentes", response_model=EmpresaSchema)
async def alterar_informacoes_assistentes(
        slug: str,
        request: InformacoesAssistentes,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    if request.assistente_padrao:
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

@router.delete("/{slug}/informacoes_assistentes/assistente/{id}")
async def remover_assistente(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    if empresa.assistentePadrao == id:
        raise HTTPException(status_code=403, detail="Não é possível excluir o assistente padrão da empresa. Troque o assistente padrão e tente novamente")

    assistente = db.query(Assistente).filter_by(id=id, id_empresa=empresa.id).first()
    if assistente:
        db.delete(assistente)
        db.commit()
        return True
    return False

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

@router.delete("/{slug}/informacoes_assistentes/voz/{id}")
async def remover_voz(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    voz = db.query(Voz).filter_by(id=id, id_empresa=empresa.id).first()
    if voz:
        db.delete(voz)
        db.commit()
        return True
    return False

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

@router.post("/{slug}/informacoes_mensagens/digisac")
async def adicionar_cliente_digisac(
        slug: str,
        request: InformacoesDigisac,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    digisac_client = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
    if digisac_client:
        raise HTTPException(status_code=404, detail="Essa empresa já possui um cliente do Digisac")

    digisac_client = DigisacClient(
        digisacSlug=request.slug,
        service_id=request.service_id,
        digisacToken=request.token,
        digisacDefaultUser=request.user_id,
        id_empresa=empresa.id
    )

    db.add(digisac_client)
    db.commit()
    db.refresh(digisac_client)
    return digisac_client

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

@router.delete("/{slug}/informacoes_mensagens/digisac/departamento/{id}")
async def remover_departamento(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    digisac_client = db.query(DigisacClient).filter_by(id_empresa=empresa.id).first()
    if not digisac_client:
        raise HTTPException(status_code=404, detail="Cliente do Digisac não encontrado para essa empresa")

    departamento = db.query(Departamento).filter_by(id=id, id_digisac_client=digisac_client.id).first()
    if departamento:
        db.delete(departamento)
        db.commit()
        return True
    return False

@router.post("/{slug}/informacoes_mensagens/evolutionapi")
async def adicionar_cliente_evolutionapi(
        slug: str,
        request: InformacoesEvolutionAPI,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    evolutionapi_client = db.query(EvolutionAPIClient).filter_by(id_empresa=empresa.id).first()
    if evolutionapi_client:
        raise HTTPException(status_code=404, detail="Essa empresa já possui um cliente do EvolutionAPI")

    evolutionapi_client = EvolutionAPIClient(
        apiKey=request.api_key,
        instanceName=request.instance_name,
        id_empresa=empresa.id
    )

    db.add(evolutionapi_client)
    db.commit()
    db.refresh(evolutionapi_client)
    return evolutionapi_client

@router.put("/{slug}/informacoes_mensagens/evolutionapi", response_model=EvolutionAPIClientSchema)
async def alterar_informacoes_evolutionapi(
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

@router.delete("/{slug}/informacoes_agenda/agenda/{id}")
async def remover_agenda(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    agenda = db.query(Agenda).filter_by(id=id, id_empresa=empresa.id).first()
    if agenda:
        db.delete(agenda)
        db.commit()
        return True
    return False

@router.post("/{slug}/informacoes_agenda/outlook")
async def adicionar_cliente_outlook(
        slug: str,
        request: InformacoesOutlook,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    outlook_client = db.query(OutlookClient).filter_by(id_empresa=empresa.id).first()
    if outlook_client:
        raise HTTPException(status_code=404, detail="Essa empresa já possui um cliente do Outlook")

    outlook_client = OutlookClient(
        clientId=request.client_id,
        tenantId=request.tenant_id,
        clientSecret=request.client_secret,
        duracaoEvento=request.duracao_evento,
        usuarioPadrao=request.usuario_padrao,
        horaInicioAgenda=request.hora_inicial,
        horaFinalAgenda=request.hora_final,
        timeZone=request.fuso_horario,
        id_empresa=empresa.id
    )

    db.add(outlook_client)
    db.commit()
    db.refresh(outlook_client)
    return outlook_client

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

@router.post("/{slug}/informacoes_agenda/googlecalendar")
async def alterar_informacoes_googlecalendar(
        slug: str,
        request: InformacoesGoogleCalendar,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    googlecalendar_client = db.query(GoogleCalendarClient).filter_by(id_empresa=empresa.id).first()
    if googlecalendar_client:
        raise HTTPException(status_code=404, detail="Essa empresa já possui um cliente do Google Calendar")

    googlecalendar_client = GoogleCalendarClient(
        project_id=request.project_id,
        private_key_id=request.private_key_id,
        private_key=request.private_key,
        client_email=request.client_email,
        client_id=request.client_id,
        client_x509_cert_url=request.client_x509_cert_url,
        api_key=request.api_key,
        duracao_evento=request.duracao_evento,
        hora_inicio_agenda=request.hora_inicial,
        hora_final_agenda=request.hora_final,
        timezone=request.fuso_horario,
        id_empresa=empresa.id
    )

    db.add(googlecalendar_client)
    db.commit()
    db.refresh(googlecalendar_client)
    return googlecalendar_client

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

@router.post("/{slug}/informacoes_crm/rdstation")
async def adicionar_cliente_rdstation(
        slug: str,
        request: InformacoesRDStationCRMClient,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    rdstationcrm_client = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
    if rdstationcrm_client:
        raise HTTPException(status_code=404, detail="Essa empresa já possui um cliente do RD Station CRM")

    rdstationcrm_client = RDStationCRMClient(
        token=request.token,
        id_fonte_padrao=request.id_fonte_padrao,
        id_empresa=empresa.id
    )

    db.add(rdstationcrm_client)
    db.commit()
    db.refresh(rdstationcrm_client)
    return rdstationcrm_client

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

    estagio = db.query(RDStationCRMDealStage).filter_by(id=request.id, id_rdstationcrm_client=rdstationcrm_client.id).first()
    if not estagio:
        raise HTTPException(status_code=404, detail="Estágio não encontrado para esse cliente do RD Station CRM")

    estagio.atalho = request.atalho
    estagio.deal_stage_id = request.deal_stage_id
    estagio.user_id = request.user_id
    estagio.deal_stage_inicial = request.estagio_inicial
    db.commit()
    return estagio

@router.delete("/{slug}/informacoes_crm/rdstation/estagio/{id}")
async def remover_estagio(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    rdstationcrm_client = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
    if not rdstationcrm_client:
        raise HTTPException(status_code=404, detail="Cliente do RD Station CRM não encontrado para essa empresa")

    estagio = db.query(RDStationCRMDealStage).filter_by(id=id, id_rdstationcrm_client=rdstationcrm_client.id).first()
    if estagio:
        db.delete(estagio)
        db.commit()
        return True
    return False

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

@router.post("/{slug}/informacoes_financeiras/asaas")
async def adicionar_cliente_asaas(
        slug: str,
        request: InformacoesAsaas,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    asaas_client = db.query(AsaasClient).filter_by(id_empresa=empresa.id, client_number=request.numero_cliente).first()
    if asaas_client:
        raise HTTPException(status_code=409, detail="Essa empresa já possui um cliente do Asaas com esse número de cliente")

    asaas_client = AsaasClient(
        token=request.token,
        rotulo=request.rotulo,
        client_number=request.numero_cliente,
        id_empresa=empresa.id
    )

    db.add(asaas_client)
    db.commit()
    db.refresh(asaas_client)
    return asaas_client

@router.put("/{slug}/informacoes_financeiras/asaas", response_model=AsaasClientSchema)
async def alterar_informacoes_cliente_asaas(
        slug: str,
        request: InformacoesAsaas,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    asaas_client = db.query(AsaasClient).filter_by(id_empresa=empresa.id, client_number=request.numero_cliente).first()
    if not asaas_client:
        raise HTTPException(status_code=404, detail="Cliente do Asaas não encontrado para essa empresa")

    asaas_client.token = request.token
    asaas_client.rotulo = request.rotulo
    db.commit()
    return asaas_client

@router.delete("/{slug}/informacoes_financeiras/asaas/{id}")
async def remover_cliente_asaas(
        slug: str,
        id: int,
        empresa: Empresa = Depends(verificar_permissao_empresa),
        db: Session = Depends(obter_sessao)
):
    asaas_client = db.query(AsaasClient).filter_by(id=id, id_empresa=empresa.id).first()
    if asaas_client:
        db.delete(asaas_client)
        db.commit()
        return True
    return False
