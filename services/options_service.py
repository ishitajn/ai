# services/options_service.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Union, Optional

import config
from utils import constants
from prompts import personas

# --- Pydantic Models for the Response ---

class ConstraintValueOption(BaseModel):
    value: Any
    description: str

class SliderConstraints(BaseModel):
    min: float
    max: float
    step: float

class DropdownConstraints(BaseModel):
    allowedValues: List[ConstraintValueOption]

class BaseParameter(BaseModel):
    name: str
    description: str
    valueType: str
    defaultValue: Any

class SliderParameter(BaseParameter):
    uiType: Literal["slider"]
    constraints: SliderConstraints

class DropdownParameter(BaseParameter):
    uiType: Literal["dropdown", "segmented_control"]
    constraints: DropdownConstraints

class CheckboxParameter(BaseParameter):
    uiType: Literal["checkbox"]
    constraints: Optional[dict] = None

class TextParameter(BaseParameter):
    uiType: Literal["text_input"]
    constraints: Optional[dict] = None

class ParameterGroup(BaseModel):
    groupName: str
    groupDescription: str
    parameters: List[Union[SliderParameter, DropdownParameter, CheckboxParameter, TextParameter]]

# --- Generator Function ---

def generate_all_options() -> List[ParameterGroup]:
    """
    Generates the full, structured list of all configurable options.
    """
    ui_controls_group = ParameterGroup(
        groupName="UI Controls",
        groupDescription="Settings that directly control the generated message style and content.",
        parameters=[
            SliderParameter(
                name="flirtyValue",
                uiType="slider",
                valueType="integer",
                description="Controls the level of flirtatiousness in the generated message, from polite and respectful to bold and suggestive.",
                constraints=SliderConstraints(min=0, max=100, step=1),
                defaultValue=config.DEFAULT_FLIRTY_VALUE,
            ),
            SliderParameter(
                name="lengthValue",
                uiType="slider",
                valueType="integer",
                description="Controls the target length of the generated message.",
                constraints=SliderConstraints(min=0, max=100, step=1),
                defaultValue=config.DEFAULT_LENGTH_VALUE,
            ),
            DropdownParameter(
                name="linguisticStyle",
                uiType="dropdown",
                valueType="string",
                description="Determines the linguistic style of the generated message.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=s, description=s.replace("_", " ").title()) for s in constants.LINGUISTIC_STYLES]
                ),
                defaultValue=config.DEFAULT_LINGUISTIC_STYLE,
            ),
            DropdownParameter(
                name="humorStyle",
                uiType="dropdown",
                valueType="string",
                description="Specify the exact type of humor to use.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=s, description=s.title()) for s in constants.HUMOR_STYLES]
                ),
                defaultValue=config.DEFAULT_HUMOR_STYLE,
            ),
            CheckboxParameter(
                name="endWithQuestion",
                uiType="checkbox",
                valueType="boolean",
                description="If checked, the generated message will end with a question to encourage a reply.",
                defaultValue=config.DEFAULT_END_WITH_QUESTION,
            ),
            DropdownParameter(
                name="persona",
                uiType="dropdown",
                valueType="string",
                description="Choose the conversational archetype the AI should embody.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=k, description=v['name']) for k, v in personas.PERSONAS.items()]
                ),
                defaultValue=config.DEFAULT_PERSONA,
            ),
            DropdownParameter(
                name="ultimateGoal",
                uiType="segmented_control",
                valueType="string",
                description="Select the primary objective for this conversation.",
                constraints=DropdownConstraints(
                    allowedValues=[
                        ConstraintValueOption(value="Date", description="The primary goal is to secure an in-person or virtual date."),
                        ConstraintValueOption(value="Sexual_Encounter", description="The primary goal is to directly propose an in-person or virtual sexual encounter.")
                    ]
                ),
                defaultValue=config.DEFAULT_ULTIMATE_GOAL,
            ),
            DropdownParameter(
                name="emojiStrategy",
                uiType="dropdown",
                valueType="string",
                description="Controls how emojis are used in the generated message.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=s, description=s.title()) for s in constants.EMOJI_STRATEGIES]
                ),
                defaultValue=config.DEFAULT_EMOJI_STRATEGY,
            ),
            SliderParameter(
                name="modelTemperature",
                uiType="slider",
                valueType="float",
                description="Controls the creativity and randomness of the AI. Higher values mean more creative, lower values mean more predictable.",
                constraints=SliderConstraints(min=0.1, max=1.5, step=0.05),
                defaultValue=config.DEFAULT_MODEL_TEMPERATURE,
            ),
            SliderParameter(
                name="topPValue",
                uiType="slider",
                valueType="float",
                description="Controls the nucleus sampling probability. Only consider words comprising the top P probability mass.",
                constraints=SliderConstraints(min=0.1, max=1.0, step=0.05),
                defaultValue=config.DEFAULT_TOP_P_VALUE,
            ),
            TextParameter(
                name="customInstruction",
                uiType="text_input",
                valueType="string",
                description="Provide a specific, custom instruction for the AI to follow for the next message.",
                defaultValue="",
            ),
        ]
    )

    analysis_overrides_group = ParameterGroup(
        groupName="Analysis Overrides",
        groupDescription="Manually override the AI's internal analysis scores and states. Use with caution.",
        parameters=[
            SliderParameter(
                name="investmentScore_override",
                uiType="slider",
                valueType="float",
                description="Manually override the AI's calculated investment score.",
                constraints=SliderConstraints(min=-1.0, max=1.0, step=0.1),
                defaultValue=None,
            ),
            SliderParameter(
                name="rapportScore_override",
                uiType="slider",
                valueType="float",
                description="Manually override the AI's calculated rapport score.",
                constraints=SliderConstraints(min=0.0, max=1.0, step=0.1),
                defaultValue=None,
            ),
            SliderParameter(
                name="sexualTension_override",
                uiType="slider",
                valueType="float",
                description="Manually override the AI's calculated sexual tension score.",
                constraints=SliderConstraints(min=0.0, max=1.0, step=0.1),
                defaultValue=None,
            ),
            CheckboxParameter(
                name="isLongDistance_override",
                uiType="checkbox",
                valueType="boolean",
                description="Manually override if the conversation is considered long distance.",
                defaultValue=None,
            ),
        ]
    )

    conversation_analysis_group = ParameterGroup(
        groupName="Conversation Analysis Thresholds",
        groupDescription="Advanced settings to fine-tune how the AI analyzes conversational dynamics. Adjust with caution.",
        parameters=[
            SliderParameter(name="INVESTMENT_SCORE_QUESTION_ASKED_BONUS", uiType="slider", valueType="float", description="Bonus for asking a question.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.INVESTMENT_SCORE_QUESTION_ASKED_BONUS),
            SliderParameter(name="INVESTMENT_SCORE_QUESTION_IGNORED_PENALTY", uiType="slider", valueType="float", description="Penalty for ignoring a question.", constraints=SliderConstraints(min=-1, max=0, step=0.05), defaultValue=config.INVESTMENT_SCORE_QUESTION_IGNORED_PENALTY),
            SliderParameter(name="INVESTMENT_SCORE_LENGTH_MATCH_BONUS", uiType="slider", valueType="float", description="Bonus for matching message length.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.INVESTMENT_SCORE_LENGTH_MATCH_BONUS),
            SliderParameter(name="INVESTMENT_SCORE_LENGTH_MISMATCH_PENALTY", uiType="slider", valueType="float", description="Penalty for mismatched message length.", constraints=SliderConstraints(min=-1, max=0, step=0.05), defaultValue=config.INVESTMENT_SCORE_LENGTH_MISMATCH_PENALTY),
            SliderParameter(name="INVESTMENT_SCORE_LOW_EFFORT_PENALTY", uiType="slider", valueType="float", description="Penalty for low-effort replies.", constraints=SliderConstraints(min=-1, max=0, step=0.05), defaultValue=config.INVESTMENT_SCORE_LOW_EFFORT_PENALTY),
            SliderParameter(name="INVESTMENT_SCORE_DECAY_FACTOR", uiType="slider", valueType="float", description="Decay factor for investment score over time.", constraints=SliderConstraints(min=0.5, max=1, step=0.05), defaultValue=config.INVESTMENT_SCORE_DECAY_FACTOR),
            SliderParameter(name="SEXUAL_TENSION_INTENT_BONUS", uiType="slider", valueType="float", description="Bonus for sexual intent.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.SEXUAL_TENSION_INTENT_BONUS),
            SliderParameter(name="SEXUAL_TENSION_NEGATIVE_REACTION_PENALTY", uiType="slider", valueType="float", description="Penalty for negative reaction to sexual intent.", constraints=SliderConstraints(min=-1, max=0, step=0.05), defaultValue=config.SEXUAL_TENSION_NEGATIVE_REACTION_PENALTY),
            SliderParameter(name="SEXUAL_TENSION_DECAY_FACTOR", uiType="slider", valueType="float", description="Decay factor for sexual tension.", constraints=SliderConstraints(min=0.5, max=1, step=0.05), defaultValue=config.SEXUAL_TENSION_DECAY_FACTOR),
            SliderParameter(name="RAPPORT_CONVO_LENGTH_BONUS_MAX", uiType="slider", valueType="float", description="Max bonus for conversation length.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.RAPPORT_CONVO_LENGTH_BONUS_MAX),
            SliderParameter(name="RAPPORT_CONVO_LENGTH_FACTOR", uiType="slider", valueType="integer", description="Factor for conversation length bonus.", constraints=SliderConstraints(min=1, max=50, step=1), defaultValue=config.RAPPORT_CONVO_LENGTH_FACTOR),
            SliderParameter(name="TOPIC_STATUS_KEEP_THRESHOLD", uiType="slider", valueType="float", description="Sentiment threshold to keep a topic.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.TOPIC_STATUS_KEEP_THRESHOLD),
            SliderParameter(name="TOPIC_STATUS_AVOID_THRESHOLD", uiType="slider", valueType="float", description="Sentiment threshold to avoid a topic.", constraints=SliderConstraints(min=-1, max=0, step=0.05), defaultValue=config.TOPIC_STATUS_AVOID_THRESHOLD),
        ]
    )

    strategic_goal_group = ParameterGroup(
        groupName="Strategic Goal Engine Thresholds",
        groupDescription="Thresholds that determine which strategic goal the AI should pursue.",
        parameters=[
            SliderParameter(name="DORMANT_INVESTMENT_THRESHOLD", uiType="slider", valueType="float", description="Investment score below which the conversation is considered dormant.", constraints=SliderConstraints(min=-1, max=0, step=0.05), defaultValue=config.DORMANT_INVESTMENT_THRESHOLD),
            SliderParameter(name="LUKEWARM_INVESTMENT_THRESHOLD", uiType="slider", valueType="float", description="Investment score below which the conversation is lukewarm.", constraints=SliderConstraints(min=-0.5, max=0.5, step=0.05), defaultValue=config.LUKEWARM_INVESTMENT_THRESHOLD),
            SliderParameter(name="ASK_RAPPORT_THRESHOLD", uiType="slider", valueType="float", description="Rapport threshold for asking for a date.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.ASK_RAPPORT_THRESHOLD),
            SliderParameter(name="ASK_INVESTMENT_THRESHOLD", uiType="slider", valueType="float", description="Investment threshold for asking for a date.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.ASK_INVESTMENT_THRESHOLD),
            SliderParameter(name="ASK_SEXUAL_TENSION_THRESHOLD", uiType="slider", valueType="float", description="Sexual tension threshold for proposing an encounter.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.ASK_SEXUAL_TENSION_THRESHOLD),
            SliderParameter(name="ESCALATE_RAPPORT_THRESHOLD", uiType="slider", valueType="float", description="Rapport threshold for escalating.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.ESCALATE_RAPPORT_THRESHOLD),
            SliderParameter(name="ESCALATE_INVESTMENT_THRESHOLD", uiType="slider", valueType="float", description="Investment threshold for escalating.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.ESCALATE_INVESTMENT_THRESHOLD),
            SliderParameter(name="PUSH_PULL_TRIGGER_PROBABILITY", uiType="slider", valueType="float", description="Probability of triggering a push-pull.", constraints=SliderConstraints(min=0, max=1, step=0.05), defaultValue=config.PUSH_PULL_TRIGGER_PROBABILITY),
        ]
    )

    geo_analysis_group = ParameterGroup(
        groupName="Geo-Analysis Configuration",
        groupDescription="Settings related to geo-location analysis.",
        parameters=[
            SliderParameter(name="LONG_DISTANCE_THRESHOLD_KM", uiType="slider", valueType="integer", description="Distance in kilometers to be considered long distance.", constraints=SliderConstraints(min=1, max=500, step=1), defaultValue=config.LONG_DISTANCE_THRESHOLD_KM),
        ]
    )

    return [ui_controls_group, analysis_overrides_group, conversation_analysis_group, strategic_goal_group, geo_analysis_group]
