import sqlite3
from flask import flash
import requests
import logging

from hjblog.db import get_db


class Coordinates:
    """Object that associates a city with its relative informations.
    Includes the city name, latitude, longitude, timezone and a http
    status code indicative of the success of the operation: a status code
    comprehended between 200 and 399 will provide the informations required,
    a status code outside the closed interval will not provide informations.
    """

    def __init__(
        self,
        city: str,
        latitude: str,
        longitude: str,
    ):
        self.city: str | None = None
        self.latitude: str | None = None
        self.longitude: str | None = None
        self.timezone: str | None = None
        self.status_code: int = None

        # City name is too long
        # NOTE: This errors should not happen if used with the form `hjblog.bps.user_actions.forms.QueryMeteoAPI`
        if len(city) > 169:
            flash("The name of the city provided is too long.", category="alert-danger")
            self._error(400)
        # No latitude and valid longitude or vice versa
        elif (latitude == "") ^ (longitude == ""):
            flash(
                "If you fulfill the latitude field you also need to fulfill the longitude field and vice versa",
                category="alert-danger",
            )
            self._error(400)
        # Latitude and longitude where provided by the user
        elif (latitude != "") and (longitude != ""):
            # Latitude and/or longitude are too long
            # NOTE: This should not happen if used with the form `hjblog.bps.user_actions.forms.QueryMeteoAPI`
            if len(latitude) > 10 or longitude > 7:
                flash(
                    "Incorrect latitude and longitude values", category="alert-danger"
                )
                self._error(400)
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            # NOTE: This errors should not happen if used with the form `hjblog.bps.user_actions.forms.QueryMeteoAPI`
            except ValueError:
                flash(
                    "Incorrect latitude and longitude values", category="alert-danger"
                )
                self._error(400)
            except Exception as e:
                # Unexpected behaviour
                logging.exception(e)
                self._error(400)
                flash(
                    "Incorrect latitude and longitude values", category="alert-danger"
                )
            self.city = city
            self.latitude = latitude
            self.longitude = longitude
            # Default timezone
            self.timezone = "Europe/Rome"
            self.status_code = 200
        # The user provided only the city name
        else:
            self._get_coordinates(city)

    def _error(self, code: int):
        """Private method, assaigns informations that are proper
        of a query that wasn't successful, in other words only the status status code.
        """
        self.city = None
        self.latitude = None
        self.longitude = None
        self.timezone = None
        self.status_code = code

    def _get_coordinates(self, city: str):
        """# `get_coordinates`

        Fetches the database and eventually the backend for the coordinates
        of the city required, sets the instance variables accordingly.
        """
        # examplar response:
        # `{'results': [{'id': 3169070, 'name': 'Rome', 'latitude': 41.89193, 'longitude': 12.51133, 'elevation': 20.0, 'feature_code': 'PPLC', 'country_code': 'IT', 'admin1_id': 3174976, 'admin2_id': 3169069, 'admin3_id': 3169071, 'timezone': 'Europe/Rome', 'population': 2318895, 'postcodes': ['00187'], 'country_id': 3175395, 'country': 'Italy', 'admin1': 'Latium', 'admin2': 'Rome', 'admin3': 'Rome'}], 'generationtime_ms': 2.247095}`

        # TODO: input sanitizing
        db = get_db()
        success = self._fetch_db_for_coordinates(city, db)
        # We found the coordinates in the database
        if success == True:
            return

        self._fetch_backend_for_coordinates(city)
        # We werent able to fetch the backend correctly
        if self.status_code != 200:
            return

        # We found a new valid entry for cities
        try:
            # Insert new entry in the database
            db.execute(
                "INSERT INTO cities (name, latitude, longitude, timezone) VALUES (?, ?, ?, ?)",
                (
                    city,
                    self.latitude,
                    self.longitude,
                    self.timezone,
                ),
            )
            db.commit()
        except sqlite3.Error as e:
            logging.exception(e)
            # NOTE: We incurred into a db error but we can still server the user
            # the result he has searched for
        except Exception as e:
            # Unexpected behaviour
            # NOTE: We incurred into a db error but we can still server the user
            # the result he has searched for
            logging.exception(e)

    def _fetch_db_for_coordinates(self, city: str, db: sqlite3.Connection) -> bool:
        """# `_fetch_db_for_coordinates`, `get_coordinates`'s helper

        Tries to fetch the information required from the database,
        populates the correct fields with the information and returns `True`, or it
        doesn't find a suitable entry and returns `False` without adding any information.
        """
        try:
            query = db.execute(
                "SELECT name, latitude, longitude, timezone FROM cities WHERE (name = ?)",
                (city,),
            ).fetchone()
        except sqlite3.Error as e:
            logging.exception(e)
            return False
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            return False

        if query is None:
            return False

        self.city = query["name"]
        self.latitude = query["latitude"]
        self.longitude = query["longitude"]
        self.timezone = query["timezone"]
        self.status_code = 200

        return True

    def _fetch_backend_for_coordinates(self, city: str):
        """# `_fetch_backend_for_coordinates`, `_get_coordinates`'s helper

        Fetches the backend for coordinates, populates the information with
        the information fetched if the procedure went fine, otherwise it will
        populates the fields with error informations.
        """
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search", params=params
        )
        try:
            json_response = response.json()
        except requests.exceptions.JSONDecodeError as e:
            self._error(500)
            return
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            self._error(500)
            return

        status = response.status_code
        if status > 399 or status < 200:
            if status == 404:
                self._error(404)
            else:
                self._error(500)
            return

        try:
            results = json_response.get("results", None)[0]
            latitude = results.get("latitude", None)
            longitude = results.get("longitude", None)
            timezone = results.get("timezone", None)
        except AttributeError as e:
            self._error(404)
            return
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            self._error(404)
            return

        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.status_code = 200

    def __repr__(self) -> str:
        if self.status_code >= 200 and self.status_code < 400:
            return f"city: {self.city}\nlatitude: {self.latitude}\nlongitude: {self.longitude}\ntimezone: {self.timezone}\nstatus code: {self.status_code}"
        return f"Error, http status code: {self.status_code}"


