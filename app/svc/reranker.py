from app.schemas import Suggestions
from typing import List

MAX_SUGGESTIONS_PER_LIST = 2

def enforce_constraints(suggestions: Suggestions) -> Suggestions:
    """
    Caps suggestions to a max of 2 items per list and removes duplicates.

    It iterates over all lists within the Suggestions object and applies
    the constraints.
    """

    # Get all fields from the dataclass that are lists
    for field_name in suggestions.__dataclass_fields__:
        suggestion_list = getattr(suggestions, field_name)

        if isinstance(suggestion_list, list):
            # 1. Remove duplicates while preserving original order
            # dict.fromkeys creates a dictionary with unique keys from the list
            unique_suggestions = list(dict.fromkeys(suggestion_list))

            # 2. Cap the list to the maximum allowed number
            capped_suggestions = unique_suggestions[:MAX_SUGGESTIONS_PER_LIST]

            # 3. Update the field in the suggestions object
            setattr(suggestions, field_name, capped_suggestions)

    return suggestions
