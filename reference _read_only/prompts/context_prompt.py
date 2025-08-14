from collections import defaultdict
from api_models import ScrapedData, FullUISettings
from analysis_models import FullConversationAnalysis, MatchMemory
from . import templates
from config import MAX_HISTORY_MESSAGES_IN_PROMPT

def build_context_prompt(
        scraped_data: ScrapedData,
        analysis: FullConversationAnalysis,
        ui_settings: FullUISettings
) -> str:
    """
    Builds the complete context section of the user prompt, including the strategic
    memory summary, conversation history, and profile information.
    """
    memory_section = _build_memory_summary(analysis.memory)

    history_section = ""
    if analysis.conversationState != 'OPENER' and scraped_data.conversationHistory:
        history_section = _build_history_section(
            scraped_data.conversationHistory,
            analysis,
            scraped_data.myName,
            scraped_data.theirName
        )

    profile_section = _build_profile_section(
        analysis.conversationState,
        scraped_data.theirProfile,
        ui_settings.myProfile,
        scraped_data.myName,
        scraped_data.theirName
    )

    return "\n\n".join(filter(None, [memory_section, history_section, profile_section]))

def _build_memory_summary(memory: MatchMemory) -> str:
    """Creates a rich, categorized summary of the conversational landscape for the LLM."""
    if not memory.topics and not memory.keyFacts:
        return ""

    categorized_topics = defaultdict(list)
    for topic, details in memory.topics.items():
        if details.status != 'avoid':
            topic_str = f"{topic} (Sent: {details.avg_sentiment:.2f})"
            categorized_topics[details.category].append(topic_str)

    category_map = {
        "sexual": "🔥 Sexual Topics",
        "flirtatious": "❤️ Flirtatious & Complimentary Topics",
        "vulnerable": "🧠 Deep & Vulnerable Topics",
        "planning": "📅 Logistics & Planning",
        "professional": "💼 Professional & Work Topics",
        "geo-context": "🌍 Location & Travel Topics",
        "general_interest": "💬 General Interests & Hobbies"
    }

    summary_points = []
    for category, header in category_map.items():
        if category in categorized_topics:
            topics_list_str = ", ".join(categorized_topics[category])
            summary_points.append(f"- **{header}:** {topics_list_str}")
            
    avoid_topics = [f"{t} (Sent: {d.avg_sentiment:.2f})" for t, d in memory.topics.items() if d.status == 'avoid']
    if avoid_topics:
        summary_points.append(f"- ⚠️ **Sensitive/Avoid Topics:** {', '.join(avoid_topics)}")

    if memory.keyFacts:
        facts = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in memory.keyFacts.items())
        summary_points.append(f"- 📌 **Key Facts Learned:** {facts}")
    
    summary_points.append(f"- 📈 **Vitals:** Rapport: {memory.rapportScore:.2f}/1.0 | Investment: {memory.investmentScore:.2f} | Sexual Tension: {memory.sexualTension:.2f}")

    summary_text = "\n".join(summary_points)
    return f"{templates.SECTION_HEADER('CONVERSATIONAL LANDSCAPE & STRATEGY')}\n{summary_text}"

def _build_history_section(history, analysis, my_name, their_name) -> str:
    """Builds the conversation history, adding critical notices and truncating if necessary."""
    notices = []
    if analysis.lastMatchMessageAnalysis and analysis.lastMatchMessageAnalysis.questionInfo.isQuestion:
        q_type = analysis.lastMatchMessageAnalysis.questionInfo.type
        notices.append(templates.CRITICAL_NOTICE(f"The match's last message is a {q_type} question. You MUST address it."))
    
    history_to_show = history
    if len(history) > MAX_HISTORY_MESSAGES_IN_PROMPT:
        notices.append(templates.CRITICAL_NOTICE(f"History is long. Showing last {MAX_HISTORY_MESSAGES_IN_PROMPT} messages for immediate context."))
        history_to_show = history[-MAX_HISTORY_MESSAGES_IN_PROMPT:]

    formatted_messages = "\n".join(
        templates.MESSAGE_FORMAT(msg.date, their_name if msg.role == 'assistant' else my_name, msg.content)
        for msg in history_to_show
    )
    notice_text = "\n".join(notices) + "\n" if notices else ""

    return f"{templates.SECTION_HEADER('RECENT CONVERSATION HISTORY')}\n{notice_text}{formatted_messages}"

def _build_profile_section(state, their_profile, my_profile, my_name, their_name) -> str:
    """Builds the profile context section with dynamic headers based on state."""
    header = "PROFILE CONTEXT"
    if state == 'OPENER':
        header = "PROFILE CONTEXT (Primary Source for Opener)"
    elif state == 'ACTIVE_CONVO':
        header = "PROFILE CONTEXT (Secondary Reference for New Topics)"

    their_profile_text = f"**{their_name.upper()}'S PROFILE:** {their_profile or 'Not provided.'}"
    my_profile_text = f"**{my_name.upper()}'S PROFILE (Your Persona):** {my_profile or 'Not provided.'}"

    return f"{templates.SECTION_HEADER(header)}\n{their_profile_text}\n\n{my_profile_text}"