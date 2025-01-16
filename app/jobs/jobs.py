from datetime import datetime, timedelta
from sqlalchemy import or_, and_

from app.db.database import retornar_sessao
from app.db.models import Empresa, Contato
from app.jobs.sub_jobs import enviar_retomada_conversa, enviar_confirmacao_consulta


async def retomar_conversa():
    agora = datetime.now()

    with retornar_sessao() as db:
        try:
            empresas = db.query(Empresa).filter_by(recall_ativo=True).all()

            for empresa in empresas:
                timeout_padrao = empresa.recall_timeout_minutes or 60
                timeout_padrao_time = agora - timedelta(minutes=timeout_padrao)

                timeout_final = empresa.final_recall_timeout_minutes or 1440
                timeout_final_time = agora - timedelta(minutes=timeout_final)

                interacoes_inativas = db.query(Contato).filter(
                    Contato.id_empresa == empresa.id,
                    or_(
                        and_(
                            Contato.lastMessage <= timeout_padrao_time,
                            Contato.recallCount < empresa.recall_quant - 1,
                            Contato.receber_respostas_ia == True
                        ),
                        and_(
                            Contato.lastMessage <= timeout_final_time,
                            Contato.recallCount == empresa.recall_quant - 1,
                            Contato.receber_respostas_ia == True
                        )
                    )
                ).all()

                for contato in interacoes_inativas:
                    await enviar_retomada_conversa(contato, empresa, db)
        except Exception as e:
            print(f"Erro ao processar: {e}")


async def confirmar_agendamento():
    data_atual = datetime.now()
    dia_seguinte = data_atual + timedelta(days=1)

    with retornar_sessao() as db:
        try:
            empresas = db.query(Empresa).filter_by(confirmar_agendamentos_ativo=True).all()

            for empresa in empresas:
                await enviar_confirmacao_consulta(dia_seguinte.strftime("%Y-%m-%d"), data_atual.strftime("%Y-%m-%dT%H:%M:%S"), empresa, db)
        except Exception as e:
            print(f"Erro ao processar: {e}")
