from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# 1. Input Data Structures

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

# 2. Intermediate Data Structures

@dataclass
class NormalizedData:
    turns: List[Message]
    truncated_history: bool

@dataclass
class FeatureProbes:
    greetings: bool = False
    questions: bool = False
    pet_related: bool = False
    location_related: bool = False
    flirtation_detected: bool = False
    sexual_tone: bool = False
    playful_energy: bool = False
    reciprocity: bool = False
    disclosure: bool = False
    question_asking: bool = False
    response_length_class: str = "medium" # low, medium, high

@dataclass
class Topic:
    label: str
    keywords: List[str]

@dataclass
class GeoTimeInfo:
    time_of_day: str  # e.g., 'morning', 'evening'
    is_virtual: bool
    country_difference: bool

@dataclass
class ContextPack:
    turns: List[Message]
    features: FeatureProbes
    topics: List[Topic]
    geo: GeoTimeInfo
    compressed_history: Optional[str] = None

# 3. Output Data Structures

@dataclass
class Suggestions:
    talking_points: List[str] = field(default_factory=list)
    sexual_suggestions: List[str] = field(default_factory=list)
    intimacy_suggestions: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    next_action_plans: List[str] = field(default_factory=list)

@dataclass
class EngagementMetrics:
    level: str  # low, medium, high
    indicators: List[str]
    reciprocity: bool
    disclosure: bool
    question_asking: bool
    response_length_class: str

@dataclass
class SexualIntimacyAnalysis:
    flirtation_detected: bool
    sexual_tone: bool
    playful_energy: bool
    comfort_level: str  # low, medium, high
    escalation_readiness: str  # early, moderate, ready

@dataclass
class Analysis:
    sexual_intimacy: SexualIntimacyAnalysis
    engagement: EngagementMetrics

@dataclass
class UnifiedJSONOutput:
    topics: List[Topic]
    geo: GeoTimeInfo
    predictions_and_suggestions: Suggestions
    analysis: Analysis
