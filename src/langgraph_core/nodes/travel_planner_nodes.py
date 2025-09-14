from src.langgraph_core.state.travel_planner_states import TravelPlannerState
from langchain_core.messages import AIMessage, HumanMessage
from uuid import uuid4
from src.langgraph_core.tools.custom_tools import weather_tool
from src.langgraph_core.tools.tools import get_tools


class TravelPlannerNode:
    def __init__(self, llm):
        self.llm = llm
        self.weather_tool_name = weather_tool.name
        self.search_tool_name = get_tools()[0].name

    def router(self, state: TravelPlannerState) -> dict:
        """
        Decide which route (weather, search, or chat) the query should take.
        If weather/search -> inject AIMessage with tool_call right here.
        """
        # print("Route node being called")

        if not state.get("messages"):
            return {"route": "chat", "messages": [AIMessage(content="I didn’t receive any input.")]}

        last_msg = state["messages"][-1]

        # Only process if it's HumanMessage
        if not isinstance(last_msg, HumanMessage):
            return {"route": "chat", "messages": state["messages"]}

        user_input = last_msg.content.lower()

        if any(k in user_input for k in ["weather", "temp", "temperature", "hot", "cold"]):
            city = (
                user_input.replace("temp in", "")
                .replace("weather in", "")
                .strip()
                or "pune"
            )
            ai_msg = AIMessage(
                content="Let me check the weather for you...",
                tool_calls=[{"id": str(uuid4()), "name": self.weather_tool_name, "args": {"city_name": city}}],
            )
            return {"route": "weather", "messages": state["messages"] + [ai_msg]}

        elif any(k in user_input for k in ["search", "google", "find", "lookup"]):
            query = user_input.replace("search", "").replace("google", "").strip()
            ai_msg = AIMessage(
                content=f"Searching for {query}...",
                tool_calls=[{"id": str(uuid4()), "name": self.search_tool_name, "args": {"query": query}}],
            )
            return {"route": "search", "messages": state["messages"] + [ai_msg]}

        else:
            return {"route": "chat", "messages": state["messages"]}

    def chat_node(self, state: TravelPlannerState, llm):
        """
        Pure chat node for normal LLM conversation.
        No tool logic here.
        """
        if not state["messages"]:
            return {"messages": [AIMessage(content="I didn’t receive any input.")]}

        last_msg = state["messages"][-1]

        # Ignore AIMessage (only handle HumanMessage)
        if not isinstance(last_msg, HumanMessage):
            return {"messages": state["messages"]}

        # print("Chat_node being called:", last_msg.content)
        # print("🔥 Current State:", state)

        response = llm.invoke([last_msg])
        return {"messages": state["messages"] + [response]}
