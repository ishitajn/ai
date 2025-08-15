import logging
import spacy
from typing import List

from analysis_models import DateAnalysis, DateLogistics, MessageAnalysis
from utils.constants import PLANNING_WORDS, DATE_KEYWORDS, COMMITMENT_LEVELS

logger = logging.getLogger(__name__)

def get_date_analysis(analyzed_messages: List[MessageAnalysis], nlp: spacy.language.Language) -> DateAnalysis:
    logger.debug("Getting date analysis.")
    date_analysis = DateAnalysis()
    for msg in reversed(analyzed_messages):
        text_lower = msg.content.lower()
        if any(word in text_lower for word in PLANNING_WORDS):
            date_analysis.isDatePlanned = True
            for keyword, date_type in DATE_KEYWORDS.items():
                if keyword in text_lower:
                    date_analysis.dateType = date_type
                    if date_type == "virtual":
                        date_analysis.isVirtual = True
                    break
            for level, phrases in COMMITMENT_LEVELS.items():
                if any(phrase in text_lower for phrase in phrases):
                    date_analysis.dateCommitmentLevel = level
                    break
            doc = nlp(msg.content)
            for ent in doc.ents:
                if ent.label_ in ("TIME", "DATE"):
                    date_analysis.dateLogistics.time = ent.text
                if ent.label_ in ("ORG", "FAC"):
                    date_analysis.dateLogistics.venue = ent.text
            if date_analysis.dateCommitmentLevel != "none":
                break
    logger.debug(f"Date analysis result: {date_analysis.model_dump_json(indent=2)}")
    return date_analysis
