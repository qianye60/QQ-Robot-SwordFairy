import os
import requests
from datetime import datetime
from langchain_core.tools import tool
from .config import config
import pytz

weather_config = config.get('openweather', {})
os.environ["OPENWEATHER_API_KEY"] = weather_config.get('api_key', '')

@tool
def get_weather_data(location: str, country_code: str, query_time: str = None, query_type: str = 'current'):
    """检索特定位置和时间的天气数据。
    Args:
        location: 城市名称或者中国的直辖市或副省级城市. e.g. 成都、北京、上海.
        country_code: 该地点的 ISO 3166 国家代码. e.g. CN.
        query_time: 检索天气数据的时间，格式为“YYYY-MM-DD HH:MM:SS”。可选。
        query_type: 要检索的天气数据类型。选项包括“current”（当前）、“today”（今天）、“hourly”（每小时）、“daily”（每天）。“daily”可以查询一周中每天的天气。可选。
    """
    api_key = os.environ.get('OPENWEATHER_API_KEY')

    if not api_key:
        return "API key not found. Please set the OPENWEATHER_API_KEY environment variable."

    geo_url = f'http://api.openweathermap.org/geo/1.0/direct?q={location},{country_code}&appid={api_key}'
    geo_response = requests.get(geo_url)
    geo_data = geo_response.json()

    if not geo_data:
        return "Location not found."

    lat = geo_data[0]['lat']
    lon = geo_data[0]['lon']

    exclude_options = {
        'current': 'minutely,hourly,daily,alerts',
        'today': 'current,minutely,hourly,alerts',
        'hourly': 'current,minutely,daily,alerts',
        'daily': 'current,minutely,hourly,alerts',
        'alerts': 'current,minutely,hourly,daily'
    }

    exclude_param = exclude_options.get(query_type, 'minutely,hourly,daily,alerts')

    if query_time:
        query_timestamp = int(datetime.strptime(query_time, '%Y-%m-%d %H:%M:%S').timestamp())
        weather_url = f'https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={query_timestamp}&appid={api_key}&units=metric'
    else:
        weather_url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={exclude_param}&appid={api_key}&units=metric'

    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    def format_timestamp(timestamp, timezone_str):
      """格式化时间戳为指定时区的日期时间字符串。"""
      try:
          tz = pytz.timezone(timezone_str)
          dt = datetime.fromtimestamp(timestamp, tz)
          return dt.strftime('%Y-%m-%d %H:%M:%S')
      except Exception:
          return timestamp
    
    if 'timezone' in weather_data:
        timezone_str = weather_data['timezone']

        if 'daily' in weather_data:
          for day_data in weather_data['daily']:
              day_data['dt'] = format_timestamp(day_data['dt'], timezone_str)
              day_data['sunrise'] = format_timestamp(day_data['sunrise'], timezone_str)
              day_data['sunset'] = format_timestamp(day_data['sunset'], timezone_str)
              day_data['moonrise'] = format_timestamp(day_data['moonrise'], timezone_str)
              day_data['moonset'] = format_timestamp(day_data['moonset'], timezone_str)
        if 'hourly' in weather_data:
            for hour_data in weather_data['hourly']:
                hour_data['dt'] = format_timestamp(hour_data['dt'], timezone_str)
        if 'current' in weather_data:
            weather_data['current']['dt'] = format_timestamp(weather_data['current']['dt'], timezone_str)
            weather_data['current']['sunrise'] = format_timestamp(weather_data['current']['sunrise'], timezone_str)
            weather_data['current']['sunset'] = format_timestamp(weather_data['current']['sunset'], timezone_str)
    
    current_datetime = datetime.now()
    date_str = current_datetime.strftime('%Y-%m-%d')
    time_str = current_datetime.strftime('%H:%M:%S')
    weekday_str = current_datetime.strftime('%A')

    return {
        'date': date_str,
        'time': time_str,
        'weekday': weekday_str,
        'weather_data': weather_data
    }

tools = [get_weather_data]