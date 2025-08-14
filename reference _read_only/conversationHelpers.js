// conversationHelpers.js (Updated with Dynamic Defaults & Granular Analysis)

import nlp from "./lib/compromise.js";
const DEBUG = {
  log: (category, message, data = null) =>
    console.log(
      `[WINGMAN-HELPER-${category.toUpperCase()}] ${message}`,
      data ?? ""
    ),
};
export const LINGUISTIC_STYLES = [
  "auto",
  "casual",
  "charming",
  "direct",
  "intellectual",
  "mysterious",
  "playful",
  "poetic",
  "sarcastic",
  "sexual",
  "witty",
].sort((a, b) => (a === "auto" ? -1 : b === "auto" ? 1 : a.localeCompare(b)));
export const DATE_ARC_PHASES = ["rapport", "escalation", "planning"];

// ===================================================================================
// SECTION 1: CORE MESSAGE ANALYSIS
// ===================================================================================

/**
 * Analyzes a single message for subtext, intent, and style.
 * @param {string} text - The message content.
 * @returns {object} A structured analysis object.
 */
function analyzeSingleMessage(text) {
  if (!text) {
    return {
      content: "",
      doc: nlp(""),
      subtext: {
        valence: 0.0,
        arousal: 0.0,
        intents: [],
        isSarcastic: false,
        isAmbiguous: false,
        isVulnerable: false,
      },
      questionInfo: { isQuestion: false, count: 0, type: "none" },
      isLowEffort: true,
      isGeoRelated: false,
      wordCount: 0,
    };
  }
  const doc = nlp(text);
  const subtext = analyzeMessageSubtext(doc);
  const questionInfo = analyzeQuestion(doc);

  return {
    content: text,
    doc,
    subtext,
    questionInfo,
    isDirectQuestion: questionInfo.isQuestion,
    isLowEffort: isLowEffortReply(text),
    isGeoRelated: isMessageGeoRelated(text),
    wordCount: doc.wordCount(),
  };
}

/**
 * Analyzes the subtext of a single message for emotion, intent, and nuance.
 * @param {object} doc - A compromise.js document object.
 * @returns {Omit<LastMessageAnalysis, 'isDirectQuestion' | 'isLowEffort' | 'isGeoRelated' | 'suggestedResponseStyle' | 'questionInfo'>} A structured object containing detailed subtext analysis.
 */
