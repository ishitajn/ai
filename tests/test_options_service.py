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
    assert len(options) > 0
    for group in options:
        assert isinstance(group, ParameterGroup)
        assert isinstance(group.parameters, list)

def test_slider_parameter_constraints():
    """
    Tests the constraints of a specific slider parameter to ensure correctness.
    """
    options = generate_all_options()
    ui_controls_group = next((g for g in options if g.groupName == "UI Controls"), None)
    assert ui_controls_group is not None

    flirty_value = next((p for p in ui_controls_group.parameters if p.name == "flirtyValue"), None)
    assert flirty_value is not None
    assert isinstance(flirty_value, SliderParameter)
    assert flirty_value.uiType == "slider"
    assert flirty_value.valueType == "integer"
    assert flirty_value.constraints.min == 0
    assert flirty_value.constraints.max == 100
    assert flirty_value.constraints.step == 1

def test_dropdown_dynamic_values():
    """
    Tests that dropdown values are dynamically loaded from the constants file.
    """
    options = generate_all_options()
    ui_controls_group = next((g for g in options if g.groupName == "UI Controls"), None)
    assert ui_controls_group is not None

    linguistic_style = next((p for p in ui_controls_group.parameters if p.name == "linguisticStyle"), None)
    assert linguistic_style is not None
    assert isinstance(linguistic_style, DropdownParameter)

    # Check that the number of options matches the source of truth
    assert len(linguistic_style.constraints.allowedValues) == len(constants.LINGUISTIC_STYLES)

    # Check that one of the values from the source of truth is present in the generated options
    expected_value = constants.LINGUISTIC_STYLES[1] # e.g., "casual"
    assert any(opt.value == expected_value for opt in linguistic_style.constraints.allowedValues)