class WeatherForecast:
    """
    Object that encloses the forecast for a specific city, contains daily forecasts and hourly forecasts.
    The property `status_code` contains the response of the backend.
    [Backend documentation](https://open-meteo.com/en/docs).
    NOTE: only one status code, if one of the two failed we consider both failed.
    """

    def __init__(self, coordinates: Coordinates):
        self.hourly_forecast: list[HourlyForecast] | None = []
        self.daily_forecast: list[DailyForecast] | None = []
        self.coordinates = coordinates
        self.status_code: int = None

        # Hourly
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "timezone": coordinates.timezone,
            "forecast_hours": 20,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "surface_pressure",
                "cloud_cover",
                "wind_speed_10m",
                "precipitation_probability",
                "weather_code",
            ],
        }
        hourly = requests.get("https://api.open-meteo.com/v1/forecast", params=params)
        if hourly.status_code < 200 and hourly.status_code > 399:
            self._error(hourly.status_code)
            return

        try:
            hourly_json_response = hourly.json()
        except requests.exceptions.JSONDecodeError as e:
            self._error(500)
            return
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            self._error(500)
            return

        success = self._get_hourly_forecasts(hourly_json_response)
        if success == False:
            self._error(500)
            return

        # Daily
        params = {
            "latitude": coordinates.latitude,
            "longitude": coordinates.longitude,
            "forecast_days": 7,
            "timezone": coordinates.timezone,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_mean",
                "weather_code",
                "sunrise",
                "sunset",
            ],
        }

        daily = requests.get("https://api.open-meteo.com/v1/forecast", params=params)
        if daily.status_code < 200 and daily.status_code > 399:
            self._error(daily.status_code)
            return

        try:
            daily_json_response = daily.json()
        except requests.exceptions.JSONDecodeError as e:
            self._error(500)
            return
        except Exception as e:
            self._error(500)
            return

        success = self._get_daily_forecasts(daily_json_response)
        if success == False:
            self._error(500)
            return

        self.status_code = 200

    def _get_hourly_forecasts(self, forecast_json: dict) -> bool:
        """# `_get_hourly_forecast`, `__init__`'s helper

        Receives an appropriate response in json fromat, parses it and
        populates the appropriate instance variables, returns `True` if
        everything went fine, `False` otherwise.
        """
        try:
            # TODO: error handling: check if None
            hourly: dict = forecast_json.get("hourly", None)
            time: list[str] = hourly.get("time", None)
            temperature: list[float] = hourly.get("temperature_2m", None)
            relative_humidity: list[float] = hourly.get("relative_humidity_2m", None)
            surface_pressure: list[float] = hourly.get("surface_pressure", None)
            cloud_cover: list[int] = hourly.get("cloud_cover", None)
            wind_speed: list[float] = hourly.get("wind_speed_10m", None)
            precipitation_probability: list[int] = hourly.get(
                "precipitation_probability", None
            )
            weather_code: list[int] = hourly.get("weather_code", None)

            for i in range(0, len(time)):
                forecast = HourlyForecast(
                    time[i],
                    temperature[i],
                    relative_humidity[i],
                    surface_pressure[i],
                    cloud_cover[i],
                    wind_speed[i],
                    precipitation_probability[i],
                    weather_code[i],
                )
                self.hourly_forecast.append(forecast)
        except AttributeError as e:
            # This means the response received by the backend
            # is different from what we expected
            logging.error(f"Backed API hasn't responded as expectet: {e}")
            return False
        except Exception as e:
            # Unexpected behaviour
            logging.error(
                f"Unable to fulfill a request due to an unexpected error: {e}"
            )
            logging.exception(e)
            return False

        return True

    def _get_daily_forecasts(self, forecast_json: dict) -> bool:
        """# `_get_daily_forecasts`, `__init__`'s helper

        Receives an appropriate response in json fromat, parses it and
        populates the appropriate instance variables, returns `True` if
        everything went find, `False` otherwise.
        """
        try:
            # TODO: error handling: check if None
            daily: dict = forecast_json.get("daily", None)
            time: list[str] = daily.get("time", None)
            temperature_max: list[float] = daily.get("temperature_2m_max", None)
            temperature_min: list[float] = daily.get("temperature_2m_min", None)
            precipitation_probability: list[int] = daily.get(
                "precipitation_probability_mean", None
            )
            weather_code: list[int] = daily.get("weather_code", None)
            sunrise: list[str] = daily.get("sunrise", None)
            sunset: list[str] = daily.get("sunset", None)

            for i in range(0, len(time)):
                forecast = DailyForecast(
                    time[i],
                    temperature_max[i],
                    temperature_min[i],
                    precipitation_probability[i],
                    weather_code[i],
                    sunrise[i],
                    sunset[i],
                )
                self.daily_forecast.append(forecast)
        except AttributeError as e:
            # This means the response received by the backend
            # is different from what we expected
            logging.error(f"Backed API hasn't responded as expectet: {e}")
            logging.error(
                f"Unable to fulfill a request due to an unexpected error: {e}"
            )
            return False
        except Exception as e:
            # Unexpected behaviour
            logging.exception(e)
            return False
        return True

    def _error(self, status_code: int):
        """# `_error`, `__init__`'s helper

        Sets the appropriate fields in orther to represent a failure
        at responding to a query.
        """
        self.status_code = status_code
        self.hourly_forecast = None
        self.daily_forecast = None
        # The backend didn't responde as expected
        # TODO: logging the occurrence

    def __repr__(self):
        formatted = f"Forecast for {self.coordinates}\n\n\n"
        formatted = formatted + "HourlyForecasts:\n\n"
        for forecast in self.hourly_forecast:
            formatted = formatted + forecast.__repr__()
        formatted = formatted + "\n\n\nDailyForecast:\n\n"
        for forecast in self.daily_forecast:
            formatted = formatted + forecast.__repr__()
        return formatted