function analyzeMessageSubtext(doc) {
  const subtext = {
    valence: 0.0,
    arousal: 0.0,
    intents: new Set(),
    isSarcastic: false,
    isAmbiguous: false,
    isVulnerable: false,
  };

  const positiveWords = {
    absolutely: 0.7,
    amazing: 0.9,
    awesome: 0.8,
    beautiful: 0.85,
    brilliant: 0.8,
    cool: 0.4,
    cute: 0.6,
    definitely: 0.7,
    dope: 0.6,
    excellent: 0.8,
    excited: 0.7,
    fantastic: 0.8,
    fun: 0.6,
    gorgeous: 0.9,
    great: 0.7,
    happy: 0.7,
    hilarious: 0.7,
    incredible: 0.9,
    interesting: 0.5,
    love: 0.9,
    lovely: 0.7,
    nice: 0.5,
    perfect: 0.95,
    sweet: 0.6,
    totally: 0.6,
    wonderful: 0.8,
    wow: 0.7,
  };
  const negativeWords = {
    annoying: -0.6,
    awful: -0.9,
    bad: -0.6,
    boring: -0.7,
    bummer: -0.5,
    disappointing: -0.6,
    dislike: -0.8,
    frustrating: -0.7,
    hate: -0.9,
    horrible: -0.9,
    lame: -0.5,
    meh: -0.4,
    rough: -0.5,
    sad: -0.7,
    sucks: -0.8,
    terrible: -0.8,
    ugh: -0.4,
    unfortunate: -0.5,
    worst: -1.0,
  };
  const arousalWords = {
    "!": 0.3,
    "!!": 0.6,
    "!!!": 0.8,
    boring: -0.7,
    crazy: 0.7,
    exhausted: -0.6,
    haha: 0.2,
    hahaha: 0.4,
    insane: 0.8,
    lmao: 0.5,
    lol: 0.3,
    "no way": 0.7,
    omg: 0.7,
    omfg: 0.9,
    rofl: 0.6,
    sleepy: -0.4,
    tired: -0.6,
    what: 0.5,
    wow: 0.6,
    wtf: 0.8,
  };
  const vulnerableWords = [
    "a little scared",
    "actually",
    "confess",
    "feeling a bit down",
    "honestly",
    "i admit",
    "i feel",
    "i struggle with",
    "i've never told anyone",
    "i'm worried",
    "if that makes sense",
    "is that weird",
    "it's been tough",
    "my secret is",
    "nervous",
    "opening up",
    "tbh",
    "to be honest",
  ];
  const sexualWords = [
    "bed",
    "beautiful",
    "body",
    "come over",
    "craving",
    "cuddle",
    "cute",
    "desire",
    "dirty",
    "get a room",
    "gorgeous",
    "handsome",
    "hot",
    "kiss",
    "lips",
    "make a move",
    "my place",
    "naughty",
    "pleasure",
    "sexy",
    "sheets",
    "skin",
    "spoil",
    "stunning",
    "taste",
    "tease",
    "tonight",
    "touch",
    "undress",
    "your place",
  ];
  const sexualEmojis =
    /😏|😈|🔥|💦|🥵|😜|😉|💋|👅|🍑|🍆|🛏️|🤤|😇|👀|💅|✨|🫦|👉|👌|👇|👆|💦|💨|♋️|69|💥|💫|✨|🌶️|🍭|🍦|🍩|🌮|🌭|🍌|🍒|🍾|🥂|⛓️|🔗|🪢|🪚|🔨|📍|📌| handcuffs | whip |🕯️|🔑|🔐|🍼| kitten | puppy | bull | top | bottom /;
  const text = doc.text("text");

  Object.entries(positiveWords).forEach(([word, score]) => {
    if (doc.has(word)) subtext.valence += score;
  });
  Object.entries(negativeWords).forEach(([word, score]) => {
    if (doc.has(word)) subtext.valence += score;
  });
  Object.entries(arousalWords).forEach(([word, score]) => {
    if (text.includes(word)) subtext.arousal += score;
  });

  if (analyzeQuestion(doc).isQuestion) subtext.intents.add("questioning");
  if (detectLogisticsSignal(doc)) subtext.intents.add("planning");
  if (doc.has("(haha|lol|lmao|rofl)")) subtext.intents.add("reacting_to_humor");
  if (doc.has("#PastTense") && doc.wordCount() > 15)
    subtext.intents.add("storytelling");
  if (doc.has(sexualWords.join("|")) || sexualEmojis.test(text))
    subtext.intents.add("flirting_or_sexual");
  if (subtext.intents.has("flirting_or_sexual")) {
    subtext.valence += 0.5;
    subtext.arousal += 0.7;
  }
  const sarcasticMarkers = [
    "(yeah right|sure|whatever|obviously)",
    "(so|totally|just) #Adverb? #PositiveAdjective",
  ];
  if (doc.has(sarcasticMarkers.join("|")) && subtext.valence > 0)
    subtext.isSarcastic = true;

  const ambiguousPhrases = [
    "im down",
    "sounds good",
    "maybe",
    "we should",
    "sometime",
  ];
  if (doc.has(ambiguousPhrases.join("|")) && !subtext.intents.has("planning"))
    subtext.isAmbiguous = true;

  if (doc.has(vulnerableWords.join("|"))) subtext.isVulnerable = true;

  subtext.valence = Math.max(-1, Math.min(1, subtext.valence));
  subtext.arousal = Math.max(-1, Math.min(1, subtext.arousal));
  subtext.intents = Array.from(subtext.intents);

  return subtext;
}

// ===================================================================================
// SECTION 2: DYNAMIC DEFAULTS & MEMORY
// ===================================================================================

/**
 * Calculates dynamic default settings based on the full conversation analysis.
 * @param {object} analysis - The full analysis object from runFullConversationAnalysis.
 * @returns {object} An object with suggested default values for UI controls.
 */
