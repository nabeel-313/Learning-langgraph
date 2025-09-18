from src.langgraph_core.state.travel_planner_states import TravelPlannerState
from langchain_core.messages import AIMessage, HumanMessage
from uuid import uuid4
from src.langgraph_core.tools.custom_tools import weather_tool
from src.langgraph_core.tools.tools import get_tools
from src.utils.Utilities import TravelInfo


class TravelPlannerNode:
    def __init__(self, llm):
        self.llm = llm
        self.weather_tool_name = weather_tool.name
        self.search_tool_name = get_tools()[0].name

    def router(self, state: TravelPlannerState) -> dict:
        if not state.get("messages"):
            return {
                "route": "chat",
                "messages": [AIMessage(content="I didn’t receive any input.")],
                "last_user_message": ""  # <-- ensure state key always exists
            }
        last_msg = state["messages"][-1]
        if not isinstance(last_msg, HumanMessage):
            return {
                "route": "chat",
                "messages": state["messages"],
                "last_user_message": state.get("last_user_message", "")
            }

        user_input = last_msg.content
        # LLM prompt for routing
        routing_prompt = f"""
        You are an intent classifier. Decide the route for this user message:
        Options: 'chat', 'weather', 'search', 'travel'.
        Respond with one of the three words ONLY.

        User message: "{user_input}"
        """
        route_response = self.llm.invoke([
            HumanMessage(content=routing_prompt)
            ])
        route = route_response.content.strip().lower()

        if route not in ["weather", "search"]:
            route = "chat"

        messages = state["messages"]

        # Tool call injection for weather
        if route == "weather":
            city_prompt = f"""
            Extract the city/location name from this user message for
            weather lookup.If none found, default to 'pune'.
            Respond with city name only.
            Message: "{user_input}"
            """
            city_response = self.llm.invoke([
                HumanMessage(content=city_prompt)
                ])
            city = city_response.content.strip() or "pune"

            ai_msg = AIMessage(
                content="Let me check the weather for you...",
                tool_calls=[{
                    "id": str(uuid4()),
                    "name": self.weather_tool_name,
                    "args": {"city_name": city}
                }],
            )
            messages = messages + [ai_msg]

        elif route == "search":
            query_prompt = f"""
            Extract the search query from this user message.
            Respond with query text only.
            Message: "{user_input}"
            """
            query_response = self.llm.invoke([
                HumanMessage(content=query_prompt)
                ])
            query = query_response.content.strip() or user_input

            ai_msg = AIMessage(
                content=f"Searching for {query}...",
                tool_calls=[{
                    "id": str(uuid4()),
                    "name": self.search_tool_name,
                    "args": {"query": query}
                }],
            )
            messages = messages + [ai_msg]

        # ALWAYS return last_user_message
        return {"route": route,
                "messages": messages,
                "last_user_message": user_input
                }

    def detect_travel(self, state: TravelPlannerState) -> dict:
        query = state.get("last_user_message", "")
        if any(word in query for word in ["visit", "travel"]):
            route = "travel"
        else:
            route = "chat"

        return {"route": route,
                "messages": state["messages"],
                "last_user_message": query
                }

    def chat_node(self, state: TravelPlannerState):
        """
        Pure chat node for normal LLM conversation.
        No tool logic here.
        """
        if not state["messages"]:
            return {"messages": [
                AIMessage(content="I didn’t receive any input.")
                ]}

        last_msg = state["messages"][-1]

        # Ignore AIMessage (only handle HumanMessage)
        if not isinstance(last_msg, HumanMessage):
            print("check for HS,it is not")
            return {"messages": state["messages"]}
        response = self.llm.invoke([last_msg])
        return {"messages": state["messages"] + [response]}

    def travel_node(self, state: TravelPlannerState):
        extractor = TravelInfo()
        info = extractor.extract_trip_info(state["last_user_message"])
        state["location"] = info["location"]
        state["start_date"] = info["start_date"]
        state["end_date"] = info["end_date"]
        state["duration"] = info["duration"]
        # print(state)
        parts = ["Got it! Planning trip"]

        if state["location"]:
            parts.append(f"to {state['location']}")

        if state["duration"]:
            parts.append(f"for {state['duration']} days")

        if state["start_date"] and state["end_date"]:
            parts.append(f"from {state['start_date']} to {state['end_date']}")

        msg_text = " ".join(parts) + "."
        return {
                "messages": state["messages"] + [AIMessage(content=msg_text)],
                "location": state["location"],
                "start_date": state["start_date"],
                "end_date": state["end_date"],
                "duration": state["duration"],
            }