class HourlyForecast:
    """Docstring for HourlyPrediction."""

    def __init__(
        self,
        time: str,
        temperature: float,
        relative_humidity: float,
        surface_pressure: float,
        cloud_cover: int,
        wind_speed: float,
        precipitation_probability: int,
        weather_code: int,
    ):
        # TODO: validate types
        self.time = time
        self.temperature = temperature
        self.relative_humidity = relative_humidity
        self.surface_pressure = surface_pressure
        self.cloud_cover = cloud_cover
        self.wind_speed = wind_speed
        self.precipitation_probability = precipitation_probability
        self.weather_code = weather_code

    def get_weather(self) -> str:
        """Returns textual version of the weather code"""
        if self.weather_code == 0:
            return "clear sky"
        elif self.weather_code == 1 or self.weather_code == 2 or self.weather_code == 3:
            return "partly cloudy"
        elif self.weather_code == 45 or self.weather_code == 48:
            return "foggy"
        elif (
            self.weather_code == 51
            or self.weather_code == 53
            or self.weather_code == 55
        ):
            return "light precipitation"
        elif (
            self.weather_code == 51
            or self.weather_code == 53
            or self.weather_code == 55
        ):
            return "light precipitation"
        elif self.weather_code == 56 or self.weather_code == 57:
            return "freezing light precipitation"
        elif (
            self.weather_code == 61
            or self.weather_code == 63
            or self.weather_code == 65
        ):
            return "rain"
        elif self.weather_code == 66 or self.weather_code == 67:
            return "freezing rain"
        elif (
            self.weather_code == 71
            or self.weather_code == 73
            or self.weather_code == 75
        ):
            return "snow fall"
        elif self.weather_code == 77:
            return "snow grains"
        elif (
            self.weather_code == 80
            or self.weather_code == 81
            or self.weather_code == 82
        ):
            return "rain shower"
        elif self.weather_code == 85 or self.weather_code == 86:
            return "snow shower"
        elif self.weather_code == 95:
            return "thunderstorm"
        elif self.weather_code == 95 or self.weather_code == 99:
            return "thunderstorm and hail"

    def __repr__(self):
        return f"HourlyForecast for: {self.time}\ntemperature: {self.temperature}\nrelative_humidity: {self.relative_humidity}\nsurface_pressure: {self.surface_pressure}\ncloud_cover: {self.cloud_cover}\nwind_speed: {self.wind_speed}\nprecipitation_probability: {self.precipitation_probability}\nweather_code: {self.weather_code}"


