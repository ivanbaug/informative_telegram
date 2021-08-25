import requests
import feedparser
from datetime import datetime
from my_keys import *


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
        unixtime = int(f['dt']) + tz_offset  # timezone offset
        # dt = datetime.utcfromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')
        time = datetime.utcfromtimestamp(unixtime).strftime('%I%p')
        forecast = f['weather'][0]
        id = int(forecast['id'])
        main_fc = forecast['main']
        description_fc = forecast['description']
        comment = ""
        if id < 700:
            comment = " ☔"
        forecast_str += f"{time} | {description_fc}{comment}\n"
    return forecast_str


def entryd_to_date(date_str: str) -> datetime:
    # Works only with the format of this feed
    # Clean date string
    date_str = date_str[5:-6]
    # Convert to datetime obj
    return datetime.strptime(date_str, '%d %b %Y %H:%M:%S')


def get_rss_feed():
    NewsFeed = feedparser.parse(FEED_URL)

    # Get the latest date of an entry recorded by this script
    with open('last_date.txt', 'r') as file:
        last_date_str = file.readline()
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d %H:%M:%S')

    # Take the top 10 entries and check whether they are new
    new_entry_count = 0
    msg_text = ""
    new_date = last_date

    for e in NewsFeed.entries[:10]:
        entry_date = entryd_to_date(e['published'])
        if entry_date > last_date:
            new_entry_count += 1
            line = f"{entry_date} # {e['title']}\n"
            msg_text += line
            # print(line)
            # Record the most recent date to log it in a file at the end of
            # the process
            if entry_date > new_date:
                new_date = entry_date

    if new_entry_count:
        msg = f'There are {new_entry_count} new entries!\n{msg_text}'
    else:
        msg = 'There are no new entries.'

    if new_entry_count:
        with open('last_date.txt', 'w') as file:
            file.write(datetime.strftime(new_date, '%Y-%m-%d %H:%M:%S'))

    return (new_entry_count > 0, msg)
