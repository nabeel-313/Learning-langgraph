from pydantic import BaseModel, Field
from typing import Literal


class WindInfo(BaseModel):
    speed: float = Field(..., description="Wind speed in km/h")
    direction: int = Field(..., description="Wind direction in radian, e.g., 258'")


class WeatherResponse(BaseModel):
    city: str
    temp: float
    unit: Literal["Celsius", "Fahrenheit", "Kelvin"]
    wind: WindInfo
