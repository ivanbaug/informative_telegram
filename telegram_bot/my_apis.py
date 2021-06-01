import requests
from datetime import datetime
from my_keys import  *

def get_weather():
  OWM_Endpoint = "https://api.openweathermap.org/data/2.5/onecall"
  weather_params = {
  "lat": 4.62, 
  "lon": -74.06,
  "appid": WEATHER_KEY,
  "exclude": "current,minutely,daily",
  "units": "metric",
  }
  response = requests.get(OWM_Endpoint, params=weather_params)
  response.raise_for_status()
  # get the next 8 hours of forecast to notify myself if it will rain
  response_json = response.json()
  tz_offset = int(response_json['timezone_offset'])
  forecasts = response_json['hourly'][:8]

  forecast_str = ""
  for f in forecasts:
    unixtime = int(f['dt']) + tz_offset #timezone offset
    # dt = datetime.utcfromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')
    dt = datetime.utcfromtimestamp(unixtime).strftime('%I%p')
    forecast = f['weather'][0]
    id = int(forecast['id'])
    main_fc = forecast['main']
    description_fc = forecast['description']
    comment = ""
    if id < 700:
      comment = " ☔"
    forecast_str += f"{dt} | {description_fc}{comment}\n"
  return forecast_str
