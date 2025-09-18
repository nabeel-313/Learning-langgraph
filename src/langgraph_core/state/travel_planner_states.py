from typing_extensions import TypedDict, List
from langgraph.graph.message import add_messages
from typing import Annotated

class TravelPlannerState(TypedDict):
    """A basic chatbot with a simple conversation flow."""

    messages: Annotated[List, add_messages]
    last_user_message: str   # <-- NEW FIELD to track original input
