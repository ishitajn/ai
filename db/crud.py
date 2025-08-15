import logging
from typing import Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from . import models
from analysis_models import FullConversationAnalysis

logger = logging.getLogger(__name__)

def get_match_analysis(db: Session, match_id: str) -> Optional[FullConversationAnalysis]:
    try:
        db_obj = db.query(models.MatchMemoryDB).filter(models.MatchMemoryDB.match_id == match_id).first()
        if db_obj:
            return FullConversationAnalysis.model_validate(db_obj.memory_data)
        return None
    except ValidationError as e:
        logger.error(f"Pydantic validation error for match_id {match_id}: {e}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Database error while getting analysis for match_id {match_id}: {e}")
        db.rollback()
        return None

def save_match_analysis(db: Session, match_id: str, analysis: FullConversationAnalysis):
    try:
        db_obj = db.query(models.MatchMemoryDB).filter(models.MatchMemoryDB.match_id == match_id).first()
        analysis_dict = analysis.model_dump()
        if db_obj:
            db_obj.memory_data = analysis_dict
        else:
            db_obj = models.MatchMemoryDB(match_id=match_id, memory_data=analysis_dict)
            db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except SQLAlchemyError as e:
        logger.error(f"Database error while saving analysis for match_id {match_id}: {e}")
        db.rollback()
        return None