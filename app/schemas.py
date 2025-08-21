from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# 1. Input Data Structures (Unchanged)

@dataclass
class UserProfile:
    user_id: str
    name: str

@dataclass
class MatchProfile:
    match_id: str
    name: str

@dataclass
class Location:
    city: str
    country: str

@dataclass
class Message:
    role: str  # e.g., 'user', 'match'
    text: str
    timestamp: str

@dataclass
class UISettings:
    enhanced_nlp: bool
    local_model_config: Dict[str, Any]
    time_zone: str

@dataclass
class Payload:
    user_profile: UserProfile
    match_profile: MatchProfile
    location: Location
    conversation_history: List[Message]
    ui_settings: UISettings

# 2. Intermediate Data Structures (Will be refactored as services are updated)

@dataclass
class NormalizedData:
    turns: List[Message]
    truncated_history: bool

@dataclass
class FeatureProbes:
    # Raw signals extracted directly from conversation text
    greetings: bool = False  # Is the last message a greeting?
    recent_greeting_used: bool = False  # Was a greeting used in the last few turns?
    questions: bool = False  # Does the last message contain a question?
    match_contains_question: bool = False # Did the match's last message contain a question?
    pet_related: bool = False
    location_related: bool = False  # Is the last message about a location?
    flirtation_detected: bool = False
    sexual_tone: bool = False
    playful_energy: bool = False
    reciprocity: bool = False
    disclosure: bool = False
    question_asking: bool = False  # Did the user ask a question in their last turn?
    response_length_class: str = "medium"  # low, medium, high
    last_response_by: str = "user"

@dataclass
class Topic:
    label: str
    keywords: List[str]
    # This category will be used to sort topics into the new output schema
    category: str = "neutral" # e.g., focus, avoid, sensitive, fetish, sexual

# 3. New Output Data Structures (Reflects the new JSON schema)

@dataclass
class ConversationStateTopics:
    focus: List[str] = field(default_factory=list)
    avoid: List[str] = field(default_factory=list)
    neutral: List[str] = field(default_factory=list)
    sensitive: List[str] = field(default_factory=list)
    fetish: List[str] = field(default_factory=list)
    sexual: List[str] = field(default_factory=list)

@dataclass
class ConversationState:
    topics: ConversationStateTopics = field(default_factory=ConversationStateTopics)
    recent_topics: Optional[List[str]] = field(default_factory=list)

@dataclass
class GeoLocationDetails:
    city: str = ""
    country: str = ""
    timeOfDay: str = ""
    current_date_time: str = ""

@dataclass
class Geo:
    userLocation: GeoLocationDetails = field(default_factory=GeoLocationDetails)
    matchLocation: GeoLocationDetails = field(default_factory=GeoLocationDetails)
    isVirtual: bool = False
    timeZoneDifference: int = 0
    countryDifference: bool = False

@dataclass
class Suggestions:
    topics: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    sexual: List[str] = field(default_factory=list)
    intimacy: List[str] = field(default_factory=list)

@dataclass
class LastMatchResponse:
    contains_question: bool = False
    related_to_location: bool = False

@dataclass
class Analysis:
    last_response: str = ""  # 'user' or 'match'
    last_match_response: LastMatchResponse = field(default_factory=LastMatchResponse)
    match_engaged: str = "low"  # low/medium/high
    comfort_level: str = "low"
    escalation_readiness: str = "early"
    recent_greeting_used: bool = False
    conversation_pace: str = "balanced"
    reciprocity_balance: str = "balanced"
    flirtation_level: str = "none"
    sexual_response_allowed: bool = False
    length: int = 50
    tone: int = 50
    linguistic_style: str = "casual"
    emoji_strategy: str = "auto"
    suggested_next_action: str = "MAINTAIN_ENGAGEMENT"
    sexual_communication_style: str = "casual_and_flirty"
    date_arc_phase: str = "rapport_building"
    suggested_response_style: str = "thoughtful"

@dataclass
class Sentiment:
    overall: str = "neutral"  # positive, neutral, negative

@dataclass
class UnifiedJSONOutput:
    matchId: str
    conversation_state: ConversationState = field(default_factory=ConversationState)
    geo: Geo = field(default_factory=Geo)
    suggestions: Suggestions = field(default_factory=Suggestions)
    analysis: Analysis = field(default_factory=Analysis)
    sentiment: Sentiment = field(default_factory=Sentiment)
    pipeline: str = "enhanced"
