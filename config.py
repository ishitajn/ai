# config.py

"""
Central configuration file for the Wingman AI application.
This file contains all default values, thresholds, and magic numbers
to make the application easily tunable from a single location.
"""

# --- Database Configuration ---
DATABASE_URL = "sqlite:///./wingman.db"

# --- NLP & Geo-Analysis Configuration ---
SPACY_MODEL = "en_core_web_sm"
GEOLOCATOR_USER_AGENT = "wingman_ai_strategist_v9"
LONG_DISTANCE_THRESHOLD_KM = 80  # Approx. 50 miles

# --- Conversation Analysis Thresholds ---
# Investment Score Calculation
INVESTMENT_SCORE_QUESTION_ASKED_BONUS = 0.2
INVESTMENT_SCORE_QUESTION_IGNORED_PENALTY = -0.15
INVESTMENT_SCORE_LENGTH_MATCH_BONUS = 0.1
INVESTMENT_SCORE_LENGTH_MISMATCH_PENALTY = -0.1
INVESTMENT_SCORE_LOW_EFFORT_PENALTY = -0.3
INVESTMENT_SCORE_DECAY_FACTOR = 0.8

# Sexual Tension Calculation
SEXUAL_TENSION_INTENT_BONUS = 0.25
SEXUAL_TENSION_NEGATIVE_REACTION_PENALTY = -0.5
SEXUAL_TENSION_DECAY_FACTOR = 0.85

# Rapport Score Calculation
RAPPORT_CONVO_LENGTH_BONUS_MAX = 0.5
RAPPORT_CONVO_LENGTH_FACTOR = 10 # (num_messages / this_factor)

# Topic Status Thresholds
TOPIC_STATUS_KEEP_THRESHOLD = 0.4
TOPIC_STATUS_AVOID_THRESHOLD = -0.3

# --- Strategic Goal Engine Thresholds ---
# Engagement State
DORMANT_INVESTMENT_THRESHOLD = -0.4
LUKEWARM_INVESTMENT_THRESHOLD = 0.1

# "The Ask" Conditions
ASK_RAPPORT_THRESHOLD = 0.7
ASK_INVESTMENT_THRESHOLD = 0.5
ASK_SEXUAL_TENSION_THRESHOLD = 0.6

# Escalation Conditions
ESCALATE_RAPPORT_THRESHOLD = 0.5
ESCALATE_INVESTMENT_THRESHOLD = 0.2

# Push-Pull Trigger Probability
PUSH_PULL_TRIGGER_PROBABILITY = 0.25

# --- Default UI Settings ---
# These are the "factory defaults" for the FullUISettings model.
DEFAULT_FLIRTY_VALUE = 50
DEFAULT_LENGTH_VALUE = 50
DEFAULT_LINGUISTIC_STYLE = "auto"
DEFAULT_HUMOR_STYLE = "witty"
DEFAULT_VULNERABILITY_LEVEL = 20
DEFAULT_END_WITH_QUESTION = True
DEFAULT_ULTIMATE_GOAL = "Date"
DEFAULT_EMOJI_STRATEGY = "auto"
DEFAULT_MODEL_TEMPERATURE = 0.7
DEFAULT_TOP_P_VALUE = 1.0