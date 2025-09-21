import requests
from src.langgraph_core.schemas.all_schems import WeatherResponse, WindInfo
from langchain.tools import StructuredTool
from src.utils.Utilities import get_api_key
from src.loggers import Logger
from typing import Dict, Any


logger = Logger(__name__).get_logger()


def weather_information(city_name: str) -> WeatherResponse:
    """Generates a weather report for a given city."""
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": get_api_key("OPENWEATHERMAP_API_KEY"),
        "units": "metric",
    }
    # print("weather node called")
    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise ValueError(f"Error fetching weather: {response.text}")

    data = response.json()
    info = WeatherResponse(
        city=data["name"],
        temp=data["main"]["temp"],
        unit="Celsius",
        wind=WindInfo(speed=data["wind"]["speed"],
                      direction=data["wind"]["deg"]),
    )
    return info.dict()


# Wrap as StructuredTool so LangGraph / LangChain agent can use it
weather_tool = StructuredTool.from_function(
    func=weather_information,
    name="weather_infotmation",
    description="Fetches current weather info for a given city",
    return_direct=True,
)


def search_flights(source: str, destination: str, start_date: str,
                   end_date: str, flight_type: str = "cheapest") -> Dict[str, Any]:
    """
    Search flights using SerpAPI.
    """
    api_key = get_api_key("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SerpAPI API key is required")

    params = {
        "engine": "google_flights",
        "departure_id": source,
        "arrival_id": destination,
        "outbound_date": start_date,
        "return_date": end_date,
        "currency": "INR",
        "api_key": api_key,
    }

    try:
        logger.info("Searching flights from %s to %s", source, destination)
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        results = response.json()

        # Decide which list of flights to use
        if flight_type == "cheapest":
            flights = results.get("cheapest_flights", []) or results.get("best_flights", [])
        else:
            flights = results.get("best_flights", []) or results.get("other_flights", [])

        flight_options = []
        for flight in flights:
            segment = flight.get("flights", [{}])[0]

            dep_airport = segment.get("departure_airport", {})
            arr_airport = segment.get("arrival_airport", {})

            flight_options.append({
                "airline": segment.get("airline", flight.get("airline", "")),
                "price": flight.get("price", "N/A"),

                # Departure
                "departure_airport": dep_airport.get("id") or dep_airport.get("name", ""),
                "departure_time": dep_airport.get("time") or dep_airport.get("datetime", ""),

                # Arrival
                "arrival_airport": arr_airport.get("id") or arr_airport.get("name", ""),
                "arrival_time": arr_airport.get("time") or arr_airport.get("datetime", ""),

                "duration": segment.get("duration", flight.get("duration", "")),
            })

        return {"flights": flight_options}

    except Exception as e:
        logger.error(f"Error fetching flights: {e}")
        return {"flights": []}
