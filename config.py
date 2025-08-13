# config.py

"""
Central configuration file for the Wingman AI application.
This file contains all default values, thresholds, and magic numbers
to make the application easily tunable from a single location.
"""
import os

def get_env_var(key: str, default_value):
    """Gets an environment variable and casts it to the type of the default value."""
    value = os.getenv(key)
    if value is None:
        return default_value

    var_type = type(default_value)
    try:
        if var_type == bool:
            return str(value).lower() in ('true', '1', 't')
        return var_type(value)
    except (ValueError, TypeError):
        return default_value

# --- Database Configuration ---
DATABASE_URL = get_env_var("DATABASE_URL", "sqlite:///./wingman.db")

# --- NLP & Geo-Analysis Configuration ---
SPACY_MODEL = get_env_var("SPACY_MODEL", "en_core_web_sm")
GEOLOCATOR_USER_AGENT = get_env_var("GEOLOCATOR_USER_AGENT", "wingman_ai_strategist_v9")
LONG_DISTANCE_THRESHOLD_KM = get_env_var("LONG_DISTANCE_THRESHOLD_KM", 80)

# --- Conversation Analysis Thresholds ---
INVESTMENT_SCORE_QUESTION_ASKED_BONUS = get_env_var("INVESTMENT_SCORE_QUESTION_ASKED_BONUS", 0.2)
INVESTMENT_SCORE_QUESTION_IGNORED_PENALTY = get_env_var("INVESTMENT_SCORE_QUESTION_IGNORED_PENALTY", -0.15)
INVESTMENT_SCORE_LENGTH_MATCH_BONUS = get_env_var("INVESTMENT_SCORE_LENGTH_MATCH_BONUS", 0.1)
INVESTMENT_SCORE_LENGTH_MISMATCH_PENALTY = get_env_var("INVESTMENT_SCORE_LENGTH_MISMATCH_PENALTY", -0.1)
INVESTMENT_SCORE_LOW_EFFORT_PENALTY = get_env_var("INVESTMENT_SCORE_LOW_EFFORT_PENALTY", -0.3)
INVESTMENT_SCORE_DECAY_FACTOR = get_env_var("INVESTMENT_SCORE_DECAY_FACTOR", 0.8)

SEXUAL_TENSION_INTENT_BONUS = get_env_var("SEXUAL_TENSION_INTENT_BONUS", 0.25)
SEXUAL_TENSION_NEGATIVE_REACTION_PENALTY = get_env_var("SEXUAL_TENSION_NEGATIVE_REACTION_PENALTY", -0.5)
SEXUAL_TENSION_DECAY_FACTOR = get_env_var("SEXUAL_TENSION_DECAY_FACTOR", 0.85)

RAPPORT_CONVO_LENGTH_BONUS_MAX = get_env_var("RAPPORT_CONVO_LENGTH_BONUS_MAX", 0.5)
RAPPORT_CONVO_LENGTH_FACTOR = get_env_var("RAPPORT_CONVO_LENGTH_FACTOR", 10)

TOPIC_STATUS_KEEP_THRESHOLD = get_env_var("TOPIC_STATUS_KEEP_THRESHOLD", 0.4)
TOPIC_STATUS_AVOID_THRESHOLD = get_env_var("TOPIC_STATUS_AVOID_THRESHOLD", -0.3)

# --- Strategic Goal Engine Thresholds ---
DORMANT_INVESTMENT_THRESHOLD = get_env_var("DORMANT_INVESTMENT_THRESHOLD", -0.4)
LUKEWARM_INVESTMENT_THRESHOLD = get_env_var("LUKEWARM_INVESTMENT_THRESHOLD", 0.1)

ASK_RAPPORT_THRESHOLD = get_env_var("ASK_RAPPORT_THRESHOLD", 0.7)
ASK_INVESTMENT_THRESHOLD = get_env_var("ASK_INVESTMENT_THRESHOLD", 0.5)
ASK_SEXUAL_TENSION_THRESHOLD = get_env_var("ASK_SEXUAL_TENSION_THRESHOLD", 0.6)

ESCALATE_RAPPORT_THRESHOLD = get_env_var("ESCALATE_RAPPORT_THRESHOLD", 0.5)
ESCALATE_INVESTMENT_THRESHOLD = get_env_var("ESCALATE_INVESTMENT_THRESHOLD", 0.2)

PUSH_PULL_TRIGGER_PROBABILITY = get_env_var("PUSH_PULL_TRIGGER_PROBABILITY", 0.25)

# --- Default UI Settings ---
DEFAULT_FLIRTY_VALUE = get_env_var("DEFAULT_FLIRTY_VALUE", 50)
DEFAULT_LENGTH_VALUE = get_env_var("DEFAULT_LENGTH_VALUE", 50)
DEFAULT_LINGUISTIC_STYLE = get_env_var("DEFAULT_LINGUISTIC_STYLE", "auto")
DEFAULT_HUMOR_STYLE = get_env_var("DEFAULT_HUMOR_STYLE", "witty")
DEFAULT_VULNERABILITY_LEVEL = get_env_var("DEFAULT_VULNERABILITY_LEVEL", 20)
DEFAULT_END_WITH_QUESTION = get_env_var("DEFAULT_END_WITH_QUESTION", True)
DEFAULT_PERSONA = get_env_var("DEFAULT_PERSONA", "witty_adventurer")
DEFAULT_ULTIMATE_GOAL = get_env_var("DEFAULT_ULTIMATE_GOAL", "Date")
DEFAULT_EMOJI_STRATEGY = get_env_var("DEFAULT_EMOJI_STRATEGY", "auto")
DEFAULT_MODEL_TEMPERATURE = get_env_var("DEFAULT_MODEL_TEMPERATURE", 0.7)
DEFAULT_TOP_P_VALUE = get_env_var("DEFAULT_TOP_P_VALUE", 1.0)

# --- Prompt Generation Configuration ---
MAX_HISTORY_MESSAGES_IN_PROMPT = get_env_var("MAX_HISTORY_MESSAGES_IN_PROMPT", 20)