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
    displayName: str
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
    Generates the full, structured list of all configurable options with user-friendly names and corrected UI types.
    """
    # --- Group 1: Core Controls ---
    core_controls_group = ParameterGroup(
        groupName="Core Controls",
        groupDescription="The most important settings that define the style and strategy of the AI.",
        parameters=[
            DropdownParameter(
                name="strategyMode",
                displayName="Strategy Mode",
                uiType="segmented_control",
                valueType="string",
                description="Select the overall AI strategy, from cautious to aggressive.",
                constraints=DropdownConstraints(allowedValues=[
                    ConstraintValueOption(value=s, description=s) for s in constants.STRATEGY_MODES
                ]),
                defaultValue="Balanced",
            ),
            DropdownParameter(
                name="flirtyValue",
                displayName="Flirtiness",
                uiType="dropdown",
                valueType="integer",
                description="Controls the level of flirtatiousness in the generated message.",
                constraints=DropdownConstraints(allowedValues=[
                    ConstraintValueOption(value=10, description="Polite and straightforward"),
                    ConstraintValueOption(value=30, description="Friendly and approachable"),
                    ConstraintValueOption(value=50, description="Lightly flirty and engaging"),
                    ConstraintValueOption(value=70, description="Clearly flirty and playful"),
                    ConstraintValueOption(value=90, description="Bold and sexually suggestive"),
                ]),
                defaultValue=config.DEFAULT_FLIRTY_VALUE,
            ),
            DropdownParameter(
                name="lengthValue",
                displayName="Message Length",
                uiType="dropdown",
                valueType="integer",
                description="Controls the target length of the generated message.",
                constraints=DropdownConstraints(allowedValues=[
                    ConstraintValueOption(value=10, description="Very Short (1 sentence)"),
                    ConstraintValueOption(value=30, description="Short (1-2 sentences)"),
                    ConstraintValueOption(value=50, description="Medium (2-3 sentences)"),
                    ConstraintValueOption(value=70, description="Long (4-5 sentences)"),
                    ConstraintValueOption(value=90, description="Epic (6-7 sentences)"),
                ]),
                defaultValue=config.DEFAULT_LENGTH_VALUE,
            ),
            DropdownParameter(
                name="persona",
                displayName="AI Persona",
                uiType="dropdown",
                valueType="string",
                description="Choose the conversational archetype the AI should embody.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=k, description=v['name']) for k, v in personas.PERSONAS.items()]
                ),
                defaultValue=config.DEFAULT_PERSONA,
            ),
            CheckboxParameter(
                name="endWithQuestion",
                displayName="End with a Question",
                uiType="checkbox",
                valueType="boolean",
                description="Ensure the message ends with a question to encourage a reply.",
                defaultValue=config.DEFAULT_END_WITH_QUESTION,
            ),
        ]
    )

    # --- Group 2: Style & Voice ---
    style_voice_group = ParameterGroup(
        groupName="Style & Voice",
        groupDescription="Fine-tune the specific voice and style of the AI's messages.",
        parameters=[
            DropdownParameter(
                name="linguisticStyle",
                displayName="Linguistic Style",
                uiType="dropdown",
                valueType="string",
                description="Determines the specific linguistic flavor of the generated message.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=s, description=s.replace("_", " ").title()) for s in constants.LINGUISTIC_STYLES]
                ),
                defaultValue=config.DEFAULT_LINGUISTIC_STYLE,
            ),
            DropdownParameter(
                name="humorStyle",
                displayName="Humor Style",
                uiType="dropdown",
                valueType="string",
                description="Specify the exact type of humor to use, if any.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=s, description=s.title()) for s in constants.HUMOR_STYLES]
                ),
                defaultValue=config.DEFAULT_HUMOR_STYLE,
            ),
            DropdownParameter(
                name="emojiStrategy",
                displayName="Emoji Strategy",
                uiType="dropdown",
                valueType="string",
                description="Controls how emojis are used in the generated message.",
                constraints=DropdownConstraints(
                    allowedValues=[ConstraintValueOption(value=s, description=s.title()) for s in constants.EMOJI_STRATEGIES]
                ),
                defaultValue=config.DEFAULT_EMOJI_STRATEGY,
            ),
        ]
    )

    # --- Group 3: Overrides & Manual Control ---
    overrides_group = ParameterGroup(
        groupName="Overrides & Manual Control",
        groupDescription="Manually override the AI's analysis or provide specific instructions.",
        parameters=[
            TextParameter(
                name="customInstruction",
                displayName="Custom Instruction",
                uiType="text_input",
                valueType="string",
                description="Provide a specific, one-time instruction for the AI to follow for the next message.",
                defaultValue="",
            ),
            SliderParameter(
                name="investmentScore_override",
                displayName="Force Investment Score",
                uiType="slider",
                valueType="float",
                description="Manually set the AI's calculated investment score. Affects strategy.",
                constraints=SliderConstraints(min=-1.0, max=1.0, step=0.1),
                defaultValue=None,
            ),
            SliderParameter(
                name="rapportScore_override",
                displayName="Force Rapport Score",
                uiType="slider",
                valueType="float",
                description="Manually set the AI's calculated rapport score. Affects strategy.",
                constraints=SliderConstraints(min=0.0, max=1.0, step=0.1),
                defaultValue=None,
            ),
        ]
    )

    # --- Group 4: Advanced Settings (for Developers/Power Users) ---
    advanced_group = ParameterGroup(
        groupName="Advanced & Debug",
        groupDescription="Fine-tune the core analysis engine and LLM parameters. Adjust with caution.",
        parameters=[
            SliderParameter(
                name="modelTemperature",
                displayName="Model Temperature",
                uiType="slider",
                valueType="float",
                description="Controls the creativity and randomness of the AI. Higher is more creative.",
                constraints=SliderConstraints(min=0.1, max=1.5, step=0.05),
                defaultValue=config.DEFAULT_MODEL_TEMPERATURE,
            ),
            SliderParameter(
                name="INVESTMENT_SCORE_DECAY_FACTOR",
                displayName="Investment Decay Factor",
                uiType="slider",
                valueType="float",
                description="Rate at which investment score decays over time. Lower values mean faster decay.",
                constraints=SliderConstraints(min=0.5, max=1, step=0.05),
                defaultValue=config.INVESTMENT_SCORE_DECAY_FACTOR
            ),
            SliderParameter(
                name="PUSH_PULL_TRIGGER_PROBABILITY",
                displayName="Push-Pull Trigger Probability",
                uiType="slider",
                valueType="float",
                description="Probability of suggesting a 'Push-Pull' strategy when conditions are met.",
                constraints=SliderConstraints(min=0, max=1, step=0.05),
                defaultValue=config.PUSH_PULL_TRIGGER_PROBABILITY
            ),
        ]
    )

    return [core_controls_group, style_voice_group, overrides_group, advanced_group]
