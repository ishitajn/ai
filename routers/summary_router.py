import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api_models import AnalysisRequest, SummarizedAnalysis
from db.database import get_db
from services import analysis_service, summarization_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analysis/summary", response_model=SummarizedAnalysis, tags=["Analysis"])
async def get_analysis_summary(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Performs a full conversation analysis and then transforms it into a
    concise, semantically-enhanced summary.
    """
    logger.info(f"Received summary analysis request for match: {request.matchId}")

    # Step 1: Perform the full, detailed analysis
    full_analysis = analysis_service.run_full_conversation_analysis(
        db=db,
        match_id=request.matchId,
        scraped_data=request.scraped_data,
        ui_settings=request.ui_settings
    )

    # Step 2: Summarize the detailed analysis
    history_as_dicts = [msg.model_dump() for msg in request.scraped_data.conversationHistory]
    summary = summarization_service.summarize_analysis(
        full_analysis=full_analysis,
        history=history_as_dicts,
        analysis_engine=request.ui_settings.analysis_engine,
        use_enhanced_nlp=request.ui_settings.useEnhancedNlp
    )

    return summary
