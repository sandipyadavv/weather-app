from django.shortcuts import render

import os
import requests
from dotenv import load_dotenv
from django.shortcuts import render

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


def home(request):
    city = request.GET.get("city", "Kathmandu").strip() or "Kathmandu"

    weather = None
    forecast = []
    error = None

    if not API_KEY:
        error = "Add your OpenWeather API key to the .env file."
    else:
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": city,
                    "appid": API_KEY,
                    "units": "metric",
                },
                timeout=10,
            )

            if response.status_code == 404:
                error = "City not found. Please try another city."
            elif response.status_code == 401:
                error = "Invalid API key. Please check your .env file."
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

                forecast_response = requests.get(
                    "https://api.openweathermap.org/data/2.5/forecast",
                    params={
                        "q": city,
                        "appid": API_KEY,
                        "units": "metric",
                    },
                    timeout=10,
                )
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()

                daily = {}

                for item in forecast_data.get("list", []):
                    date = item["dt_txt"].split(" ")[0]
                    hour = item["dt_txt"].split(" ")[1]

                    if date not in daily or hour.startswith("12:"):
                        daily[date] = item

                for date, item in list(daily.items())[:5]:
                    forecast.append({
                        "date": date,
                        "temperature": round(item["main"]["temp"]),
                        "description": item["weather"][0]["description"].title(),
                        "icon": item["weather"][0]["icon"],
                    })

        except requests.RequestException:
            weather = None
            forecast = []
            error = "Could not retrieve weather. Check your internet or API key."
        except (KeyError, TypeError, ValueError):
            weather = None
            forecast = []
            error = "The weather service returned unexpected data."

    return render(request, "weatherapp/index.html", {
        "weather": weather,
        "forecast": forecast,
        "error": error,
        "searched_city": city,
    })


# Create your views here.
