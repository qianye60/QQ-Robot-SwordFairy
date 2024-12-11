import requests
from langchain_core.tools import tool
from .config import config

jina_api_key = config.get('jina', {}).get('api_key', '')
top_n = config.get('jina', {}).get('top_n', 5)
min_length = config.get('jina', {}).get('min_length', 10)

@tool
def jina_reader(url: str):
    """Fetch webpage content by URL, filter short lines and truncate.
    Args:
        url: The URL to fetch.
    """

    url = f'https://r.jina.ai/{url}'
    headers = {
        "X-Retain-Images": "none"
    }

    if jina_api_key:
        headers["Authorization"] = f"Bearer {jina_api_key}"

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        lines = response.text.splitlines()
        filtered_lines = [line for line in lines if len(line.strip()) >= min_length]
        truncated_lines = filtered_lines[:top_n]
        result = '\n'.join(truncated_lines)

        return result
    except requests.exceptions.Timeout:
        return "内容过多，返回失败"
    except requests.exceptions.RequestException:
        return "未知错误"

tools = [jina_reader]

