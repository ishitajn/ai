from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Sub-models for Analysis ---

class SubtextAnalysis(BaseModel):
    valence: float = Field(0.0, description="Sentiment score from -1.0 (negative) to 1.0 (positive).")
    arousal: float = Field(0.0, description="Intensity/energy score from -1.0 (calm) to 1.0 (excited).")
    intents: List[str] = Field(default_factory=list, description="Detected intents like 'planning', 'flirting'.")
    isSarcastic: bool = False
    isVulnerable: bool = False
    isAmbiguous: bool = False

class QuestionInfo(BaseModel):
    isQuestion: bool = False
    count: int = 0
    type: str = Field("none", description="e.g., 'direct', 'indirect', 'open', 'closed'.")

class MessageAnalysis(BaseModel):
    content: str
    role: str
    subtext: SubtextAnalysis
    questionInfo: QuestionInfo
    isLowEffort: bool = False
    isGeoRelated: bool = False
    wordCount: int = 0
    suggestedResponseStyle: Optional[str] = None

class TopicDetails(BaseModel):
    score: float = Field(0.0, description="A calculated score representing the topic's importance or sentiment.")
    mentions: int = 0

class PersonalityProfile(BaseModel):
    extraversion: float = 0.0
    agreeableness: float = 0.0
    openness: float = 0.0

class MatchMemory(BaseModel):
    dateArcPhase: str = Field("rapport", description="Current phase: rapport, escalation, planning.")
    rapportScore: float = Field(0.0, description="A score from 0 to 1 indicating connection strength.")
    investmentScore: float = Field(0.0, description="A score from -1 to 1 quantifying their interest and effort.")
    sexualTension: float = Field(0.0, description="A score from 0 to 1 quantifying explicit sexual communication.")
    topics: Dict[str, TopicDetails] = Field(default_factory=dict)
    insideJokes: List[str] = Field(default_factory=list)
    avoidedTopics: List[str] = Field(default_factory=list)
    questionHistory: List[str] = Field(default_factory=list)
    personalityProfile: PersonalityProfile = Field(default_factory=PersonalityProfile)
    redFlags: List[str] = Field(default_factory=list)

class DateLogistics(BaseModel):
    venue: Optional[str] = None
    address: Optional[str] = None
    time: Optional[str] = None

class DateAnalysis(BaseModel):
    isDatePlanned: bool = False
    dateCommitmentLevel: str = "none"
    dateLogistics: DateLogistics = Field(default_factory=DateLogistics)
    dateType: str = "none"
    dateVibe: str = "none"
    whoInitiated: str = "none"

class ConsentSignal(BaseModel):
    type: str
    evidence: str

class SexualAnalysis(BaseModel):
    sexualTensionScore: float = 0.0
    sexualIntentConfidence: float = 0.0
    escalationPace: str = "none"
    dominantSubmissiveScore: float = 0.0
    consentSignals: List[ConsentSignal] = Field(default_factory=list)
    kinksAndFetishes: List[str] = Field(default_factory=list)
    sexualCommunicationStyle: str = "none"
    sexualResponseSuggestion: str = "none"
    sexualArchetype: str = "none"
    reciprocityScore: float = 0.0
    explicitToImplicitRatio: float = 0.0

class ResponseSuggestions(BaseModel):
    length: int = 0
    tone: int = 0
    linguisticStyle: str = "casual"
    emojiStrategy: str = "auto"
    endWithQuestion: bool = True
    suggestedNextAction: str = "BUILD_RAPPORT"
    confidenceScore: float = 0.0
    keyTalkingPoints: List[str] = Field(default_factory=list)

class LocationContext(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    timeZone: Optional[str] = None
    timeOfDay: Optional[str] = None

class GeoContext(BaseModel):
    userLocation: LocationContext = Field(default_factory=LocationContext)
    matchLocation: LocationContext = Field(default_factory=LocationContext)
    distance: Dict[str, Optional[int]] = Field(default_factory=lambda: {"km": None, "miles": None})
    timeZoneDifference: Optional[int] = None
    countryDifference: bool = False
    isVirtual: bool = False

# --- Main Analysis Container ---

class FullConversationAnalysis(BaseModel):
    """
    The main internal container for all analysis results.
    """
    conversationState: str
    suppressGreeting: bool
    lastMessageAnalysis: Optional[MessageAnalysis] = None
    memory: MatchMemory = Field(default_factory=MatchMemory)
    dateAnalysis: DateAnalysis = Field(default_factory=DateAnalysis)
    sexualAnalysis: SexualAnalysis = Field(default_factory=SexualAnalysis)
    responseSuggestions: ResponseSuggestions = Field(default_factory=ResponseSuggestions)
    geoContext: GeoContext = Field(default_factory=GeoContext)
