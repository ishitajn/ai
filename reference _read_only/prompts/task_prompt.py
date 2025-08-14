from api_models import FullUISettings
from analysis_models import FullConversationAnalysis


def get_tone_description(value: int) -> str:
    if value >= 90: return "Intensely flirty, bold, and sexually suggestive. Push the envelope."
    if value >= 70: return "Clearly flirty and playful. Use compliments and teasing."
    if value >= 50: return "Lightly flirty and casually engaging. Hint at attraction."
    if value >= 30: return "Friendly and approachable. Focus on warmth and connection."
    return "Polite and straightforward. Keep it neutral and respectful."


def get_length_description(value: int) -> str:
    if value >= 90: return "Strictly 6-7 sentences (an epic, detailed paragraph)."
    if value >= 70: return "Strictly 4-5 sentences (a long, thoughtful message)."
    if value >= 50: return "Strictly 2-3 sentences (a standard, medium-length message)."
    if value >= 30: return "Strictly 1-2 sentences (a short and punchy message)."
    return "Strictly one full sentence (a very short, concise message)."


def build_task_prompt(
        ui_settings: FullUISettings,
        analysis: FullConversationAnalysis
) -> str:
    """Builds the task-specific part of the user prompt with a clear, actionable mission."""
    goal = analysis.strategicGoal

    # --- Mission Briefing ---
    mission_header = f"--- YOUR MISSION: {goal.type.replace('_', ' ')} ---"
    mission_details = [f"**Justification:** {goal.justification}"]

    # Add specific execution instructions based on the mission
    if goal.type == "PROPOSE_DATE":
        mission_details.append(
            "**Execution:** Propose a specific, low-pressure in-person date (e.g., drinks, coffee). Connect it to a recent topic. Use a confident, assumptive tone. Example: 'So that settles it, we're getting drinks this week. Are you free Thursday or Saturday?'")
    elif goal.type == "PROPOSE_VIRTUAL_DATE":
        mission_details.append(
            "**Execution:** Propose a low-pressure video or phone call. Casually acknowledge the distance as the reason. This shows logistical awareness. Example: 'Since we're a bit far apart for a spontaneous coffee, how about we hop on a video call sometime this week instead?'")
    elif goal.type == "ESCALATE_FLIRT":
        mission_details.append(
            "**Execution:** Increase the flirt level. Use more playful teasing, direct compliments about their personality or style, and hint at attraction.")
    elif goal.type == "ESCALATE_SEXUAL_TENSION":
        mission_details.append(
            "**Execution:** Shift from playful flirting to direct, provocative communication. Use descriptive language about desire or physical attraction.")
    elif goal.type == "ENCOURAGE_INTERACTION":
        mission_details.append(
            "**Execution:** The match is giving low-effort replies. Your mission is to make it easier to give a full response than a short one. Use techniques like a playful assumption or an 'A or B' question. Avoid open-ended questions like 'How was your day?'.")
    elif goal.type == "PROVIDE_STIMULUS":
        mission_details.append(
            "**Execution:** The match is dormant. Your goal is NOT to get a reply. It is to create a positive emotional spike and then disappear. Share a funny meme, a cool link, or a quick observation. You MUST NOT ask a question. End with a phrase like 'Just a random thought' or 'Have a good one'.")
    elif goal.type == "MAINTAIN_FRAME":
        mission_details.append(
            "**Execution:** You must pass a confidence test. Do NOT be defensive. Use the 'Agree and Amplify' technique. Exaggerate their accusation to the point of absurdity, with a playful tone. Example: If they say 'Are you a player?', you say 'Yes, I'm the regional champion. The trophy is in the mail.'")
    elif goal.type == "APPLY_PUSH_PULL":
        mission_details.append(
            "**Execution:** Construct a 'Push-Pull' message. Start with a compliment (the 'Pull'), then immediately follow it with a playful tease or challenge (the 'Push'). Example: 'You have an amazing sense of style (Pull), I'm guessing your closet is a disaster zone though (Push).'")
    elif goal.type == "BUILD_RAPPORT":
        mission_details.append(
            "**Execution:** Focus on the topics marked '✅ Keep' or '❤️ Flirtatious' in the landscape. Share a personal anecdote or ask a thoughtful follow-up question to deepen the connection.")

    mission_section = f"{mission_header}\n" + "\n".join(mission_details)

    # --- User Directives (These are constraints for the mission) ---
    directives = [
        f"- **TONE (Flirt Level: {ui_settings.flirtyValue}/100):** {get_tone_description(ui_settings.flirtyValue)}",
        f"- **LENGTH (Length Level: {ui_settings.lengthValue}/100):** {get_length_description(ui_settings.lengthValue)}",
        f"- **LINGUISTIC STYLE:** Use a {ui_settings.linguisticStyle} style.",
        f"- **HUMOR STYLE:** Use {ui_settings.humorStyle} humor.",
        f"- **EMOJI USAGE:** Use emojis according to the '{ui_settings.emojiStrategy}' strategy.",
        f"- **CONVERSATIONAL GOAL:** {'Conclude with an engaging, open-ended question.' if ui_settings.endWithQuestion else 'Avoid ending with a direct question. Statements or observations are preferred.'}"
    ]
    if ui_settings.customInstruction:
        directives.append(f"- **ABSOLUTE PRIORITY – USER'S INSTRUCTION:** {ui_settings.customInstruction}")

    directives_section = f"--- DIRECTIVES (Constraints & Style) ---\n" + "\n".join(directives)

    final_command = (
        "--- FINAL COMMAND ---\n"
        "Execute your MISSION based on all the context and within the given DIRECTIVES. "
        "Return ONLY the raw text of the message. Do not include labels, quotes, or any extra formatting."
    )

    return f"{mission_section}\n\n{directives_section}\n\n{final_command}"