function calculateDynamicDefaults(analysis) {
  const { conversationState, lastMatchMessageAnalysis, memory } = analysis;
  const defaults = {
    flirtyValue: 50,
    lengthValue: 50,
    linguisticStyle: "auto",
    emojiStrategy: "auto",
    endWithQuestion: true,
    geoContextToggle: false,
  };

  // Flirty Value Logic
  if (
    memory.dateArcPhase === "escalation" ||
    lastMatchMessageAnalysis.subtext.intents.includes("flirting_or_sexual")
  ) {
    defaults.flirtyValue = 70;
  } else if (memory.dateArcPhase === "planning") {
    defaults.flirtyValue = 60;
  } else if (
    lastMatchMessageAnalysis.subtext.isVulnerable ||
    lastMatchMessageAnalysis.subtext.valence < -0.3
  ) {
    defaults.flirtyValue = 30; // More supportive/less flirty
  }

  // Length Value Logic
  const avgMatchWordCount = memory.matchMessageStats?.avgWordCount || 20;
  if (lastMatchMessageAnalysis.isLowEffort) {
    defaults.lengthValue = 70; // Encourage a longer, re-engaging reply
  } else if (avgMatchWordCount > 50) {
    defaults.lengthValue = 60; // Match their longer style
  } else if (avgMatchWordCount < 15) {
    defaults.lengthValue = 40; // Match their shorter style
  }

  // Linguistic Style Logic
  if (lastMatchMessageAnalysis.subtext.isSarcastic) {
    defaults.linguisticStyle = "witty";
  } else if (
    lastMatchMessageAnalysis.subtext.intents.includes("storytelling")
  ) {
    defaults.linguisticStyle = "charming";
  }

  // End with Question Logic
  if (
    lastMatchMessageAnalysis.isDirectQuestion ||
    conversationState.startsWith("REENGAGING")
  ) {
    defaults.endWithQuestion = false; // Avoid question-for-question or needy re-engagement
  }

  // Geo Context Toggle Logic
  if (
    memory.geoContextData &&
    (memory.geoContextData.distance.miles > 100 ||
      (memory.geoContextData.timeZoneDifference &&
        memory.geoContextData.timeZoneDifference >= 2))
  ) {
    defaults.geoContextToggle = true;
  }

  DEBUG.log("DEFAULTS", "Calculated dynamic defaults", defaults);
  return defaults;
}

/**
 * Updates the memory object based on the entire conversation history.
 * @param {Message[]} conversationHistory
 * @param {MatchMemory} storedMemory
 * @returns {MatchMemory} The updated memory object.
 */
function updateMemoryFromHistory(conversationHistory, storedMemory) {
  let memory = JSON.parse(
    JSON.stringify(
      storedMemory || {
        topics: {},
        insideJokes: [],
        avoidedTopics: [],
        questionHistory: [],
        dateArcPhase: "rapport",
        userMessageStats: { total: 0, wordCount: 0, avgWordCount: 0 },
        matchMessageStats: { total: 0, wordCount: 0, avgWordCount: 0 },
      }
    )
  );

  // Reset stats before recalculating
  memory.userMessageStats = { total: 0, wordCount: 0, avgWordCount: 0 };
  memory.matchMessageStats = { total: 0, wordCount: 0, avgWordCount: 0 };

  conversationHistory.forEach((msg) => {
    const wordCount = msg.content.split(" ").length;
    if (msg.role === "user") {
      memory.userMessageStats.total++;
      memory.userMessageStats.wordCount += wordCount;
    } else {
      memory.matchMessageStats.total++;
      memory.matchMessageStats.wordCount += wordCount;
    }
  });

  memory.userMessageStats.avgWordCount =
    memory.userMessageStats.total > 0
      ? Math.round(
          memory.userMessageStats.wordCount / memory.userMessageStats.total
        )
      : 0;
  memory.matchMessageStats.avgWordCount =
    memory.matchMessageStats.total > 0
      ? Math.round(
          memory.matchMessageStats.wordCount / memory.matchMessageStats.total
        )
      : 0;

  // Topic and Joke logic
  for (let i = 0; i < conversationHistory.length - 1; i++) {
    if (
      conversationHistory[i].role === "user" &&
      conversationHistory[i + 1].role === "assistant"
    ) {
      const userDoc = nlp(conversationHistory[i].content);
      const matchDoc = nlp(conversationHistory[i + 1].content);
      const subtext = analyzeMessageSubtext(matchDoc);
      const potentialTopics = userDoc
        .nouns()
        .toSingular()
        .out("array")
        .filter((n) => n.length > 3);

      if (potentialTopics.length > 0) {
        const scoreChange = subtext.valence + subtext.arousal * 0.5;
        potentialTopics.forEach((topic) => {
          if (!memory.topics[topic]) {
            memory.topics[topic] = { score: 0, mentions: 0 };
          }
          memory.topics[topic].score += scoreChange;
          memory.topics[topic].mentions += 1;
        });
      }

      if (
        subtext.intents.includes("reacting_to_humor") &&
        subtext.valence > 0.5
      ) {
        const jokeText = userDoc
          .sentences()
          .isStatement()
          .last()
          .text("reduced");
        if (jokeText && !memory.insideJokes.includes(jokeText)) {
          memory.insideJokes.push(jokeText);
        }
      }

      if (analyzeQuestion(userDoc).isQuestion) {
        const questionText = userDoc.text("reduced");
        if (!memory.questionHistory.includes(questionText)) {
          memory.questionHistory.push(questionText);
        }
      }
    }
  }

  // Update avoided topics
  for (const topic in memory.topics) {
    if (
      memory.topics[topic].score < -1.5 &&
      !memory.avoidedTopics.includes(topic)
    ) {
      memory.avoidedTopics.push(topic);
    }
  }

  // Update Date Arc Phase
  const historySubtexts = conversationHistory.map((msg) =>
    analyzeMessageSubtext(nlp(msg.content))
  );
  const flirtSignalsInHistory = historySubtexts.filter((s) =>
    s.intents.includes("flirting_or_sexual")
  ).length;
  const logisticsSignalsInHistory = historySubtexts.filter((s) =>
    s.intents.includes("planning")
  ).length;

  if (memory.dateArcPhase === "rapport" && flirtSignalsInHistory >= 2) {
    memory.dateArcPhase = "escalation";
  }
  if (memory.dateArcPhase === "escalation" && logisticsSignalsInHistory >= 1) {
    memory.dateArcPhase = "planning";
  }

  return memory;
}

