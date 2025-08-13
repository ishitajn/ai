# tests/test_prompt_service.py

import pytest
from services import prompt_service
from api_models import ScrapedData, FullUISettings, PromptGenerationResponse
from analysis_models import FullConversationAnalysis, MatchMemory, StrategicGoal

def test_generate_prompts_includes_token_count():
    """
    Tests that the generate_prompts function correctly calculates and includes
    a token_count in its response.
    """
    # 1. Create minimal mock data required for the function to run
    mock_analysis = FullConversationAnalysis(
        conversationState="ACTIVE_CONVO",
        conversationPacing="normal",
        strategicGoal=StrategicGoal(type="BUILD_RAPPORT", justification="test", urgency="normal"),
        memory=MatchMemory()
    )
    mock_scraped_data = ScrapedData(
        theirProfile="Test profile",
        conversationHistory=[]
    )
    mock_ui_settings = FullUISettings(
        myLocation="Test City",
        myProfile="My test profile",
        local_model_name="test-model"
    )

    # 2. Call the function
    response = prompt_service.generate_prompts(
        analysis=mock_analysis,
        scraped_data=mock_scraped_data,
        ui_settings=mock_ui_settings
    )

    # 3. Assert the response is correct
    assert isinstance(response, PromptGenerationResponse)

    # Check that token_count is present and is a plausible integer
    assert response.token_count is not None
    assert isinstance(response.token_count, int)
    assert response.token_count > 0

    # Sanity check: token count should be roughly related to text length
    total_text_length = len(response.system_prompt) + len(response.user_prompt)
    # A common rule of thumb is ~4 chars per token. We'll give a wide berth.
    assert response.token_count > total_text_length / 10
    assert response.token_count < total_text_length