class DailyForecast:
    """Docstring for HourlyPrediction."""

    def __init__(
        self,
        time: str,
        temperature_max: float,
        temperature_min: float,
        precipitation_probability: float,
        weather_code: int,
        sunrise: str,
        sunset: str,
    ):
        # TODO: validate types
        self.time = time
        self.temperature_max = temperature_max
        self.temperature_min = temperature_min
        self.precipitation_probability = precipitation_probability
        self.weather_code = weather_code
        self.sunrise = sunrise
        self.sunset = sunset

    def get_weather(self) -> str:
        """Returns textual version of the weather code"""
        if self.weather_code == 0:
            return "clear sky"
        elif self.weather_code == 1 or self.weather_code == 2 or self.weather_code == 3:
            return "partly cloudy"
        elif self.weather_code == 45 or self.weather_code == 48:
            return "foggy"
        elif (
            self.weather_code == 51
            or self.weather_code == 53
            or self.weather_code == 55
        ):
            return "light precipitation"
        elif (
            self.weather_code == 51
            or self.weather_code == 53
            or self.weather_code == 55
        ):
            return "light precipitation"
        elif self.weather_code == 56 or self.weather_code == 57:
            return "freezing light precipitation"
        elif (
            self.weather_code == 61
            or self.weather_code == 63
            or self.weather_code == 65
        ):
            return "rain"
        elif self.weather_code == 66 or self.weather_code == 67:
            return "freezing rain"
        elif (
            self.weather_code == 71
            or self.weather_code == 73
            or self.weather_code == 75
        ):
            return "snow fall"
        elif self.weather_code == 77:
            return "snow grains"
        elif (
            self.weather_code == 80
            or self.weather_code == 81
            or self.weather_code == 82
        ):
            return "rain shower"
        elif self.weather_code == 85 or self.weather_code == 86:
            return "snow shower"
        elif self.weather_code == 95:
            return "thunderstorm"
        elif self.weather_code == 95 or self.weather_code == 99:
            return "thunderstorm and hail"

    def __repr__(self):
        return f"DailyForecast for: {self.time}\ntemperature_max: {self.temperature_max}\ntemperature_min: {self.temperature_min}\nprecipitation_probability: {self.precipitation_probability}\nweather_code: {self.weather_code}\nsunrise: {self.sunrise}\nsunset: {self.sunset}"