// ===================================================================================
// SECTION 3: TOP-LEVEL ORCHESTRATOR
// ===================================================================================

/**
 * @param {Message[]} conversationHistory
 * @param {MatchMemory} storedMemory
 * @returns {{analysis: object, dynamicDefaults: object}}
 */
export function runFullConversationAnalysis(conversationHistory, storedMemory) {
  DEBUG.log("ANALYSIS", "Starting full conversation analysis...");
  const updatedMemory = updateMemoryFromHistory(
    conversationHistory,
    storedMemory
  );

  const lastUserMessage = conversationHistory
    ?.filter((msg) => msg.role === "user")
    .pop();
  const lastMatchMessage = conversationHistory
    ?.filter((msg) => msg.role === "assistant")
    .pop();

  const analysis = {
    conversationState: determineConversationState(conversationHistory),
    lastUserMessageAnalysis: analyzeSingleMessage(lastUserMessage?.content),
    lastMatchMessageAnalysis: analyzeSingleMessage(lastMatchMessage?.content),
    suppressGreeting: hasRecentGreeting(conversationHistory),
    memory: updatedMemory,
  };

  const dynamicDefaults = calculateDynamicDefaults(analysis);

  DEBUG.log("ANALYSIS", "Full analysis finished.", {
    analysis,
    dynamicDefaults,
  });
  return {
    analysis,
    dynamicDefaults,
  };
}

// ===================================================================================
// SECTION 4: HELPER FUNCTIONS (Updated)
// ===================================================================================

/**
 * @param {Message[]} conversationHistory
 * @returns {ConversationState}
 */
export function determineConversationState(conversationHistory) {
  const messageCount = conversationHistory?.length || 0;
  if (messageCount === 0) {
    return "OPENER";
  }

  const lastMessage = conversationHistory[messageCount - 1];
  const daysSinceMatchReply = calculateDaysSinceMatchReply(conversationHistory);

  let state = "ACTIVE_CONVO";
  if (lastMessage.role === "user") {
    // We are waiting for them to reply
    if (daysSinceMatchReply >= 30) state = "REENGAGING_MONTH";
    else if (daysSinceMatchReply >= 7) state = "REENGAGING_WEEK";
    // FIX: Changed from >= 2 to > 1 to correctly capture a 1-day gap as per the template description.
    else if (daysSinceMatchReply > 1) state = "REENGAGING_DAY";
  }

  const matchMessageCount = conversationHistory.filter(
    (m) => m.role === "assistant"
  ).length;
  if (state === "ACTIVE_CONVO" && matchMessageCount < 5) {
    state = "EARLY_CONVO";
  }

  DEBUG.log("STATE", `Determined state: ${state}`, {
    messageCount,
    daysSinceMatchReply,
    matchMessageCount,
  });
  return state;
}

