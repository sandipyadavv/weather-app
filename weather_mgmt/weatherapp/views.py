
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from django.conf import settings
from django.shortcuts import render


# Load environment variables from the .env file
ENV_FILE = Path(settings.BASE_DIR) / ".env"
load_dotenv(ENV_FILE)

API_KEY = os.getenv("OPENWEATHER_API_KEY")


def home(request):
    city = request.GET.get("city", "Kathmandu").strip() or "Kathmandu"

    weather = None
    forecast = []
    error = None

    if not API_KEY:
        error = (
            "API key not found. Please check your .env file "
            "in the project root directory."
        )
        print("DEBUG: OPENWEATHER_API_KEY was not loaded.")

    else:
        try:
            # Get current weather
            current_url = (
                "https://api.openweathermap.org/data/2.5/weather"
            )

            response = requests.get(
                current_url,
                params={
                    "q": city,
                    "appid": API_KEY,
                    "units": "metric",
                },
                timeout=15,
            )

            if response.status_code == 401:
                error = (
                    "OpenWeather rejected your API key. "
                    "Check the key in .env and make sure it is activated."
                )
                print("DEBUG: OpenWeather returned HTTP 401.")

            elif response.status_code == 404:
                error = "City not found. Please enter a valid city name."

            else:
                response.raise_for_status()
                data = response.json()

                current = data["main"]
                condition = data["weather"][0]

                weather = {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": round(current["temp"]),
                    "feels_like": round(current["feels_like"]),
                    "description": condition["description"].title(),
                    "icon": condition["icon"],
                    "humidity": current["humidity"],
                    "pressure": current["pressure"],
                    "wind": data.get("wind", {}).get("speed", 0),
                    "temp_min": round(current["temp_min"]),
                    "temp_max": round(current["temp_max"]),
                }

                # Get five-day forecast
                forecast_url = (
                    "https://api.openweathermap.org/data/2.5/forecast"
                )

                forecast_response = requests.get(
                    forecast_url,
                    params={
                        "q": city,
                        "appid": API_KEY,
                        "units": "metric",
                    },
                    timeout=15,
                )

                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()

                daily = {}

                for item in forecast_data.get("list", []):
                    date = item["dt_txt"].split(" ")[0]
                    hour = item["dt_txt"].split(" ")[1]

                    # Prefer the forecast around noon for each day
                    if date not in daily or hour.startswith("12:"):
                        daily[date] = item

                for date, item in list(daily.items())[:5]:
                    forecast.append({
                        "date": date,
                        "temperature": round(item["main"]["temp"]),
                        "description": (
                            item["weather"][0]["description"].title()
                        ),
                        "icon": item["weather"][0]["icon"],
                    })

        except requests.exceptions.HTTPError as exc:
            print("DEBUG: OpenWeather HTTP error:", exc)
            weather = None
            forecast = []
            error = (
                "The weather service returned an error. "
                "Check your API key, account activation, and API access."
            )

        except requests.exceptions.Timeout:
            print("DEBUG: OpenWeather request timed out.")
            weather = None
            forecast = []
            error = "Weather request timed out. Please try again."

        except requests.exceptions.RequestException as exc:
            print("DEBUG: OpenWeather connection error:", exc)
            weather = None
            forecast = []
            error = (
                "Could not connect to the weather service. "
                "Check your internet connection."
            )

        except (KeyError, TypeError, ValueError) as exc:
            print("DEBUG: Unexpected weather data:", exc)
            weather = None
            forecast = []
            error = "The weather service returned unexpected data."

    return render(
        request,
        "weatherapp/index.html",
        {
            "weather": weather,
            "forecast": forecast,
            "error": error,
            "searched_city": city,
        },
    )