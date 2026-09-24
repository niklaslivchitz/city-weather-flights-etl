"""This script contains functions to scrape data from Wikipedia regarding cities and their populations."""


import requests
from bs4 import BeautifulSoup
import pandas as pd
from lat_lon_parser import parse
from datetime import datetime

HEADERS = {'User-Agent': 'ETL-bootcamp-project see https://github.com/niklaslivchitz/ETL-test'}

def cityscraper(citylist):
    "this functions scrapes the country, latitude and longitude of a list of cities from Wikipedia and returns a pandas dataframe with the results."
    soups = {}
    slurry = {}
    for city in citylist:
        url = f"https://en.wikipedia.org/wiki/{city}"
        response = requests.get(url, headers=HEADERS)
        soups[city] = BeautifulSoup(response.content, 'html.parser')
        slurry[city] = [soups[city].find(class_="infobox-data").get_text(), soups[city].find(class_="latitude").get_text(), soups[city].find(class_="longitude").get_text()]
    df = pd.DataFrame(slurry).transpose()
    df.columns = ["country", "latitude", "longitude"]
    cities_only = df.reset_index().rename(columns={"index": "city_name"})
    cities_only["latitude"] = cities_only["latitude"].apply(parse)
    cities_only["longitude"] = cities_only["longitude"].apply(parse)
    return cities_only



def popscraper(citylist):
    "and this function scrapes the population of a list of cities from Wikipedia and returns a pandas dataframe with the results."
    soups = {}
    slurry = {}
    for city in citylist:
        url = f"https://en.wikipedia.org/wiki/{city}"
        response = requests.get(url, headers=HEADERS)
        soups[city] = BeautifulSoup(response.content, 'html.parser')
        infobox = soups[city].find("table", class_="infobox")
        pop_header = infobox.find(string=lambda s: s and s.strip().startswith("Population"))
        pop_cell = pop_header.find_next("td")
        pop_text = pop_cell.get_text()

        if not any(char.isdigit() for char in pop_text):
            pop_cell = pop_cell.find_next("td")
            pop_text = pop_cell.get_text()

        slurry[city] = [pop_text, datetime.today().strftime("%d.%m.%Y")]
    df = pd.DataFrame(slurry).transpose()
    df.columns = ["population", "year_retrieved"]
    cities_only = df.reset_index().rename(columns={"index": "city_name"})
    cities_only["population"] = cities_only["population"].str.extract(r'([\d,]+)')[0]
    cities_only["population"] = cities_only["population"].str.replace(",", "", regex=False).astype(int)
    cities_only["year_retrieved"] = pd.to_datetime(cities_only["year_retrieved"], format="%d.%m.%Y")
    return cities_only

