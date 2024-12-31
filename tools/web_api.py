# tools/web_api.py
import requests
from langchain_core.tools import tool
from .config import config
import os
import re

import os
@tool
def web_api(webside:str=None,music:str=None,select_api:str=None):
  """根据用户请求合理判断并请求相应的api接口然后返回。
  Args:
    select_api:
        根据用户请求，从下列的api功能字典的键和值中寻找类似功能，键是功能名字，将要和变量的值一样，值是触发所需要的含义和请求参数列表，如果下列参数为可选，且用户没有指定将为None，含义相似即可，若是未找到将不为字符串变量赋值，就是默认的None。如果用户请求功能列表或者功能大全、说明之类就组织下列字典发送。
        {
            "小姐姐短视频":["关键含义:随机小姐姐、随机短视频","None"],
            "TCPing":["关键含义":"测试网站、ping网站","webside='网站网址'(必填)"],
            "点歌":"["关键含义":"点歌、歌曲、网易云歌曲","music:'音乐名称'"]",
        }
    *argument:所有参数类型都为字符串str,更具select_api的参数说明来决定有多少个参数，每个参数有什么意思，代表着什么。
  """
  try:
    if select_api == "小姐姐短视频":
        response_url = requests.get("http://tucdn.wpon.cn/api-girl/index.php?wpon=url")
        url = "https://"+response_url.text[2:]
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




