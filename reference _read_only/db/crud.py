from typing import Optional

from sqlalchemy.orm import Session
from . import models
from analysis_models import MatchMemory, FullConversationAnalysis

def get_match_analysis(db: Session, match_id: str) -> Optional[FullConversationAnalysis]:
    db_obj = db.query(models.MatchMemoryDB).filter(models.MatchMemoryDB.match_id == match_id).first()
    if db_obj:
        return FullConversationAnalysis.model_validate(db_obj.memory_data)
    return None

def save_match_analysis(db: Session, match_id: str, analysis: FullConversationAnalysis):
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