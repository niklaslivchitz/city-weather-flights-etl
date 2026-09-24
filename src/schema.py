"""Set up the cities database in a local MySQL server.

You have to call the functions from elsewhere to run them, planned for this project is a master notebook.

It could also be done in a database manager, but this way the schema lives in code.
"""

from sqlalchemy import text
from db import get_engine


TABLES = [
    """CREATE TABLE IF NOT EXISTS cities (
        city_id    INT AUTO_INCREMENT,
        city_name  VARCHAR(255) NOT NULL UNIQUE,
        PRIMARY KEY (city_id)
    )""",
    """CREATE TABLE IF NOT EXISTS cities_coords (
        city_id    INT,
        longitude  DECIMAL(9,6),
        latitude   DECIMAL(8,6),
        PRIMARY KEY (city_id),
        FOREIGN KEY (city_id) REFERENCES cities(city_id)
    )""",
    """CREATE TABLE IF NOT EXISTS city_pop (
        city_id         INT,
        population      INT,
        year_retrieved  DATE,
        PRIMARY KEY (city_id),
        FOREIGN KEY (city_id) REFERENCES cities(city_id)
    )""",
    """CREATE TABLE IF NOT EXISTS weather_actual (
        city_id       INT NOT NULL,
        measured_at   DATETIME NOT NULL,
        weather_main  VARCHAR(50),
        weather_desc  VARCHAR(100),
        temp          FLOAT,
        feels_like    FLOAT,
        temp_min      FLOAT,
        temp_max      FLOAT,
        pressure      INT,
        humidity      INT,
        visibility    INT,
        wind_speed    FLOAT,
        wind_deg      INT,
        wind_gust     FLOAT,
        clouds        INT,
        rain_1h       FLOAT,
        snow_1h       FLOAT,
        sunrise       DATETIME,
        sunset        DATETIME,
        utc_offset_s  INT,
        retrieved_at  DATETIME NOT NULL,
        PRIMARY KEY (city_id, measured_at),
        FOREIGN KEY (city_id) REFERENCES cities(city_id)
    )""",
    """CREATE TABLE IF NOT EXISTS weather_forecast (
        city_id       INT NOT NULL,
        forecast_for  DATETIME NOT NULL,
        retrieved_at  DATETIME NOT NULL,
        weather_main  VARCHAR(50),
        temp          FLOAT,
        humidity      INT,
        wind_speed    FLOAT,
        wind_gust     FLOAT,
        clouds        INT,
        pop           FLOAT,
        rain_3h       FLOAT,
        snow_3h       FLOAT,
        PRIMARY KEY (city_id, forecast_for),
        FOREIGN KEY (city_id) REFERENCES cities(city_id)
    )""",
]


def reset_database():
    """Drop and recreate the empty 'cities' database. Deletes all data."""
    admin_engine = get_engine(database=None)  # server-level, not inside a database
    with admin_engine.begin() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS cities"))
        conn.execute(text("CREATE DATABASE cities"))


def create_tables():
    """Create any tables that don't exist yet. Safe to run repeatedly."""
    engine = get_engine()
    with engine.begin() as conn:
        for stmt in TABLES:
            conn.execute(text(stmt))