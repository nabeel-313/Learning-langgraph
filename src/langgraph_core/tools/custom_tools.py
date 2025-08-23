import requests
from src.langgraph_core.schemas.all_schems import WeatherResponse, WindInfo
from langchain.tools import StructuredTool
from src.utils.Utilities import get_api_key

def weather_infotmation(city_name: str) -> WeatherResponse:
    """Generates a weather report for a given city."""
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": get_api_key("OPENWEATHERMAP_API_KEY"),
        "units": "metric"
    }
    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        raise ValueError(f"Error fetching weather: {response.text}")
    
    data = response.json()
    info = WeatherResponse(
        city=data['name'],
        temp=data['main']['temp'],
        unit="Celsius",
        wind=WindInfo(
            speed=data["wind"]["speed"],
            direction=data["wind"]["deg"]
        )
    )
    return info.dict()

# Wrap as StructuredTool so LangGraph / LangChain agent can use it
weather_tool = StructuredTool.from_function(
    func=weather_infotmation,
    name="weather_infotmation",
    description="Fetches current weather info for a given city",
    return_direct=True
)