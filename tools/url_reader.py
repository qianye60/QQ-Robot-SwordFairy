import requests
from langchain_core.tools import tool
from .config import config

jina_api_key = config.get('jina', {}).get('api_key', '')
print(jina_api_key)

@tool
def url_reader(url):
    """Fetch webpage content by URL
    Args:
        url: The URL to fetch.
    """
    
    headers = {
        "X-Retain-Images": "none",
        "X-Locale": "en-US",
    }

    if jina_api_key:
        headers["Authorization"] = f"Bearer {jina_api_key}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        return "内容过多，返回失败"
    except requests.exceptions.RequestException:
        return "未知错误"

tools = [url_reader]
