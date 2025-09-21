from typing_extensions import TypedDict, List, Optional
from langgraph.graph.message import add_messages
from typing import Annotated
from datetime import date


class TravelPlannerState(TypedDict):
    """Travel planner state with user input + extracted details."""
    messages: Annotated[List, add_messages]
    last_user_message: str
    destination: Optional[str]
    source: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    duration: Optional[int]
    flight_type: Optional[str]




