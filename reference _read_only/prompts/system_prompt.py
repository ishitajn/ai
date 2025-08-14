from analysis_models import FullConversationAnalysis
from api_models import FullUISettings
from . import personas

def get_system_prompt(analysis: FullConversationAnalysis, ui_settings: FullUISettings) -> str:
    """Builds the system prompt with core rules and highly dynamic, analysis-driven guidelines."""
    core_prompt = (
        "You are DateWing, an AI ghostwriter specializing in crafting compelling, human-like dating app messages.\n\n"
        "**--- CORE RULES ---**\n"
        "1. **PERSPECTIVE:** Write from the user's perspective (typically male) to their match (typically female).\n"
        "2. **PRIMARY DIRECTIVE:** You MUST strictly follow all instructions, constraints, and goals provided in the user's prompt under 'YOUR MISSION'. This is your highest priority.\n"
        "3. **AUTHENTICITY:** Generate text that feels genuine and personal. Avoid clichés and generic compliments."
    )
    persona_prompt = personas.get_persona_prompt(ui_settings.persona)
    dynamic_guidelines = _build_dynamic_guidelines(analysis)
    return "\n\n".join(filter(None, [core_prompt, persona_prompt, dynamic_guidelines]))

def _build_dynamic_guidelines(analysis: FullConversationAnalysis) -> str:
    """Generates real-time advice based on deep conversational analysis."""
    guidelines = []
    last_match = analysis.lastMatchMessageAnalysis
    if last_match:
        if last_match.subtext.isVulnerable:
            guidelines.append('* **BE SUPPORTIVE:** Their last message was vulnerable. Respond with warmth and validation.')
        if last_match.subtext.valence < -0.3:
            guidelines.append(f'* **EMPATHIZE:** They seem to be feeling negative. Acknowledge their feelings with empathy.')
    if analysis.memory.dateArcPhase == 'planning':
        guidelines.append('* **SOLIDIFY PLANS:** The goal is to set a date. Be direct and confident about logistics.')
    return f"**--- DYNAMIC GUIDELINES (Situational Intel) ---**\n{'\n'.join(guidelines)}" if guidelines else ""