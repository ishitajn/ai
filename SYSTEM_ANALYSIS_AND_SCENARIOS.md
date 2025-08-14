# System Analysis & Prompt Scenarios

This document provides an exhaustive breakdown of the application's analytical capabilities, the decision-making logic, and the resulting prompt generation scenarios.

***

## Part 1: Core Analysis Metrics

The system analyzes a conversation by calculating several key metrics. These metrics form the foundation for all subsequent strategic decisions.

### 1.1. Per-Message Analysis

Each individual message is analyzed to extract its subtext and characteristics.

*   **`subtext.valence` (Sentiment Score)**
    *   **Description:** A float between -1.0 (very negative) and 1.0 (very positive) representing the emotional sentiment of the message.
    *   **Calculation:** Calculated by summing the sentiment scores of words from `POSITIVE_WORDS` and `NEGATIVE_WORDS` in `utils/constants.py`. The score is modified by `INTENSIFIERS` (e.g., "very") and `NEGATION_WORDS` (e.g., "not").

*   **`subtext.arousal` (Energy Level)**
    *   **Description:** A float between -1.0 (very low energy, e.g., "tired", "bored") and 1.0 (very high energy, e.g., "omg!", "crazy").
    *   **Calculation:** Calculated by summing the scores of words from the `AROUSAL_WORDS` list.

*   **`subtext.intents` (Detected Intentions)**
    *   **Description:** A list of detected intentions within the message.
    *   **Possible Values:**
        *   `"planning"`: Identified if the message contains words from the `PLANNING_WORDS` list (e.g., "when", "drinks", "schedule").
        *   `"flirting_or_sexual"`: Identified if the message contains words from the `SEXUAL_WORDS` list or emojis from the `SEXUAL_EMOJIS` regex.
    *   **Effect:** The "flirting_or_sexual" intent directly boosts the message's valence and arousal scores.

*   **`subtext.isVulnerable` (Vulnerability Flag)**
    *   **Description:** A boolean flag that is `true` if the message contains phrases indicating vulnerability or self-disclosure.
    *   **Calculation:** Based on the `VULNERABLE_WORDS` list (e.g., "to be honest", "i feel like", "i'm nervous").

*   **`questionInfo` (Question Analysis)**
    *   **Description:** An object that determines if a message is a question and what type it is.
    *   **Properties:**
        *   `isQuestion` (boolean): `true` if a question is detected.
        *   `type` (string): "open", "closed", or "indirect".
    *   **Calculation:** A message is a "direct" question if it ends with `?`. It is classified as "open" if the first word is a "Wh-" word (What, When, Why, etc.) and "closed" otherwise. It is "indirect" if it starts with phrases from `INDIRECT_QUESTION_STARTERS` (e.g., "i was wondering").

*   **`isLowEffort` (Low-Effort Flag)**
    *   **Description:** A boolean flag that is `true` if the message is considered a low-effort reply.
    *   **Calculation:** Based on the `LOW_EFFORT_WORDS` list (e.g., "lol", "ok", "cool", "k").

### 1.2. Overall Conversation Metrics (The "Memory" Object)

These metrics are calculated by aggregating the per-message analyses over the entire conversation history.

*   **`investmentScore`**
    *   **Description:** A score from -1.0 to 1.0 representing the other person's perceived investment in the conversation.
    *   **Calculation:** This score decays over time (by `INVESTMENT_SCORE_DECAY_FACTOR`) and is adjusted based on a turn-by-turn analysis. It increases if the match asks a question or matches the user's message length. It decreases if they ignore a question, give a low-effort reply, or write a much shorter message.

*   **`rapportScore`**
    *   **Description:** A score from 0.0 to 1.0 representing the overall positive feeling and connection.
    *   **Calculation:** Primarily based on the average sentiment (`valence`) of the match's messages over the conversation. It also receives a small bonus for longer conversations.

*   **`sexualTension`**
    *   **Description:** A score from 0.0 to 1.0 representing the level of sexual chemistry.
    *   **Calculation:** This score decays over time (by `SEXUAL_TENSION_DECAY_FACTOR`). It increases each time the match sends a message with "flirting_or_sexual" intent. It is heavily penalized if the user makes a sexual advance and the match's response has a strong negative sentiment.

*   **`engagementState`**
    *   **Description:** A state describing the overall health of the conversation.
    *   **Possible Values:** "ACTIVE", "LUKEWARM", "DORMANT".
    *   **Calculation:** Determined by comparing the `investmentScore` to the `DORMANT_INVESTMENT_THRESHOLD` and `LUKEWARM_INVESTMENT_THRESHOLD`.

*   **`conversationPacing`**
    *   **Description:** A state describing the speed of replies.
    *   **Possible Values:** "fast" (< 1 hour between replies), "stalled" (> 48 hours), or "normal".
    *   **Calculation:** Based on the time since the last message in the history.

***

## Part 2: Strategic Goal Determination (The Decision Engine)

The system uses the metrics from Part 1 to select a single `StrategicGoal`. This decision is the core of the AI's "brain". The logic is a prioritized decision tree that checks conditions in order.