function calculateDaysSinceMatchReply(conversationHistory) {
  const lastMatchMessage = conversationHistory
    ?.filter((msg) => msg.role === "assistant")
    .pop();
  if (!lastMatchMessage || !lastMatchMessage.date) return Infinity;
  try {
    const ONE_DAY = 1000 * 60 * 60 * 24;
    return Math.floor((new Date() - new Date(lastMatchMessage.date)) / ONE_DAY);
  } catch (e) {
    return Infinity;
  }
}

/**
 * Checks if the USER has sent a greeting today.
 * @param {Message[]} conversationHistory
 * @returns {boolean}
 */
export function hasRecentGreeting(conversationHistory) {
  if (!conversationHistory || conversationHistory.length === 0) return false;

  const todayDateString = new Date().toISOString().split("T")[0];
  const GREETING_KEYWORDS = [
    "hey",
    "hi",
    "hello",
    "yo",
    "sup",
    "hiya",
    "heya",
    "howdy",
    "good morning",
    "morning",
    "'morning",
    "good afternoon",
    "afternoon",
    "good evening",
    "evening",
  ];

  return conversationHistory.some((msg) => {
    if (
      msg.role !== "user" ||
      !msg.date ||
      !msg.date.startsWith(todayDateString)
    ) {
      return false;
    }
    const firstWord = msg.content
      .trim()
      .toLowerCase()
      .split(" ")[0]
      .replace(/[.,!?-]/g, "");
    return GREETING_KEYWORDS.includes(firstWord);
  });
}

export function getToneDescription(value) {
  const levels = {
    100: "Be explicitly sexual and daring.",
    90: "Be intensely flirty and bold.",
    80: "Be very flirty and confident.",
    70: "Be flirty and playful.",
    60: "Be moderately flirty and engaging.",
    50: "Be lightly flirty and casually engaging.",
    40: "Be friendly and approachable.",
    30: "Be warm and relaxed.",
    20: "Be polite and friendly.",
    10: "Be polite and straightforward.",
    0: "Be completely neutral and formal.",
  };
  return levels[
    Object.keys(levels)
      .reverse()
      .find((k) => value >= k) || 0
  ];
}

export function getLengthDescription(value) {
  const levels = {
    100: "Strictly 8+ sentences (a manifesto).",
    90: "Strictly 6-7 sentences (epic).",
    80: "Strictly 5-6 sentences (very long).",
    70: "Strictly 4-5 sentences (long).",
    60: "Strictly 3-4 sentences (moderately long).",
    50: "Strictly 2-3 sentences (medium).",
    40: "Strictly 2 sentences (moderately short).",
    30: "Strictly 1-2 sentences (short).",
    20: "Strictly one full sentence (very short).",
    10: "Strictly 5-10 words (ultra short).",
    0: "Strictly 2-5 words (micro).",
  };
  return levels[
    Object.keys(levels)
      .reverse()
      .find((k) => value >= k) || 0
  ];
}

export function getStyleDescription(style, analysis) {
  // FIX: Removed dead code. The 'suggestedResponseStyle' property was never set in the analysis object.
  const styles = {
    witty: "Write with a witty and humorous style.",
    intellectual: "Write with an intellectual and deep style.",
    playful: "Write with a playful and teasing style.",
    direct: "Write with a direct and confident style.",
    poetic: "Write with a poetic and romantic style.",
    sexual: "Write with a bold, provocative and sexual style.",
    sarcastic: "Write with a sarcastic and sharp style.",
    charming: "Write with a charming and suave style.",
    casual: "Write with a casual and laid-back style.",
    mysterious: "Write with a mysterious and intriguing style.",
  };
  return styles[style] || "Write with a natural and conversational style.";
}

