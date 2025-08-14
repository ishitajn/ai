# tests/test_options_service.py

import pytest
from services.options_service import generate_all_options, ParameterGroup, SliderParameter, DropdownParameter
from utils import constants

def test_generate_all_options_structure():
    """
    Tests that the main generator function returns a list of ParameterGroup objects.
    """
    options = generate_all_options()
    assert isinstance(options, list)
    assert len(options) > 0, "Should return at least one parameter group"
    for group in options:
        assert isinstance(group, ParameterGroup)
        assert isinstance(group.parameters, list)

def test_flirty_value_is_dropdown():
    """
    Tests that the 'flirtyValue' parameter is correctly refactored to a dropdown
    with categorical options.
    """
    options = generate_all_options()
    core_controls_group = next((g for g in options if g.groupName == "Core Controls"), None)
    assert core_controls_group is not None, "Core Controls group not found"

    flirty_value = next((p for p in core_controls_group.parameters if p.name == "flirtyValue"), None)

    assert flirty_value is not None, "'flirtyValue' parameter not found"
    assert isinstance(flirty_value, DropdownParameter), "flirtyValue should be a DropdownParameter"
    assert flirty_value.uiType == "dropdown"
    assert flirty_value.displayName == "Flirtiness"
    assert len(flirty_value.constraints.allowedValues) == 5
    assert flirty_value.constraints.allowedValues[2].value == 50
    assert "Lightly flirty" in flirty_value.constraints.allowedValues[2].description

def test_dropdown_dynamic_values():
    """
    Tests that a dropdown's values are dynamically loaded from the constants file.
    """
    options = generate_all_options()
    style_group = next((g for g in options if g.groupName == "Style & Voice"), None)
    assert style_group is not None, "Style & Voice group not found"

    humor_style = next((p for p in style_group.parameters if p.name == "humorStyle"), None)

    assert humor_style is not None, "'humorStyle' parameter not found"
    assert isinstance(humor_style, DropdownParameter)
    assert humor_style.displayName == "Humor Style"

    # Check that the number of options matches the source of truth in constants
    assert len(humor_style.constraints.allowedValues) == len(constants.HUMOR_STYLES)

    # Check that one of the values from the source of truth is present
    expected_value = constants.HUMOR_STYLES[1] # e.g., "witty"
    assert any(opt.value == expected_value for opt in humor_style.constraints.allowedValues)

def test_advanced_slider_parameter():
    """
    Tests a slider from the 'Advanced & Debug' group for correct properties.
    """
    options = generate_all_options()
    advanced_group = next((g for g in options if g.groupName == "Advanced & Debug"), None)
    assert advanced_group is not None, "Advanced & Debug group not found"

    temp_param = next((p for p in advanced_group.parameters if p.name == "modelTemperature"), None)

    assert temp_param is not None, "'modelTemperature' not found in advanced group"
    assert isinstance(temp_param, SliderParameter)
    assert temp_param.displayName == "Model Temperature"
    assert temp_param.constraints.min == 0.1
    assert temp_param.constraints.max == 1.5
    assert temp_param.constraints.step == 0.05

def test_strategy_mode_dropdown():
    """
    Tests that the new 'strategyMode' dropdown is present and correct.
    """
    options = generate_all_options()
    core_controls_group = next((g for g in options if g.groupName == "Core Controls"), None)
    assert core_controls_group is not None, "Core Controls group not found"

    strategy_mode = next((p for p in core_controls_group.parameters if p.name == "strategyMode"), None)

    assert strategy_mode is not None, "'strategyMode' parameter not found"
    assert isinstance(strategy_mode, DropdownParameter)
    assert strategy_mode.displayName == "Strategy Mode"
    assert len(strategy_mode.constraints.allowedValues) == len(constants.STRATEGY_MODES)
    assert strategy_mode.constraints.allowedValues[1].value == "Balanced"
