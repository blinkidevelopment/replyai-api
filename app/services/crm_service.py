from sqlalchemy.orm import Session

from app.db.models import Empresa, RDStationCRMClient, RDStationCRMDealStage, Contato
from app.utils.crm_client import CRMClient
from app.utils.rdstation_crm import RDStationCRM


def criar_crm_client(empresa: Empresa, db: Session):
    if empresa.crm_client_type == "rdstation":
        rdstationcrm_client_db = db.query(RDStationCRMClient).filter_by(id_empresa=empresa.id).first()
        if rdstationcrm_client_db:
            deal_stage_inicial = db.query(RDStationCRMDealStage).filter_by(deal_stage_inicial=True, id_rdstationcrm_client=rdstationcrm_client_db.id).first()
            if deal_stage_inicial:
                return RDStationCRM(
                    token=rdstationcrm_client_db.token,
                    user_id=deal_stage_inicial.user_id,
                    deal_stage_id=deal_stage_inicial.deal_stage_id,
                    deal_source_id=rdstationcrm_client_db.id_fonte_padrao
                )
    return None


async def mover_lead(crm_client: CRMClient, contato: Contato, empresa: Empresa, atalho: str, db: Session):
    if crm_client and contato.deal_id:
        deal_stage_db = (
            db.query(RDStationCRMDealStage)
            .join(RDStationCRMClient, RDStationCRMDealStage.id_rdstationcrm_client == RDStationCRMClient.id)
            .filter(
                RDStationCRMDealStage.atalho == atalho,
                RDStationCRMClient.id_empresa == empresa.id
            )
            .first()
        )

        if deal_stage_db:
            return crm_client.mudar_etapa(deal_id=contato.deal_id,
                                          deal_stage_id=deal_stage_db.deal_stage_id,
                                          user_id=deal_stage_db.user_id)