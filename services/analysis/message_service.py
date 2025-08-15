import logging
import spacy

from analysis_models import MessageAnalysis, SubtextAnalysis, QuestionInfo
from constants import (
    POSITIVE_WORDS, NEGATIVE_WORDS, AROUSAL_WORDS, VULNERABLE_WORDS,
    SEXUAL_WORDS, SEXUAL_EMOJIS, LOW_EFFORT_WORDS, GEO_TRIGGERS,
    AMBIGUOUS_PHRASES, SARCASTIC_MARKERS, INTENSIFIERS, NEGATION_WORDS,
    INDIRECT_QUESTION_STARTERS
)

logger = logging.getLogger(__name__)


def analyze_single_message(
        text: str,
        role: str,
        use_enhanced_nlp: bool,
        nlp: spacy.language.Language,
        vader_analyzer
) -> MessageAnalysis:
    logger.debug(f"Analyzing single message. Role: {role}, Enhanced NLP: {use_enhanced_nlp}, Content: '{text}'")
    if not text:
        return MessageAnalysis(content="", role=role, subtext=SubtextAnalysis(), questionInfo=QuestionInfo())

    doc = nlp(text)
    subtext = _analyze_subtext_enhanced(doc, vader_analyzer) if use_enhanced_nlp else _analyze_subtext_legacy(doc)

    analysis_obj = MessageAnalysis(
        content=text,
        role=role,
        subtext=subtext,
        questionInfo=_analyze_question(doc),
        isLowEffort=_is_low_effort(text, doc),
        isGeoRelated=_detect_geo_related(doc),
        wordCount=len([token for token in doc if token.is_alpha])
    )
    analysis_obj.suggestedResponseStyle = _suggest_response_style(analysis_obj)
    logger.debug(f"Single message analysis result: {analysis_obj.model_dump_json(indent=2)}")
    return analysis_obj

def _analyze_subtext_legacy(doc: spacy.tokens.Doc) -> SubtextAnalysis:
    logger.debug(f"Analyzing subtext (legacy) for: '{doc.text}'")
    text_lower = doc.text.lower()
    subtext = SubtextAnalysis(intents=[])
    valence, arousal = 0.0, 0.0
    for token in doc:
        token_text, multiplier = token.text.lower(), 1.0
        if token.i > 0 and doc[token.i - 1].text.lower() in INTENSIFIERS:
            multiplier *= INTENSIFIERS.get(doc[token.i - 1].text.lower(), 1.0)
        if any(c.dep_ == 'neg' for c in token.children) or (token.i > 0 and doc[token.i - 1].text.lower() in NEGATION_WORDS):
            multiplier *= -1
        if token_text in POSITIVE_WORDS:
            valence += POSITIVE_WORDS[token_text] * multiplier
        if token_text in NEGATIVE_WORDS:
            valence += NEGATIVE_WORDS[token_text] * multiplier
        if token_text in AROUSAL_WORDS:
            arousal += AROUSAL_WORDS[token_text]
    if any(w in text_lower for w in ["planning"]):
        subtext.intents.append("planning")
    if any(w in text_lower for w in SEXUAL_WORDS) or SEXUAL_EMOJIS.search(text_lower):
        subtext.intents.append("flirting_or_sexual")
    if any(p in text_lower for p in VULNERABLE_WORDS):
        subtext.isVulnerable = True
    if any(m in text_lower for m in SARCASTIC_MARKERS) and valence > 0:
        subtext.isSarcastic = True
    subtext.valence = max(-1, min(1, valence))
    subtext.arousal = max(-1, min(1, arousal))
    subtext.isAmbiguous = any(phrase in text_lower for phrase in AMBIGUOUS_PHRASES)
    subtext.intents = list(set(subtext.intents))
    logger.debug(f"Subtext (legacy) result: {subtext.model_dump_json(indent=2)}")
    return subtext

def _analyze_subtext_enhanced(doc: spacy.tokens.Doc, vader_analyzer) -> SubtextAnalysis:
    logger.debug(f"Analyzing subtext (enhanced) for: '{doc.text}'")
    subtext = _analyze_subtext_legacy(doc)
    vader_scores = vader_analyzer.polarity_scores(doc.text)
    logger.debug(f"Vader scores: {vader_scores}")
    subtext.valence = vader_scores['compound']
    subtext.arousal = 0.0
    logger.debug(f"Subtext (enhanced) result: {subtext.model_dump_json(indent=2)}")
    return subtext

