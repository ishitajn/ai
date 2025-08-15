import logging
import spacy
from typing import List

from analysis_models import DateAnalysis, MessageAnalysis
from constants import PLANNING_WORDS, DATE_KEYWORDS, COMMITMENT_LEVELS

logger = logging.getLogger(__name__)

def get_date_analysis(analyzed_messages: List[MessageAnalysis], nlp: spacy.language.Language) -> DateAnalysis:
    logger.debug("Getting date analysis.")
    date_analysis = DateAnalysis()
    commitment_map = {"confirmed": 2, "provisional": 1, "low": 0, "none": -1}

    for msg in reversed(analyzed_messages):
        text_lower = msg.content.lower()
        if any(word in text_lower for word in PLANNING_WORDS):
            date_analysis.isDatePlanned = True

            # Find the best date type, don't break early
            for keyword, date_type in DATE_KEYWORDS.items():
                if keyword in text_lower:
                    date_analysis.dateType = date_type
                    if date_type == "virtual":
                        date_analysis.isVirtual = True

            # Find the highest commitment level in the message
            best_commitment_level = "none"
            for level, phrases in COMMITMENT_LEVELS.items():
                if any(phrase in text_lower for phrase in phrases):
                    if commitment_map.get(level, -1) > commitment_map.get(best_commitment_level, -1):
                        best_commitment_level = level
            date_analysis.dateCommitmentLevel = best_commitment_level

            doc = nlp(msg.content)
            for ent in doc.ents:
                if ent.label_ in ("TIME", "DATE") and not date_analysis.dateLogistics.time:
                    date_analysis.dateLogistics.time = ent.text
                if ent.label_ in ("ORG", "FAC") and not date_analysis.dateLogistics.venue:
                    date_analysis.dateLogistics.venue = ent.text

            # If we found any kind of planning in the most recent planning message, we can stop.
            if date_analysis.dateCommitmentLevel != "none" or date_analysis.dateType != "none":
                break

    logger.debug(f"Date analysis result: {date_analysis.model_dump_json(indent=2)}")
    return date_analysis
