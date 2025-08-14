from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Union, Optional

from utils.constants import LINGUISTIC_STYLES, HUMOR_STYLES, EMOJI_STRATEGIES

router = APIRouter(
    prefix="/api/v1/options",
    tags=["Configuration Options"],
)


# --- Pydantic Models for the Response ---
class Option(BaseModel):
    key: Any
    name: str
    description: str


class SliderParameter(BaseModel):
    ui_type: Literal["slider"]
    label: str
    description: str
    min: float
    max: float
    step: float = 1.0
    default: Optional[float]


class DropdownParameter(BaseModel):
    ui_type: Literal["dropdown", "segmented_control"]
    label: str
    description: str
    options: List[Option]


class ToggleParameter(BaseModel):
    ui_type: Literal["toggle"]
    label: str
    description: str
    default: Optional[bool]


class Separator(BaseModel):
    ui_type: Literal["separator"]
    label: str


class ParameterGroup(BaseModel):
    title: str
    description: str
    parameters: Dict[str, Union[SliderParameter, DropdownParameter, ToggleParameter, Separator]]


class AllOptionsResponse(BaseModel):
    core_settings: ParameterGroup
    style_settings: ParameterGroup
    strategy_settings: ParameterGroup
    power_user_settings: ParameterGroup


# --- Data Definitions ---
ULTIMATE_GOALS_DATA = [
    {"key": "Date", "name": "Date", "description": "The primary goal is to secure an in-person or virtual date."},
    {"key": "Sexual_Encounter", "name": "Sexual Encounter",
     "description": "The primary goal is to directly propose an in-person or virtual sexual encounter."}
]
OVERRIDE_GOALS_DATA = [
    {"key": "BUILD_RAPPORT", "name": "Build Rapport",
     "description": "Play it safe and focus on building a positive connection."},
    {"key": "ESCALATE_FLIRT", "name": "Escalate Flirt", "description": "Increase the romantic and flirty tension."},
    {"key": "PROPOSE_DATE", "name": "Propose In-Person Date",
     "description": "Directly ask for an in-person meeting like drinks or coffee."},
]


# --- Endpoint Implementation ---
@router.get("/all", response_model=AllOptionsResponse)
async def get_all_options():
    """
    Returns a comprehensive, categorized object of all selectable options and
    parameters supported by the backend for dynamic UI generation.
    """
    core_settings = ParameterGroup(
        title="Core Settings",
        description="The most important settings that define the overall goal and persona.",
        parameters={
            "ultimateGoal": DropdownParameter(
                ui_type="segmented_control", label="Ultimate Goal",
                description="Select the primary objective for this conversation.",
                options=[Option(**g) for g in ULTIMATE_GOALS_DATA]
            )
        }
    )

    style_settings = ParameterGroup(
        title="Style & Tone",
        description="Fine-tune the voice and feel of the generated messages.",
        parameters={
            "flirtyValue": SliderParameter(ui_type="slider", label="Flirtiness",
                                           description="Controls the intensity of romantic and flirty language.", min=0,
                                           max=100, default=50),
            "lengthValue": SliderParameter(ui_type="slider", label="Message Length",
                                           description="Controls the length of the generated message.", min=0, max=100,
                                           default=50),
            "linguisticStyle": DropdownParameter(
                ui_type="dropdown", label="Linguistic Style",
                description="Select the primary linguistic flavor of the message.",
                options=[Option(key=s, name=s.replace("_", " ").title(), description="") for s in LINGUISTIC_STYLES]
            )
        }
    )

    strategy_settings = ParameterGroup(
        title="Strategy & Tactics",
        description="Control the conversational tactics and goals.",
        parameters={
            "overrideGoal": DropdownParameter(
                ui_type="dropdown", label="Override AI Strategy",
                description="Manually select the next strategic goal.",
                options=[Option(**g) for g in OVERRIDE_GOALS_DATA]
            ),
            "endWithQuestion": ToggleParameter(ui_type="toggle", label="End with a Question",
                                               description="Ensure the message ends with a question to encourage a reply.",
                                               default=True)
        }
    )

    power_user_settings = ParameterGroup(
        title="Power User & Debug",
        description="Advanced controls for fine-tuning the AI's behavior and analysis engine.",
        parameters={
            "humorStyle": DropdownParameter(
                ui_type="dropdown", label="Humor Style", description="Specify the exact type of humor to use.",
                options=[Option(key=s, name=s.title(), description="") for s in HUMOR_STYLES]
            ),
            "modelTemperature": SliderParameter(ui_type="slider", label="Model Temperature",
                                                description="Controls the creativity of the AI.", min=0.1, max=1.5,
                                                step=0.1, default=0.7),
            "analysis_overrides_separator": Separator(ui_type="separator", label="Analysis & Psychology Overrides"),
            "investmentScore_override": SliderParameter(ui_type="slider", label="Force Investment Score",
                                                        description="Manually override the AI's calculated investment score (-1.0 to 1.0).",
                                                        min=-1.0, max=1.0, step=0.1, default=None),
            "rapportScore_override": SliderParameter(ui_type="slider", label="Force Rapport Score",
                                                     description="Manually override the AI's calculated rapport score (0.0 to 1.0).",
                                                     min=0.0, max=1.0, step=0.1, default=None),
        }
    )

    return AllOptionsResponse(
        core_settings=core_settings,
        style_settings=style_settings,
        strategy_settings=strategy_settings,
        power_user_settings=power_user_settings
    )