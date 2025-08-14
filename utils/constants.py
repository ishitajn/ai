import re

# --- UI & Style Constants ---
LINGUISTIC_STYLES = [
    "auto", "casual", "charming", "direct", "intellectual", "mysterious",
    "playful", "poetic", "sarcastic", "sexual", "witty"
]
HUMOR_STYLES = ["none", "witty", "sarcastic", "goofy", "dry", "self-deprecating"]
EMOJI_STRATEGIES = ["auto", "none", "sparing", "heavy"]
DATE_ARC_PHASES = ["rapport", "escalation", "planning", "post_date"]

# --- Word & Phrase Dictionaries for Analysis ---

# Sentiment & Arousal
POSITIVE_WORDS = {
    "love": 0.9, "amazing": 0.9, "incredible": 0.9, "perfect": 0.95, "gorgeous": 0.9,
    "beautiful": 0.85, "awesome": 0.8, "brilliant": 0.8, "fantastic": 0.8, "wonderful": 0.8,
    "absolutely": 0.7, "definitely": 0.7, "happy": 0.7, "excited": 0.7, "hilarious": 0.7,
    "lovely": 0.7, "great": 0.7, "fun": 0.6, "sweet": 0.6, "dope": 0.6, "cute": 0.6,
    "interesting": 0.5, "nice": 0.5, "cool": 0.4, "adore": 0.8, "excellent": 0.8, "charming": 0.7
}
NEGATIVE_WORDS = {
    "worst": -1.0, "hate": -0.9, "awful": -0.9, "horrible": -0.9, "terrible": -0.8,
    "sucks": -0.8, "dislike": -0.8, "boring": -0.7, "frustrating": -0.7, "sad": -0.7,
    "annoying": -0.6, "disappointing": -0.6, "bad": -0.6, "lame": -0.5, "bummer": -0.5,
    "rough": -0.5, "unfortunate": -0.5, "meh": -0.4, "ugh": -0.4, "gross": -0.8, "creepy": -0.9
}
AROUSAL_WORDS = {
    "omfg": 0.9, "wtf": 0.8, "insane": 0.8, "!!!": 0.8, "crazy": 0.7, "omg": 0.7,
    "no way": 0.7, "wow": 0.6, "rofl": 0.6, "!!": 0.6, "lmao": 0.5, "what": 0.5,
    "hahaha": 0.4, "!": 0.3, "lol": 0.3, "haha": 0.2, "holy shit": 0.9,
    "boring": -0.7, "exhausted": -0.6, "tired": -0.6, "sleepy": -0.4
}
INTENSIFIERS = {"very": 1.5, "so": 1.4, "really": 1.4, "extremely": 1.7, "incredibly": 1.7, "super": 1.6, "insanely": 1.8, "totally": 1.5, "literally": 1.3}
NEGATION_WORDS = {"not", "no", "never", "don't", "can't", "won't", "isn't", "aren't", "wasn't", "weren't", "couldn't", "shouldn't"}

