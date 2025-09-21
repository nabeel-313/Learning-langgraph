import requests
from src.langgraph_core.schemas.all_schems import WeatherResponse, WindInfo
from langchain.tools import StructuredTool
from src.utils.Utilities import get_api_key
from src.loggers import Logger
from src.exceptions import ExceptionError
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


weather_tool = StructuredTool.from_function(
    func=weather_information,
    name="weather_infotmation",
    description="Fetches current weather info for a given city",
    return_direct=True,
)


def search_flights(source: str, destination: str, start_date: str,
                   end_date: str,
                   flight_type: str = "cheapest") -> Dict[str, Any]:
    """
    Search flights using SerpAPI.
    """
    api_key = get_api_key("SERPAPI_API_KEY")
    params = {
        "engine": "google_flights", "departure_id": source,
        "arrival_id": destination, "outbound_date": start_date,
        "return_date": end_date, "currency": "INR",
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
                "departure_airport": (
                    dep_airport.get("id") or dep_airport.get("name", ""),
                ),
                "departure_time": (
                    dep_airport.get("time") or dep_airport.get("datetime", ""),
                ),

                # Arrival
                "arrival_airport": (
                    arr_airport.get("id") or arr_airport.get("name", ""),
                ),
                "arrival_time": (
                    arr_airport.get("time") or arr_airport.get("datetime", ""),
                ),

                "duration": (
                    segment.get("duration", flight.get("duration", "")),
                ),
            })

        return {"flights": flight_options}

    except Exception as e:
        logger.error(f"Error fetching flights: {e}")
        return {"flights": []}


def search_hotels(
        city: str, area_type: str, check_in: str, check_out: str,
        guests: int, hotel_type: str = "best") -> Dict[str, Any]:
    """
    Search hotels using SerpAPI.
    Parameters:
        city: City to search in
        area_type: e.g., 'main city', 'suburban'
        check_in, check_out: YYYY-MM-DD format
        guests: Number of guests
        hotel_type: 'best' or 'cheapest'
    Returns:
        Dict with list of hotels
    """
    api_key = get_api_key("SERPAPI_API_KEY")
    params = {
        "engine": "google_hotels", "q": f"{city}, {area_type}",
        "check_in": check_in, "check_out": check_out,
        "guests": guests, "currency": "INR", "api_key": api_key,
        }

    try:
        logger.info(
            "Searching hotels in %s (%s) for %d guests from %s to %s",
            city, area_type, guests, check_in, check_out
        )
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

        # Extract hotel list
        hotel_list = data.get("hotels_results", [])
        if hotel_type == "cheapest":
            hotel_list.sort(key=lambda x: x.get("price", float("inf")))

        hotels = []
        for h in hotel_list:
            hotels.append({
                "name": h.get("title"),
                "address": h.get("address"),
                "price": h.get("price", {}).get("raw", "N/A"),
                "rating": h.get("rating"),
                "reviews": h.get("reviews"),
                "url": h.get("link"),
            })

        return {"hotels": hotels}

    except Exception as e:
        custom_err = ExceptionError(e)
        logger.error("Error fetching hotels: %s", custom_err)
        return {"hotels": []}
