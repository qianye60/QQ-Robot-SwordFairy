# tools/web_api.py
import requests
from langchain_core.tools import tool
from .config import config
import os
import re

import os
@tool(parse_docstring=True)
def web_api(webside:str=None,music:str=None,video:str=None,select_api:str=None) -> str:
    """根据用户请求合理判断并请求相应的api接口然后返回。
    
    Args:
      select_api:
          根据用户请求，从下列的api功能中寻找类似功能，键是功能名字，将要和变量的值一样，值是触发所需要的含义
            1、"短视频"，["关键含义，视频、随机短视频、短视频"],
            2、"TCPing"，["关键含义"，"测试网站、ping网站"],
            3、"点歌"，"["关键含义"，"点歌、歌曲、网易云歌曲"]"
      webside:str,网站网址。
      music:str,音乐名称。
      video:str,根据用户选择视频类型,从这[“小姐姐”、“纯情女高”、“蛇姐”、“玉足”]其中选择一个，意思或读音大概即可，都匹配不上就选择“小姐姐”。
    """
    try:
      if select_api == "短视频":
          if video == "玉足":
            response = requests.get("https://api.yuafeng.cn/API/ly/yzxl.php")
            url = response.url
          elif video == "纯情女高":
            response = requests.get("https://api.yuafeng.cn/API/ly/cqng.php")
            url = response.url
          elif video == "蛇姐":
            response = requests.get("https://api.yuafeng.cn/API/ly/sjxl.php")
            url = response.url
          else:
            response = requests.get("http://tucdn.wpon.cn/api-girl/index.php?wpon=url")
            url = "https://"+response.text[2:]
          print(url)
          return url
      elif select_api == "TCPing":
          response = requests.get(f"https://api.mmp.cc/api/ping?text={webside}")
          print(response.url)
          status = response.json()["status"]
          delay = response.json()["延迟"]
          IP = response.json()["IP"]
          IP_addr = response.json()["IP地址"]
          print(delay)
          return f"网站地址:{webside}\n状态:{status}\n延迟:{delay}\nIP:{IP}\nIP的地址:{IP_addr}"
      elif select_api == "点歌":
        response = requests.get(f"https://www.hhlqilongzhu.cn/api/dg_wyymusic.php?gm={music}&n=1&num=1&type=json")
        musci_url = re.search(r"^(https?://[^\s]+?\.mp3)", response.json()["music_url"]).group(0)
        return musci_url
      else:
          return print(f"选择为:{select_api},未能获取请求！")
    except Exception as e:
      print(f"select_api出现错误: {e}")
      return None
tools = [web_api]




