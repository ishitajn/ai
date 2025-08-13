from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from analysis_models import FullConversationAnalysis
from config import (
    DEFAULT_FLIRTY_VALUE, DEFAULT_LENGTH_VALUE, DEFAULT_LINGUISTIC_STYLE,
    DEFAULT_HUMOR_STYLE, DEFAULT_VULNERABILITY_LEVEL, DEFAULT_END_WITH_QUESTION,
    DEFAULT_PERSONA, DEFAULT_ULTIMATE_GOAL, DEFAULT_EMOJI_STRATEGY,
    DEFAULT_MODEL_TEMPERATURE, DEFAULT_TOP_P_VALUE
)

# --- Data Structures for Scraped Data & UI Settings ---

class ScrapedConversationMessage(BaseModel):
    role: str
    content: str
    date: Optional[str] = None

class ScrapedData(BaseModel):
    myName: Optional[str] = "You"
    theirName: Optional[str] = "Match"
    theirProfile: str
    theirLocationString: Optional[str] = None
    conversationHistory: List[ScrapedConversationMessage]

class InitialUISettings(BaseModel):
    """The minimal settings required for an initial analysis."""
    myLocation: str
    myProfile: str
    local_model_name: str

class FullUISettings(InitialUISettings):
    """
    Represents the complete state of all UI controls. This is used for
    regeneration requests and is sent back by the server to show what
    settings were applied.
    """
    # Core
    ultimateGoal: str = Field(default=DEFAULT_ULTIMATE_GOAL)
    persona: str = Field(default=DEFAULT_PERSONA)
    
    # Style
    flirtyValue: int = Field(default=DEFAULT_FLIRTY_VALUE)
    lengthValue: int = Field(default=DEFAULT_LENGTH_VALUE)
    linguisticStyle: str = Field(default=DEFAULT_LINGUISTIC_STYLE)
    
    # Strategy
    overrideGoal: Optional[str] = Field(default=None)
    endWithQuestion: bool = Field(default=DEFAULT_END_WITH_QUESTION)
    
    # Power User
    humorStyle: str = Field(default=DEFAULT_HUMOR_STYLE)
    emojiStrategy: str = Field(default=DEFAULT_EMOJI_STRATEGY)
    modelTemperature: float = Field(default=DEFAULT_MODEL_TEMPERATURE)
    topPValue: float = Field(default=DEFAULT_TOP_P_VALUE)
    customInstruction: str = Field(default="")
    strictGoalOverride: bool = Field(default=False)
    
    # Analysis Overrides
    investmentScore_override: Optional[float] = Field(default=None)
    rapportScore_override: Optional[float] = Field(default=None)
    sexualTension_override: Optional[float] = Field(default=None)
    isLongDistance_override: Optional[bool] = Field(default=None)
    engagementState_override: Optional[str] = Field(default=None)
    dateArcPhase_override: Optional[str] = Field(default=None)

# --- Endpoint Payloads ---

class AnalysisRequest(BaseModel):
    """Payload for the initial /analyze endpoint."""
    matchId: str
    scraped_data: ScrapedData
    ui_settings: InitialUISettings

class RegenerationRequest(BaseModel):
    """Payload for the /regenerate endpoint."""
    matchId: str
    scraped_data: ScrapedData # Needed to rebuild context in prompts
    ui_settings: FullUISettings

class PromptGenerationResponse(BaseModel):
    """The structure for the 'prompts' object in the main API response."""
    system_prompt: str
    user_prompt: str
    model_name: str
    temperature: float
    top_p: float

class FullApiResponse(BaseModel):
    """The main response object for both /analyze and /regenerate."""
    prompts: PromptGenerationResponse
    full_analysis: FullConversationAnalysis
    applied_ui_settings: FullUISettings