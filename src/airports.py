"""Fetches airports near our cities and their arrivals from the AeroDataBox API (via RapidAPI)
and transforms the responses into dataframes matching the airports and flights tables."""
 
import os
import time
 
import pandas as pd
import requests
from dotenv import load_dotenv, find_dotenv
 
load_dotenv(find_dotenv(usecwd=True, raise_error_if_not_found=True), override=True)

#we use the aerodatabox from RapidAPI, free tier. Here's a reusable header
 
HEADERS = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
}
BASE_URL = "https://aerodatabox.p.rapidapi.com"

#First thing we need is to identify airports per city. There is a separate call for this.
 
def get_airports(cities_df, radius_km=50):
    """Find airports near each city (the output of weather.load_cities works)"""
    rows = []
    for row in cities_df.itertuples():
        response = requests.get(
            f"{BASE_URL}/airports/search/location",
            headers=HEADERS,
            params={"lat": row.latitude, "lon": row.longitude, "radiusKm": radius_km,
                    "limit": 10, "withFlightInfoOnly": "true"},
            timeout=10,
        )
        if response.status_code == 200:
            for a in response.json().get("items", []):
                rows.append({
                    "icao": a["icao"],
                    "iata": a.get("iata"),
                    "airport_name": a.get("name"),
                    "city_id": int(row.city_id),
                })
        else:
            print(f"Failed to get airports for {row.city_name}: {response.status_code}")
        time.sleep(1)  # free tier is rate limited
    # an airport close to two cities should only appear once
    df=pd.DataFrame(rows).drop_duplicates(subset="icao")
    return df

#Now we can pull arrivals for a particular day for each airport. The API allows at most 12 hours per request, so we need two calls per day. Times in the request are local to the airport.

def get_arrivals(icao_list, date=None):
    """Fetch all arrivals for one day (default: tomorrow) for each airport.
    Times in the request are local to the airport. Returns {icao: {"arrivals": [...], "retrieved_at": ...}}."""
    if date is None:
        date = (pd.Timestamp.today() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    windows = [(f"{date}T00:00", f"{date}T11:59"), (f"{date}T12:00", f"{date}T23:59")] #for request windows. We need two calls per day because the API only allows 12 hours per request. Times are local to the airport.
    flight_data = {}
    for icao in icao_list:
        arrivals = []
        for start, end in windows:
            #bunch of params to filter our stuff not relevant to tourism.
            response = requests.get(
                f"{BASE_URL}/flights/airports/icao/{icao}/{start}/{end}",
                headers=HEADERS,
                params={"direction": "Arrival", "withCodeshared": "false",
                        "withCancelled": "false", "withCargo": "false",
                        "withPrivate": "false"},
                timeout=10,
            )
            if response.status_code == 200:
                arrivals.extend(response.json().get("arrivals", []))
            elif response.status_code == 204:
                pass  # no flights in this window
            else:
                print(f"Failed to get arrivals for {icao} {start}: {response.status_code}")
            time.sleep(1)  # free tier is rate limited
        flight_data[icao] = {"arrivals": arrivals, "retrieved_at": pd.Timestamp.now(tz="UTC")}
    return flight_data

#Finally, we can transform the arrivals data into a dataframe matching the flights table.

def flights_to_df(flight_data):
    """Flatten get_arrivals output into a dataframe for the flights table."""
    rows = []
    for arrival_icao, f in flight_data.items():
        for entry in f["arrivals"]:
            m = entry["movement"]  # for arrivals, movement.airport is the ORIGIN
            rows.append({
                "arrival_icao": arrival_icao,
                "flight_number": entry["number"],
                "scheduled_arrival": pd.to_datetime(m["scheduledTime"]["utc"], utc=True),
                "revised_arrival": pd.to_datetime(m.get("revisedTime", {}).get("utc"), utc=True),
                "origin_icao": m["airport"].get("icao"),
                "origin_name": m["airport"].get("name"),
                "airline": entry.get("airline", {}).get("name"),
                "aircraft_model": entry.get("aircraft", {}).get("model"),
                "status": entry.get("status"),
                "retrieved_at": f["retrieved_at"],
            })
    return pd.DataFrame(rows)