# Semantic Intent & Categorization
VULNERABLE_WORDS = [
    "confess", "to be honest", "tbh", "honestly", "i admit", "i feel", "feeling a bit",
    "i struggle with", "i'm worried", "nervous", "anxious", "opening up", "it's been tough",
    "my secret is", "i've never told anyone", "is that weird", "if that makes sense",
    "i'm confused", "insecure", "my therapist", "my therapy"
]
SEXUAL_WORDS = [
    "bed", "body", "craving", "cuddle", "desire", "dirty", "gorgeous", "hot", "kiss",
    "lips", "naughty", "pleasure", "sexy", "sheets", "skin", "spoil", "stunning",
    "taste", "tease", "touch", "undress", "come over", "my place", "your place",
    "bra", "panties", "breast", "lingerie", "thong", "lace", "victoria secret",
    "fuck", "sex", "horny", "wet", "hard", "cock", "dick", "pussy", "vagina", "penis",
    "ass", "booty", "tits", "boobs", "orgasm", "cum", "clit", "nipples",
    "hookup", "fwb", "friends with benefits", "one night stand", "naked", "seduce",
    "dominate", "submissive", "kinky", "fetish", "bdsm", "choke", "spank", "daddy"
]
PLANNING_WORDS = ["when", "where", "what time", "let's", "we should", "free", "available", "schedule", "address", "number", "drinks", "coffee", "date", "meet up", "hang out"]
GEO_TRIGGERS = {
    "where", "from", "at", "in", "live", "based", "travel", "visit", "trip",
    "country", "city", "town", "location", "neighborhood", "here", "there", "area", "place"
}
PROFESSIONAL_WORDS = {
    "work", "job", "career", "office", "company", "project", "meeting", "business",
    "industry", "role", "profession", "colleague", "linkedin"
}
COMPLIMENT_WORDS = {
    "amazing", "awesome", "beautiful", "brilliant", "charming", "cool", "cute", "dope",
    "excellent", "fantastic", "fun", "gorgeous", "great", "handsome", "hilarious",
    "hot", "incredible", "impressive", "interesting", "love", "lovely", "nice",
    "perfect", "sexy", "stunning", "sweet", "wonderful", "incredible", "breathtaking"
}

# Behavioral Patterns
LOW_EFFORT_WORDS = {
    "ok", "okay", "k", "yep", "yup", "yeah", "lol", "haha", "cool", "nice", "thx",
    "ty", "np", "idk", "hbu", "wbu", "wyd", "nm", "gn", "gm", "lmao", "hmmm",
    "👍", "👌", "😂", "❤️", "🔥", "sounds good", "gotcha", "sure"
}
GREETING_KEYWORDS = {
    "hey", "hi", "hello", "yo", "sup", "hiya", "heya", "howdy", "good morning",
    "morning", "'morning", "good afternoon", "afternoon", "good evening", "evening", "what's up"
}
INDIRECT_QUESTION_STARTERS = ["i was wondering", "i'm curious", "tell me about", "what do you think about", "curious about"]
POWER_MOVE_PHRASES = ["i'll let you know", "we'll see", "let me get back to you", "i'm busy", "i have to check", "remind me"]
SHIT_TEST_PATTERNS = [
    r"i bet you say that to all", r"are you a player", r"you probably have so many",
    r"don't break my heart", r"are you trying to", r"you must be", r"\bslow down\b",
    r"getting to know you", r"\bfar away\b", r"in the next few weeks", r"prove it", r"impress me"
]

# Emojis & Misc
SEXUAL_EMOJIS = re.compile(r"[😏😈🔥💦🥵😜😉💋👅🍑🍆🛏️🤤😇👀💅✨🫦]")
AMBIGUOUS_PHRASES = ["im down", "sounds good", "maybe", "we should", "sometime", "i guess", "if you want"]
SARCASTIC_MARKERS = ["yeah right", "sure...", "whatever", "obviously", "i'm sure"]

# --- Red Flag Detection ---
RED_FLAGS = [
    "my ex", "still friends with my ex", "still live with my ex",
    "drama", "i hate drama", "no drama", "all my exes are crazy",
    "crazy", "psycho", "insane", "unhinged", "i'm a handful",
    "money problems", "i'm broke", "can you lend me", "venmo me", "cash app me",
    "move on fast", "get attached quickly", "love bombing",
    "looking for someone to take care of me", "spoil me",
    "i have a dark side", "not like other girls", "if you can't handle me at my worst"
]

# --- Date Analysis Constants ---
DATE_KEYWORDS = {
    "coffee": "coffee", "drinks": "drinks", "dinner": "dinner", "walk": "walk",
    "hike": "hike", "movie": "movie", "call": "virtual", "video chat": "virtual",
    "bar": "drinks", "restaurant": "dinner", "park": "walk"
}
COMMITMENT_LEVELS = {
    "confirmed": ["i'm free", "see you then", "it's a date", "sounds perfect", "i'm in", "let's do it"],
    "provisional": ["we should", "let's try", "maybe we can", "i'd be down"],
    "low": ["sometime", "maybe", "perhaps"]
}
