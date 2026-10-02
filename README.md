# City, Weather & Flights ETL.

## Project overview

A small end-to-end ETL pipeline built as a bootcamp project.

The scenario: a fictional e-scooter company, wants to anticipate where and when scooters will be needed. For this we want weather, and incoming flights to model tourists.

The pipeline scrapes city data from Wikipedia using BeatifulSoup, pulls weather data from the OpenWeatherMap API and airports and flight arrivals from the AeroDataBox API, transforms everything with pandas, and loads it into a MySQL database.

Everything runs off of a single notebook (`notebooks/pipeline.ipynb`), all the different functions split into modules in `src/`. This is a design choice by me for good or bad. The guided project assumes everything should be done in one notebook + a SQL script, the latter of which is done through MySQL connections. This choice is mostly driven by me wanting to learn how to do the architecture this way - both in regards to submodules and pushing commands into SQL from Python scrips.


## Technologies

- Python (pandas, requests, BeautifulSoup, SQLAlchemy, PyMySQL, python-dotenv, lat-lon-parser)
- MySQL
- Jupyter notebooks
- OpenWeatherMap API
- AeroDataBox API via RapidAPI

## Dataset

- An arbitrary list of cities, with their population and coordinates. The master list is in the pipelines notebook and can be edited to rescope.

- Weather concerning the cities, in two tables, one storing actual weather, and one storing a week long forecast.

- Airports within 50 km from the city coordinates - this might be a bit too large, since we dont do any sanity checks here. E.g. Düsseldorf gets sorted to Cologne, Kiev has no civilian traffic in wartime, and Berlin Tegel has been closed for years.

### Database schema

```
cities (database)
│
├── cities
│   ├── city_id            INT AUTO_INCREMENT   PK
│   └── city_name          VARCHAR(255)         NOT NULL UNIQUE
│
├── cities_coords
│   ├── city_id            INT                  PK, FK → cities.city_id
│   ├── longitude          DECIMAL(9,6)
│   └── latitude           DECIMAL(8,6)
│
├── city_pop
│   ├── city_id            INT                  PK, FK → cities.city_id
│   ├── population         INT
│   └── year_retrieved     DATE
│
├── weather_actual
│   ├── city_id            INT                  PK, FK → cities.city_id
│   ├── measured_at        DATETIME (UTC)       PK
│   ├── ...                weather measurements
│   └── retrieved_at       DATETIME (UTC)
│
├── weather_forecast
│   ├── city_id            INT                  PK, FK → cities.city_id
│   ├── forecast_for       DATETIME (UTC)       PK
│   ├── retrieved_at       DATETIME (UTC)
│   └── ...                forecast values
│
├── airports
│   ├── icao               VARCHAR(4)           PK
│   ├── iata               VARCHAR(3)
│   ├── airport_name       VARCHAR(255)
│   └── city_id            INT                  FK → cities.city_id
│
└── flights
    ├── arrival_icao       VARCHAR(4)           PK, FK → airports.icao
    ├── flight_number      VARCHAR(20)          PK
    ├── scheduled_arrival  DATETIME (UTC)       PK
    ├── revised_arrival    DATETIME (UTC)
    ├── origin_icao        VARCHAR(4)
    ├── origin_name        VARCHAR(255)
    ├── airline            VARCHAR(255)
    ├── aircraft_model     VARCHAR(100)
    ├── status             VARCHAR(50)
    └── retrieved_at       DATETIME (UTC)
```

The full table definitions are in `src/schema.py`, which is the setup file injecting instructions to the database.

## Setup

1. **Install a local MySQL server**.

2. **Install the Python dependencies:**
   ```
   pip install pandas requests beautifulsoup4 sqlalchemy pymysql python-dotenv lat-lon-parser jupyter
   ```

3. **Get the API keys:**
   - OpenWeatherMap (free) at [openweathermap.org](https://openweathermap.org/api)
   - RapidAPI account at [rapidapi.com](https://rapidapi.com), then subscribe to the free Basic plan of [AeroDataBox](https://rapidapi.com/aedbx-aedbx/api/aerodatabox/).

4. **Create a `.env` file** in the project root (it is gitignored):
   ```
   MYSQL_PASSWORD=your_mysql_root_password
   OPENWEATHER_TOKEN=your_openweathermap_key
   RAPIDAPI_KEY=your_rapidapi_key
   ```

5. **Run `notebooks/pipeline.ipynb`.** It has three toggles:
   ```python
   RESET_DB = False   # True drops and recreates the database
   SCRAPE   = False   # True scrapes Wikipedia and searches for airports
   FLIGHTS  = False   # True fetches tomorrow's arrivals (costs API calls)
   ```
   On the first run, set all three to `True`. After that, set `RESET_DB` and `SCRAPE` back to `False`; `SCRAPE` is only needed again when you add new cities. Weather is fetched on every run. Turn `FLIGHTS` on when you want the next day's arrivals.

## Repo Structure

```
ETL/
├── .env                 credentials (not committed)
├── .gitignore
├── README.md
├── src/
│   ├── db.py            database engine and the INSERT IGNORE helper
│   ├── schema.py        table definitions, create_tables() and reset_database()
│   ├── scrape.py        Wikipedia scrapers: cityscraper() and popscraper()
│   ├── weather.py       OpenWeatherMap calls and JSON to DataFrame transforms
│   └── airports.py      AeroDataBox airport search, arrivals and JSON to DataFrame transforms
├── notebooks/
    └── pipeline.ipynb   master notebook that runs the whole pipeline
```

## Author

Niklas Livchitz ([GitHub](https://github.com/niklaslivchitz))
