# ETL building bootcamp project

This is a work in process - next step is adding another API with flights data.

## Project overview

A small end-to-end ETL pipeline built during the WBS Coding School Data Analytics bootcamp. It collects city data from Wikipedia and live weather data from the OpenWeatherMap API, transforms both with pandas, and loads them into a normalised MySQL database.

- **Extract:** web scraping (Wikipedia, via requests + BeautifulSoup) and REST API calls (OpenWeatherMap current weather and 5-day forecast)
- **Transform:** parsing coordinates and population figures out of messy HTML, flattening nested JSON into tidy DataFrames, converting Unix timestamps to UTC datetimes
- **Load:** writing into related MySQL tables with primary and foreign keys, using an `INSERT IGNORE` strategy so the pipeline can be rerun without crashing on duplicates

The whole pipeline is driven from a single notebook (`notebooks/pipeline.ipynb`), with the logic split into reusable modules in `src/`.

## Key questions

- How do you get semi-structured data from the web (HTML pages and JSON APIs) into a relational database in a repeatable way?
- How should that data be modelled so city facts are stored once and time series data (weather) can grow over time?
- How can a pipeline be made safe to rerun, so collecting new weather data is a single cell execution?

## Technologies

- Python 3 (pandas, requests, BeautifulSoup4, SQLAlchemy, PyMySQL, python-dotenv, lat-lon-parser)
- MySQL 8 (local server)
- Jupyter notebooks
- OpenWeatherMap API (free tier)

## Dataset

**Cities (scraped from English Wikipedia):** Berlin, Hamburg, Munich, Cologne, Frankfurt, London, Kiruna, Stockholm, Prague, Paris, Kiev, Madrid. For each city: country, latitude, longitude and population, plus the date the population was retrieved. The list lives in `pipeline.ipynb` and can be edited freely.

**Weather (OpenWeatherMap API):**
- Current conditions per city: temperature, feels-like, min/max, pressure, humidity, visibility, wind, clouds, rain and snow, sunrise and sunset
- 5-day forecast in 3-hour steps per city: temperature, humidity, wind, clouds, probability of precipitation, rain and snow

### Database schema

```
cities (database)
│
├── cities
│   ├── city_id          INT AUTO_INCREMENT   PK
│   └── city_name        VARCHAR(255)         NOT NULL UNIQUE
│
├── cities_coords
│   ├── city_id          INT                  PK, FK → cities.city_id
│   ├── longitude        DECIMAL(9,6)
│   └── latitude         DECIMAL(8,6)
│
├── city_pop
│   ├── city_id          INT                  PK, FK → cities.city_id
│   ├── population       INT
│   └── year_retrieved   DATE
│
├── weather_actual
│   ├── city_id          INT                  PK, FK → cities.city_id
│   ├── measured_at      DATETIME (UTC)       PK
│   ├── ...              weather measurements
│   └── retrieved_at     DATETIME (UTC)
│
└── weather_forecast
    ├── city_id          INT                  PK, FK → cities.city_id
    ├── forecast_for     DATETIME (UTC)       PK
    ├── retrieved_at     DATETIME (UTC)
    └── ...              forecast values
```

The full table definitions are in `src/schema.py`, so the schema lives in code rather than in a database manager.

## Setup

1. **Install a local MySQL server** and make sure you can log in as `root` on `127.0.0.1:3306`.

2. **Install the Python dependencies:**
   ```bash
   pip install pandas requests beautifulsoup4 sqlalchemy pymysql python-dotenv lat-lon-parser jupyter
   ```

3. **Get an OpenWeatherMap API key** (free) at [openweathermap.org](https://openweathermap.org/api).

4. **Create a `.env` file** in the project root (it is gitignored):
   ```
   MYSQL_PASSWORD=your_mysql_root_password
   OPENWEATHER_TOKEN=your_openweathermap_key
   ```

5. **Run `notebooks/pipeline.ipynb`.** On the first run, set both toggles to `True`:
   ```python
   RESET_DB = True   # drops and recreates the 'cities' database
   SCRAPE   = True   # scrapes Wikipedia for city data
   ```
   After that, set them back to `False`. Rerunning the notebook then only fetches fresh weather data and appends it. Set `SCRAPE = True` again only when you add new cities to the list.

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
│   └── weather.py       OpenWeatherMap calls and JSON to DataFrame transforms
├── notebooks/
│   └── pipeline.ipynb   master notebook that runs the whole pipeline
└── archive/             earlier exploratory notebooks (not committed)
```

## Key Results

- A working, rerunnable ETL pipeline: one notebook run loads the current weather for all 12 cities (12 rows) and the forecast for the next 5 days (40 time slots per city, 480 rows).
- A normalised relational model where static city facts are stored once and the weather tables grow over time, linked by `city_id`.
- Modular code: exploration notebooks were refactored into four importable modules, with the master notebook reduced to configuration and orchestration.
- Robust scraping for inconsistent Wikipedia infoboxes (for example Frankfurt, where the first cell after "Population" is an image caption, and Kiev, where the number carries a footnote marker).

### Known limitations and next steps

- **Forecast revisions are not kept.** Because `weather_forecast` uses `(city_id, forecast_for)` as its primary key and rows are inserted with `INSERT IGNORE`, only the first forecast retrieved for a given time slot is stored. Adding `retrieved_at` to the key would allow comparing how forecasts change as the time approaches, and later comparing them against `weather_actual`.
- **Population is a snapshot.** `city_pop` has one row per city, so a new scrape does not update the figure.
- **Scheduling.** The pipeline is run manually. The next step would be converting `pipeline.ipynb` into a script and running it on a schedule (cron, or a cloud function with a hosted database).
- The scrapers depend on Wikipedia's page layout and may break if the infobox structure changes.

## Author

Niklas Livchitz ([GitHub](https://github.com/niklaslivchitz))