"""This script fetches weather forecast data for a list of cities. It uses the OpenWeatherMap API to get the forecast data."""

import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv
import requests
from db import get_engine


load_dotenv(find_dotenv(usecwd=True, raise_error_if_not_found=True), override=True)

weather_token = os.getenv("OPENWEATHER_TOKEN")

#we need some data from the database to know what to call

def load_cities(engine):
    name_df = pd.read_sql("cities", con=engine)
    coords_df = pd.read_sql("cities_coords", con=engine)
    return name_df.merge(coords_df, on="city_id")

#and here is the function to get the weather data for a list of cities

def get_weather_data(merge_df):
    weather_data = {}
    for city in merge_df['city_name']:
        lat = merge_df.loc[merge_df['city_name'] == city, 'latitude'].values[0]
        lon = merge_df.loc[merge_df['city_name'] == city, 'longitude'].values[0]
        response = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={weather_token}&units=metric")
        if response.status_code == 200:
            data = response.json()
            data["retrieved_at"] = pd.Timestamp.now(tz="UTC")
            city_id = merge_df.loc[merge_df['city_name'] == city, 'city_id'].values[0]
            weather_data[city_id] = data
        else:
            print(f"Failed to get data for {city}: {response.status_code}")
    return weather_data

#we also need to transform the data, middle step is a dataframe

def weather_to_df(weather_data):
    rows = []
    for city_id, w in weather_data.items():
        rows.append({
            "city_id": int(city_id),
            "measured_at": pd.to_datetime(w["dt"], unit="s", utc=True),
            "weather_main": w["weather"][0]["main"],
            "weather_desc": w["weather"][0]["description"],
            "temp": w["main"]["temp"],
            "feels_like": w["main"]["feels_like"],
            "temp_min": w["main"]["temp_min"],
            "temp_max": w["main"]["temp_max"],
            "pressure": w["main"]["pressure"],
            "humidity": w["main"]["humidity"],
            "visibility": w.get("visibility"),
            "wind_speed": w["wind"].get("speed"),
            "wind_deg": w["wind"].get("deg"),
            "wind_gust": w["wind"].get("gust", w["wind"].get("speed")),#gust is often missing - setting it to zero makes no sense, a better lower bound is wind speed.
            "clouds": w["clouds"]["all"],
            "rain_1h": w.get("rain", {}).get("1h", 0.0),
            "snow_1h": w.get("snow", {}).get("1h", 0.0),
            "sunrise": pd.to_datetime(w["sys"]["sunrise"], unit="s", utc=True),
            "sunset": pd.to_datetime(w["sys"]["sunset"], unit="s", utc=True),
            "utc_offset_s": w["timezone"],
            "retrieved_at": w["retrieved_at"],
        })
    df = pd.DataFrame(rows)
    return df

#we also have access to forecasts, lets pull that:

def get_weather_forecast(merge_df):
    forecast_data = {}
    for city in merge_df['city_name']:
        lat = merge_df.loc[merge_df['city_name'] == city, 'latitude'].values[0]
        lon = merge_df.loc[merge_df['city_name'] == city, 'longitude'].values[0]
        response = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={weather_token}&units=metric")
        if response.status_code == 200:
            data = response.json()
            data["retrieved_at"] = pd.Timestamp.now(tz="UTC")
            city_id = merge_df.loc[merge_df['city_name'] == city, 'city_id'].values[0]
            forecast_data[city_id] = data
        else:
            print(f"Failed to get data for {city}: {response.status_code}")
    return forecast_data

#and here is the function to transform the forecast data into a dataframe

def forecast_to_df(forecast_data):
    rows = []
    for city_id, f in forecast_data.items():
        for entry in f["list"]:
            rows.append({
                "city_id": int(city_id),
                "retrieved_at": f["retrieved_at"],
                "forecast_for": pd.to_datetime(entry["dt"], unit="s", utc=True),
                "weather_main": entry["weather"][0]["main"],
                "temp": entry["main"]["temp"],
                "humidity": entry["main"]["humidity"],
                "wind_speed": entry["wind"].get("speed"),
                "wind_gust": entry["wind"].get("gust"),
                "clouds": entry["clouds"]["all"],
                "pop": entry.get("pop", 0.0),
                "rain_3h": entry.get("rain", {}).get("3h", 0.0),
                "snow_3h": entry.get("snow", {}).get("3h", 0.0),
            })
    df = pd.DataFrame(rows)
    return df