export function getEmojiInstruction(strategy, flirtyValue, linguisticStyle) {
  if (!strategy || strategy === "no_emoji") return "";
  const autoDesc = () => {
    if (["intellectual", "poetic", "sarcastic"].includes(linguisticStyle))
      return "Avoid emojis almost entirely.";
    if (flirtyValue >= 80)
      return "Feel free to use 1-3 bold or suggestive emojis (e.g., 😏, 😈, 🔥).";
    if (flirtyValue >= 60)
      return "Incorporate one or two well-placed, playful emojis (e.g., 😉, 😂, 😜).";
    if (flirtyValue >= 40)
      return "You may use a single, simple, and friendly emoji (e.g., 🙂, 👍).";
    if (["playful", "witty", "charming"].includes(linguisticStyle))
      return "You can use one well-placed emoji to add personality.";
    return "Be very conservative with emojis.";
  };
  const map = {
    auto: autoDesc(),
    friendly:
      "You may use a single, simple, and friendly emoji (e.g., 🙂, 👍).",
    playful:
      "Incorporate one or two well-placed, playful emojis (e.g., 😉, 😂).",
    bold: "Feel free to use 1-3 bold or suggestive emojis (e.g., 😏, 😈, 🔥).",
  };
  return map[strategy] || "";
}

export function getTimeContext() {
  const now = new Date();
  const day = now.getDay();
  const hour = now.getHours();
  let dayPeriod =
    hour < 5
      ? "late night"
      : hour < 8
      ? "early morning"
      : hour < 12
      ? "morning"
      : hour < 14
      ? "afternoon"
      : hour < 17
      ? "late afternoon"
      : hour < 19
      ? "evening"
      : hour < 22
      ? "late evening"
      : "night";
  const dayName = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ][day];
  if (day === 0 || day === 6 || (day === 5 && hour >= 17)) {
    return `It's the weekend, ${dayName} (${dayPeriod}). You can use a more relaxed, fun-oriented greeting.`;
  }
  return `It's a weekday, ${dayName} - ${dayPeriod}. A casual check-in about their day or a light greeting (e.g., "Happy ${dayName}!") is appropriate.`;
}

export function isMessageGeoRelated(text) {
  if (!text) return false;
  const doc = nlp(text.toLowerCase());
  if (doc.places().found) return true;
  const geoTriggers = [
    "where",
    "from",
    "at",
    "in",
    "live",
    "based",
    "travel",
    "visit",
    "trip",
    "country",
    "city",
    "town",
    "location",
    "neighborhood",
    "here",
    "there",
  ];
  return doc.has(geoTriggers);
}

function isLowEffortReply(text) {
  if (!text) return true;
  const cleanedText = text.trim().toLowerCase();
  if (cleanedText.length < 15) return true;
  const lowEffortWords = new Set([
    "ok",
    "okay",
    "k",
    "yep",
    "yup",
    "yeah",
    "lol",
    "haha",
    "cool",
    "nice",
    "thx",
    "ty",
    "np",
    "idk",
    "hbu",
    "wbu",
    "wyd",
    "nm",
    "gn",
    "gm",
    "lmao",
    "👍",
    "👌",
    "😂",
    "❤️",
    "🔥",
    "sounds good",
  ]);
  const wordsInText = cleanedText.split(/\s+/);
  return wordsInText.every((word) =>
    lowEffortWords.has(word.replace(/[.,!?-]/g, ""))
  );
}

function analyzeQuestion(doc) {
  const sentences = doc.sentences();
  if (!sentences.found) return { isQuestion: false, count: 0, type: "none" };
  const questionsWithMark = sentences.isQuestion();
  if (questionsWithMark.length > 0)
    return {
      isQuestion: true,
      count: questionsWithMark.length,
      type: "direct",
    };
  const interrogatives =
    /^(what|where|when|why|which|who|whom|whose|how|are|is|am|was|were|do|does|did|can|could|will|would|should|have|has|had|may|might|must)/i;
  for (const sentence of sentences.out("array")) {
    if (interrogatives.test(sentence.trim())) {
      return { isQuestion: true, count: 1, type: "interrogative" };
    }
  }
  return { isQuestion: false, count: 0, type: "none" };
}

function detectLogisticsSignal(doc) {
  const logisticsVerbs = [
    "get",
    "grab",
    "meet",
    "hang out",
    "do",
    "go",
    "catch",
    "make",
  ];
  const logisticsNouns = [
    "drink",
    "coffee",
    "dinner",
    "lunch",
    "sometime",
    "soon",
    "weekend",
    "tonight",
    "tomorrow",
  ];
  const logisticsQuestions = [
    "are you free",
    "when are you free",
    "what are you up to",
    "wanna get",
    "down for",
  ];
  if (doc.has(logisticsQuestions)) return true;
  if (doc.verbs().has(logisticsVerbs) && doc.nouns().has(logisticsNouns))
    return true;
  return false;
}