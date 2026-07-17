import os
import json
from pathlib import Path
from typing import Dict, Optional
from fastmcp import FastMCP
from geopy.geocoders import Nominatim
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Initialize FastMCP
mcp = FastMCP("openmeteo-weather-mcp")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

geolocator = Nominatim(user_agent="openmeteo-weather-mcp")


def get_lat_long(location_string: str):
    """
    Gets the latitude and longitude of a location string using Nominatim.

    Args:
        location_string: The location string (e.g., "Paris, France").

    Returns:
        A tuple containing (latitude, longitude) or None if the location is not found.
    """

    try:
        location = geolocator.geocode(location_string)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        print(f"Error geocoding location: {e}")
        return None


@mcp.tool()
async def get_7day_weather(location: str) -> Dict:
    """Get hourly weather forecast for a location."""

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    lat, long = get_lat_long(location)
    params = {
        "latitude": lat,
        "longitude": long,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation"],
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    return hourly_dataframe.to_dict(orient="records")


@mcp.tool()
async def get_current_weather(location: str) -> Dict:
    """Get current weather forecast for a location."""

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    lat, long = get_lat_long(location)
    params = {
        "latitude": lat,
        "longitude": long,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
        ],
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_relative_humidity_2m = current.Variables(1).Value()
    current_apparent_temperature = current.Variables(2).Value()
    current_precipitation = current.Variables(3).Value()
    current_weather_code = current.Variables(4).Value()
    current_wind_speed_10m = current.Variables(5).Value()
    current_wind_direction_10m = current.Variables(6).Value()

    current_dict = {
        "temperature_2m": current_temperature_2m,
        "relative_humidity_2m": current_relative_humidity_2m,
        "apparent_temperature": current_apparent_temperature,
        "precipitation": current_precipitation,
        "weather_code": current_weather_code,
        "wind_speed_10m": current_wind_speed_10m,
        "wind_direction_10m": current_wind_direction_10m,
    }

    to_json = json.dumps(current_dict)
    return to_json


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
