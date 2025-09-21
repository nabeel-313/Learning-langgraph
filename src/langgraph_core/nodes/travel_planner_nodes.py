from src.langgraph_core.state.travel_planner_states import TravelPlannerState
from langchain_core.messages import AIMessage, HumanMessage
from uuid import uuid4
import json
from src.langgraph_core.tools.custom_tools import weather_tool, search_flights, search_hotels
from src.langgraph_core.tools.tools import get_tools
from src.utils.Utilities import TravelInfo
from src.loggers import Logger
from datetime import datetime


logger = Logger(__name__).get_logger()


class TravelPlannerNode:
    def __init__(self, llm):
        self.llm = llm
        self.weather_tool_name = weather_tool.name
        self.search_tool_name = get_tools()[0].name

    def router(self, state: TravelPlannerState) -> dict:
        logger.info("Router node node is called")
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

    def detect_travel(self, state: TravelPlannerState, ) -> dict:
        query = state.get("last_user_message", "")
        if any(word in query for word in ["visit", "travel"]):
            route = "travel"
        else:
            route = "chat"

        return {"route": route,
                "messages": state["messages"],
                "last_user_message": query
                }

    def chat_node(self, state: TravelPlannerState,):
        logger.info("Chat_node is called")
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
            return {"messages": state["messages"]}
        response = self.llm.invoke([last_msg])
        return {"messages": state["messages"] + [response]}

    def travel_node(self, state: TravelPlannerState):
        logger.info("Travel node is called")
        extractor = TravelInfo()
        info = extractor.extract_trip_info(state["last_user_message"])
        logger.info("Extracting the info from user msg ...")
        state["destination"] = info["destination"]
        state["start_date"] = info["start_date"]
        state["end_date"] = info["end_date"]
        state["duration"] = info["duration"]
        # print(state)
        parts = ["Got it! Planning trip"]

        if state["destination"]:
            parts.append(f"to {state['destination']}")

        if state["duration"]:
            parts.append(f"for {state['duration']} days")

        if state["start_date"] and state["end_date"]:
            parts.append(f"from {state['start_date']} to {state['end_date']}")

        msg_text = " ".join(parts) + "."
        return {
                "messages": state["messages"] + [AIMessage(content=msg_text)],
                "destination": state["destination"],
                "start_date": state["start_date"],
                "end_date": state["end_date"],
                "duration": state["duration"],
            }

    def collect_missing_travel_info(self, state: TravelPlannerState) -> dict:
        logger.info("Collecting missing traveling information")
        DATE_FORMAT = "%Y-%m-%d"  # ISO format: 2025-09-18
        # REQUIRED_FIELDS = ["location", "start_date", "end_date"]
        """
        Node function to collect missing travel information from the user.
        Updates state in-place and appends messages.
        """
        messages = state.get("messages", [])

        # Prompt for missing location
        if not state.get("destination"):
            user_input = input("Please provide travel destination: ").strip()
            state["destination"] = user_input
            messages.append(HumanMessage(content=user_input))

        if state.get("destination"):
            prompt = f"Is '{state['destination']}' a country or a city?" \
                      "Reply with only one word: country or city."
            resp = self.llm.invoke(prompt).content.strip().lower()

            if resp == "country":
                print(f"Destination '{state['destination']}' seems to be a country.")
                city_input = input(f"Please provide a city in {state['destination']} (e.g., capital or preferred city): ").strip()
                state["destination"] = city_input
                messages.append(HumanMessage(content=city_input))

        # ask for source location
        if not state.get("source"):
            user_input = input("Please provide source location: ").strip()
            state["source"] = user_input
            messages.append(HumanMessage(content=user_input))

        # Prompt for missing start_date
        while not state.get("start_date"):
            user_input = input("Please provide start date (YYYY-MM-DD): ").strip()
            try:
                start_date = datetime.strptime(user_input, DATE_FORMAT).date()
                state["start_date"] = start_date
                messages.append(HumanMessage(content=user_input))
            except ValueError:
                print("Invalid date format. Please enter in YYYY-MM-DD format.")

        # Prompt for missing end_date
        while not state.get("end_date"):
            user_input = input("Please provide end date (YYYY-MM-DD): ").strip()
            try:
                end_date = datetime.strptime(user_input, DATE_FORMAT).date()
                if end_date < state["start_date"]:
                    print("End date cannot be before start date. Try again.")
                    continue
                state["end_date"] = end_date
                messages.append(HumanMessage(content=user_input))
            except ValueError:
                print("Invalid date format. Please enter in YYYY-MM-DD format.")

        # Calculate duration automatically
        state["duration"] = (state["end_date"] - state["start_date"]).days + 1

        # Add summary AIMessage
        summary_msg = (
            "Collected travel info:\n"
            "destination: " + str(state["destination"]) + "\n"
            "Start Date: " + str(state["start_date"]) + "\n"
            "End Date: " + str(state["end_date"]) + "\n"
            "Duration: " + str(state["duration"]) + " days"
        )
        messages.append(AIMessage(content=summary_msg))

        state["messages"] = messages
        return state

    def flight_node(self, state: TravelPlannerState):
        messages = state.get("messages", [])
        source = state.get("source")
        destination = state.get("destination")
        # LLM prompt for IATA
        IATA_prompt = f"""
        Convert the following source and destination into IATA airport codes.
        Respond ONLY in strict JSON with keys "source" and "destination".
        Example:
        {{"source": "BOM", "destination": "DXB"}}
        User input:
        source: "{source}"
        destination: "{destination}"
        """

        resp = self.llm.invoke([HumanMessage(content=IATA_prompt)])
        raw_text = resp.content.strip()
        # print("LLM raw:", raw_text)

        # Parse the LLM output safely
        try:
            iata_data = json.loads(raw_text)
            source_iata = iata_data.get("source")
            destination_iata = iata_data.get("destination")
        except Exception:
            messages.append(AIMessage(content=f"Could not parse IATA codes. Raw: {raw_text}"))
            state["messages"] = messages
            return state

        if not source_iata:
            user_input = input(f'Could not find airport for "{source}". Please enter nearest airport city: ').strip()
            state["source"] = user_input
            messages.append(HumanMessage(content=f"Nearest airport city for source: {user_input}"))
            source_iata = user_input.upper()  # or re-run LLM to convert city → IATA

        if not destination_iata:
            user_input = input(f'Could not find airport for "{destination}". Please enter nearest airport city: ').strip()
            state["destination"] = user_input
            messages.append(HumanMessage(content=f"Nearest airport city for destination: {user_input}"))
            destination_iata = user_input.upper()  # or re-run LLM to convert city → IATA

        # Update state with normalized values
        # state["source"] = source_iata
        # state["destination"] = destination_iata

        flights_data = search_flights(
            source=source_iata,
            destination=destination_iata,
            start_date=state.get("start_date"),
            end_date=state.get("end_date"),
            flight_type=state.get("flight_type", "cheapest")
        )

        messages.append(AIMessage(content=f"Found {len(flights_data['flights'])} flights from {source_iata} to {destination_iata}."))
        flights_list = flights_data["flights"]
        flights_dict = {i + 1: flight for i, flight in enumerate(flights_list)}
        print(flights_dict)

        # Add 1–2 preview flights
        for f in flights_data["flights"][:2]:
            messages.append(AIMessage(content=f"{f['airline']} | {f['departure_airport']} → {f['arrival_airport']} {f['departure_time']} – {f['arrival_time']} | {f['price']}"))

        # Save into state
        # state["messages"] = messages
        # state["flights"] = flights_data["flights"]
        return state

    def hotel_node(self, state: TravelPlannerState):
        """
        Node to collect missing hotel info and search hotels using a custom tool.
        """
        messages = state.get("messages", [])

        # city = state.get("accommodation_city") or state.get("destination")
        # state["accommodation_city"] = city

        if state.get("accommodation_area_type") is None:
            area_input = input("Do you want to stay in main city, suburbs, or a specific neighborhood? ").strip()
            state["accommodation_area_type"] = area_input
            messages.append(HumanMessage(content=area_input))

        if state.get("accommodation_guests") is None:
            guests_input = input("How many guests will be staying? ").strip()
            state["accommodation_guests"] = int(guests_input)
            messages.append(HumanMessage(content=guests_input))

        hotel_results = search_hotels(
            city=state["destination"],
            area_type=state["accommodation_area_type"],
            check_in=state["start_date"],
            check_out=state["end_date"],
            guests=state["accommodation_guests"]
        )

        state["hotel_options"] = hotel_results.get("hotels", [])

        summary_msg = f"Found {len(state['hotel_options'])} hotels in {state['destination']} " \
                      f"({state['accommodation_area_type']}) for {state['accommodation_guests']} guests."
        messages.append(AIMessage(content=summary_msg))
        # state["messages"] = messages
        return state
