# tests/test_strategy_service.py

import pytest
from services.analysis_service import _determine_strategic_goal, _get_strategy_thresholds
from api_models import FullUISettings
from analysis_models import MatchMemory, StrategicGoal

@pytest.fixture
def base_ui_settings():
    """Returns a base FullUISettings object for tests."""
    return FullUISettings(
        myLocation="Test City",
        myProfile="My test profile",
        local_model_name="test-model"
    )

def test_aggressive_strategy_escalates_sooner(base_ui_settings):
    """
    Tests that the 'Aggressive' strategy mode suggests escalation at lower
    thresholds than the 'Patient' mode.
    """
    # 1. Define memory state that is right on the edge of escalation
    # These scores are high enough for 'Aggressive' but not for 'Patient'
    thresholds = _get_strategy_thresholds("Aggressive")
    memory = MatchMemory(
        rapportScore=thresholds['escalate_rapport'] + 0.01,
        investmentScore=thresholds['escalate_investment'] + 0.01
    )

    # 2. Test with Aggressive mode
    aggressive_settings = base_ui_settings.model_copy()
    aggressive_settings.strategyMode = "Aggressive"

    aggressive_goal = _determine_strategic_goal(memory, last_match_msg=None, ui_settings=aggressive_settings)

    # With aggressive settings, it should decide to escalate
    assert aggressive_goal.type in ["ESCALATE_FLIRT", "APPLY_PUSH_PULL"]

    # 3. Test with Patient mode
    patient_settings = base_ui_settings.model_copy()
    patient_settings.strategyMode = "Patient"

    patient_goal = _determine_strategic_goal(memory, last_match_msg=None, ui_settings=patient_settings)

    # With the same scores, patient settings should not escalate and default to building rapport
    assert patient_goal.type == "BUILD_RAPPORT"
