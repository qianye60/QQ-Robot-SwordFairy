import requests
import re

def _get_hhlq_music(music_name):
    """
    获取红海龙淇API的音乐链接
    """
    try:
        response = requests.get(
            f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={music_name}&n=1&num=1&type=json"
        )
        music_url = re.search(r"^(https?://[^\s]+?\.mp3)", response.json()["music_url"]).group(0)
        return music_url
    except Exception as e:
        return f"获取音乐链接失败: {str(e)}"

def get_music_url(music_name: str, provider: str = "hhlq"):
    """Search and get music
    Args:
        music_name: Music name/Song title/Music title
        provider: Music provider. Available values: hhlq
    """
    provider_map = {
        "hhlq": _get_hhlq_music,
    }
    
    if provider in provider_map:
        return provider_map[provider](music_name)
    else:
        return "不支持的音乐API提供商"


url = get_music_url("告白气球", "hhlq")
print(url)