def _analyze_question(doc: spacy.tokens.Doc) -> QuestionInfo:
    """
    Analyzes a spaCy Doc to find and classify questions, including informal/conversational ones.
    """
    logger.debug(f"Analyzing question for: '{doc.text}'")
    question_count = 0
    question_types = set()

    question_words = {"who", "what", "where", "when", "why", "how", "which"}
    aux_verbs = {"be", "do", "have", "can", "could", "may", "might", "must", "shall", "should", "will", "would"}

    for sent in doc.sents:
        sent_text_lower = sent.text.lower().strip()
        is_a_question = False
        sent_type = None

        # Rule 1: Ends with a question mark (strongest signal)
        if sent_text_lower.endswith('?'):
            is_a_question = True
        # Rule 2: Starts with an indirect question starter
        elif any(sent_text_lower.startswith(s) for s in INDIRECT_QUESTION_STARTERS):
            is_a_question = True
            sent_type = "indirect"
        # Rule 3: Starts with a question word (e.g., "what time", "so why are you here")
        elif sent[0].lemma_.lower() in question_words or \
             (len(sent) > 1 and sent[0].pos_ == 'ADV' and sent[1].lemma_.lower() in question_words):
            is_a_question = True
            sent_type = "open"
        # Rule 4: Starts with an auxiliary verb, indicating inversion (e.g., "are you coming")
        elif sent[0].lemma_.lower() in aux_verbs and len(sent) > 1 and any(t.dep_ == 'nsubj' for t in sent):
            is_a_question = True
            sent_type = "closed"
        # Rule 5: Handle verbless fragments (e.g., "you good?")
        elif len(sent) <= 4 and sent[0].pos_ == 'PRON' and sent.root.pos_ == 'ADJ':
            is_a_question = True
            sent_type = "closed"

        if is_a_question:
            question_count += 1
            # If type not set by a specific rule, determine it now
            if not sent_type:
                if any(token.lemma_.lower() in question_words for token in sent):
                    sent_type = "open"
                else:
                    sent_type = "closed"
            question_types.add(sent_type)

    if not question_types:
        return QuestionInfo()

    # Prioritize question type: open > indirect > closed
    final_type = "none"
    if "open" in question_types:
        final_type = "open"
    elif "indirect" in question_types:
        final_type = "indirect"
    elif "closed" in question_types:
        final_type = "closed"

    result = QuestionInfo(
        isQuestion=True,
        count=question_count,
        type=final_type
    )
    logger.debug(f"Question analysis result: {result.model_dump_json()}")
    return result

def _is_low_effort(text: str, doc: spacy.tokens.Doc) -> bool:
    logger.debug(f"Checking for low effort: '{text}'")
    text_clean = text.strip().lower()
    if len(doc) < 4 and text_clean in LOW_EFFORT_WORDS:
        logger.debug("Low effort detected (short message in low effort list).")
        return True
    result = all(w.strip(".,!?-") in LOW_EFFORT_WORDS for w in text_clean.split())
    logger.debug(f"Low effort result: {result}")
    return result

def _detect_geo_related(doc: spacy.tokens.Doc) -> bool:
    logger.debug(f"Detecting geo-related terms in: '{doc.text}'")
    result = any(token.lemma_ in GEO_TRIGGERS for token in doc)
    logger.debug(f"Geo-related result: {result}")
    return result

def _suggest_response_style(analysis: MessageAnalysis) -> str:
    logger.debug(f"Suggesting response style for message: {analysis.model_dump_json()}")
    if analysis.subtext.isSarcastic:
        logger.debug("Sarcasm detected, suggesting witty style.")
        return "witty"
    if "flirting_or_sexual" in analysis.subtext.intents:
        logger.debug("Flirting intent detected, suggesting playful style.")
        return "playful"
    if analysis.subtext.isVulnerable:
        return "supportive"
    if analysis.questionInfo.isQuestion:
        return "direct"
    if analysis.subtext.valence > 0.5:
        return "charming"
    return "casual"
