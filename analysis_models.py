from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SubtextAnalysis(BaseModel):
    valence: float = Field(0.0, description="Sentiment score from -1.0 (negative) to 1.0 (positive)")
    arousal: float = Field(0.0, description="Intensity/energy score from -1.0 (calm) to 1.0 (excited)")
    intents: List[str] = Field(default_factory=list, description="Detected intents like 'questioning', 'planning', 'flirting'.")
    isSarcastic: bool = False
    isVulnerable: bool = False

class QuestionInfo(BaseModel):
    isQuestion: bool = False
    count: int = 0
    type: str = Field("none", description="e.g., 'direct', 'indirect', 'open', 'closed'.")

class MessageAnalysis(BaseModel):
    content: str
    role: str
    date: Optional[str] = None
    subtext: SubtextAnalysis
    questionInfo: QuestionInfo
    topics: List[str] = Field(default_factory=list)
    keyEntities: Dict[str, List[str]] = Field(default_factory=dict)
    isLowEffort: bool = False
    wordCount: int = 0

class TopicDetails(BaseModel):
    mentions: int = 0
    sentiment_sum: float = 0.0
    arousal_sum: float = 0.0
    avg_sentiment: float = 0.0
    status: str = Field("neutral", description="e.g., 'keep', 'avoid', 'neutral'.")
    category: str = Field("general_interest", description="e.g., 'flirtatious', 'sexual', 'vulnerable', 'planning'.")
    last_mentioned_date: Optional[str] = None

class MatchMemory(BaseModel):
    dateArcPhase: str = Field("rapport", description="Current phase: rapport, escalation, planning.")
    rapportScore: float = Field(0.0, description="A score from 0 to 1 indicating connection strength.")
    investmentScore: float = Field(0.0, description="A score from -1 to 1 quantifying their interest and effort.")
    sexualTension: float = Field(0.0, description="A score from 0 to 1 quantifying explicit sexual communication.")
    engagementState: str = Field("ACTIVE", description="Responsiveness state: ACTIVE, LUKEWARM, DORMANT.")
    userLocation: Optional[str] = None
    matchLocation: Optional[str] = None
    estimatedDistanceKm: Optional[float] = None
    timeZoneDifferenceHours: Optional[int] = None
    isLongDistance: bool = False
    topics: Dict[str, TopicDetails] = Field(default_factory=dict)
    keyFacts: Dict[str, Any] = Field(default_factory=dict)

class StrategicGoal(BaseModel):
    type: str = Field("BUILD_RAPPORT", description="e.g., BUILD_RAPPORT, PROPOSE_DATE, ENCOURAGE_INTERACTION.")
    justification: str = Field(..., description="The reasoning behind choosing this goal.")
    urgency: str = Field("normal", description="e.g., low, normal, high, critical.")

class FullConversationAnalysis(BaseModel):
    conversationState: str
    current_topic: Optional[str] = None
    lastUserMessageAnalysis: Optional[MessageAnalysis] = None
    lastMatchMessageAnalysis: Optional[MessageAnalysis] = None
    conversationPacing: str = "normal"
    suppressGreeting: bool = False
    strategicGoal: StrategicGoal
    memory: MatchMemory