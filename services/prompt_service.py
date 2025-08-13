import tiktoken
from typing import Tuple
from api_models import ScrapedData, FullUISettings, PromptGenerationResponse
from analysis_models import FullConversationAnalysis
from prompts import system_prompt, context_prompt, task_prompt

def generate_prompts(
        analysis: FullConversationAnalysis,
        scraped_data: ScrapedData,
        ui_settings: FullUISettings
) -> PromptGenerationResponse:
    """
    Orchestrates the creation of system and user prompts using the deep analysis.
    Also calculates the token count of the final prompts.
    """
    system_message = system_prompt.get_system_prompt(analysis, ui_settings)

    context_message = context_prompt.build_context_prompt(
        scraped_data, analysis, ui_settings
    )

    task_message = task_prompt.build_task_prompt(
        ui_settings, analysis
    )

    user_message = f"{context_message}\n\n{task_message}"

    # Calculate token count
    try:
        # Using cl100k_base encoding, which is standard for gpt-4, gpt-3.5-turbo, etc.
        encoding = tiktoken.get_encoding("cl100k_base")
        system_tokens = len(encoding.encode(system_message))
        user_tokens = len(encoding.encode(user_message))
        total_tokens = system_tokens + user_tokens
    except Exception:
        # If tiktoken fails for any reason, we don't want to block the request.
        total_tokens = None

    return PromptGenerationResponse(
        system_prompt=system_message,
        user_prompt=user_message,
        model_name=ui_settings.local_model_name,
        temperature=ui_settings.modelTemperature,
        top_p=ui_settings.topPValue,
        token_count=total_tokens
    )