*   **Decision 1: Was a "Shit Test" Detected?**
    *   **Condition:** The last message from the match contains a phrase matching a pattern in `SHIT_TEST_PATTERNS` (e.g., "are you a player?").
    *   **Resulting Goal:** `MAINTAIN_FRAME`. This goal has the highest priority.

*   **Decision 2: Is the Conversation Dormant?**
    *   **Condition:** The `engagementState` is "DORMANT".
    *   **Resulting Goal:** `PROVIDE_STIMULUS`.

*   **Decision 3: Is the Conversation Lukewarm?**
    *   **Condition:** The `engagementState` is "LUKEWARM".
    *   **Resulting Goal:** `ENCOURAGE_INTERACTION`.

*   **Decision 4: Are We Planning a Date?**
    *   **Condition:** The `dateArcPhase` (a state tracker) is currently "planning".
    *   **Resulting Goal:** `HANDLE_LOGISTICS`.

*   **Decision 5: Is it Time to "Make the Ask"?**
    *   **Condition:** The `rapportScore` and `investmentScore` are both above the dynamic thresholds set by the `strategyMode` (e.g., `ask_rapport` and `ask_investment`).
    *   **Sub-Decision (based on `ultimateGoal`):**
        *   If goal is `Sexual_Encounter` and `sexualTension` is high -> `PROPOSE_ENCOUNTER`.
        *   If goal is `Sexual_Encounter` but `sexualTension` is not yet high -> `ESCALATE_SEXUAL_TENSION`.
        *   If goal is `Date` and it's long distance -> `PROPOSE_VIRTUAL_DATE`.
        *   If goal is `Date` and it's local -> `PROPOSE_DATE`.

*   **Decision 6: Is it Time to Escalate?**
    *   **Condition:** The `rapportScore` and `investmentScore` are both above the dynamic `escalate` thresholds.
    *   **Sub-Decision (probabilistic):**
        *   There is a random chance (determined by `push_pull_probability`) to select the `APPLY_PUSH_PULL` goal.
        *   Otherwise, the goal is `ESCALATE_FLIRT`. The `dateArcPhase` is also updated to "escalation".

*   **Decision 7: Default Action**
    *   **Condition:** If none of the above conditions are met.
    *   **Resulting Goal:** `BUILD_RAPPORT`.

***

## Part 3: Prompt Scenarios (The Missions)

Each `StrategicGoal` selected in Part 2 maps directly to a "mission" provided to the LLM in `prompts/task_prompt.py`. The LLM is given explicit execution instructions for each scenario.

*   **Mission: `BUILD_RAPPORT`**
    *   **Instruction:** "Focus on the topics marked '✅ Keep' or '❤️ Flirtatious' in the landscape. Share a personal anecdote or ask a thoughtful follow-up question to deepen the connection."

*   **Mission: `ESCALATE_FLIRT`**
    *   **Instruction:** "Increase the flirt level. Use more playful teasing, direct compliments about their personality or style, and hint at attraction."

*   **Mission: `ESCALATE_SEXUAL_TENSION`**
    *   **Instruction:** "Shift from playful flirting to direct, provocative communication. Use descriptive language about desire or physical attraction."

*   **Mission: `PROPOSE_DATE`**
    *   **Instruction:** "Propose a specific, low-pressure in-person date (e.g., drinks, coffee). Connect it to a recent topic. Use a confident, assumptive tone. Example: 'So that settles it, we're getting drinks this week. Are you free Thursday or Saturday?'"

*   **Mission: `PROPOSE_VIRTUAL_DATE`**
    *   **Instruction:** "Propose a low-pressure video or phone call. Casually acknowledge the distance as the reason. This shows logistical awareness. Example: 'Since we're a bit far apart for a spontaneous coffee, how about we hop on a video call sometime this week instead?'"

*   **Mission: `PROPOSE_ENCOUNTER`**
    *   **Instruction:** "Sexual tension and investment are very high. Propose an encounter."

*   **Mission: `ENCOURAGE_INTERACTION`**
    *   **Instruction:** "The match is giving low-effort replies. Your mission is to make it easier to give a full response than a short one. Use techniques like a playful assumption or an 'A or B' question. Avoid open-ended questions like 'How was your day?'."

*   **Mission: `PROVIDE_STIMULUS`**
    *   **Instruction:** "The match is dormant. Your goal is NOT to get a reply. It is to create a positive emotional spike and then disappear. Share a funny meme, a cool link, or a quick observation. You MUST NOT ask a question. End with a phrase like 'Just a random thought' or 'Have a good one'."

*   **Mission: `MAINTAIN_FRAME`**
    *   **Instruction:** "You must pass a confidence test. Do NOT be defensive. Use the 'Agree and Amplify' technique. Exaggerate their accusation to the point of absurdity, with a playful tone. Example: If they say 'Are you a player?', you say 'Yes, I'm the regional champion. The trophy is in the mail.'"

*   **Mission: `APPLY_PUSH_PULL`**
    *   **Instruction:** "Construct a 'Push-Pull' message. Start with a compliment (the 'Pull'), then immediately follow it with a playful tease or challenge (the 'Push'). Example: 'You have an amazing sense of style (Pull), I'm guessing your closet is a disaster zone though (Push).'"

*   **Mission: `HANDLE_LOGISTICS`**
    *   **Instruction:** "A date is being planned. Focus on confirming details."
