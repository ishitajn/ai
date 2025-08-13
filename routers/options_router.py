from fastapi import APIRouter
from typing import List
from services.options_service import generate_all_options, ParameterGroup

router = APIRouter(
    prefix="/api/v1/options",
    tags=["Configuration Options"],
)

@router.get("/all", response_model=List[ParameterGroup])
async def get_all_options():
    """
    Returns a comprehensive, categorized list of all selectable options and
    parameters supported by the backend for dynamic UI generation.
    """
    return generate_all_options()