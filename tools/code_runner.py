# judge0
from langchain_core.tools import tool
from datetime import datetime
from .config import config
import requests
import base64
import json
import time
import os
import re

code_runner = config.get("code_runner", {})

judge0_api_key = code_runner.get("judge0_api_key")
cpu_time_limit = code_runner.get("cpu_time_limit", 5)
wall_time_limit = code_runner.get("wall_time_limit", 8)
CACHE_FILE = "languages_cache.json"
UPDATE_INTERVAL = 2 * 24 * 60 * 60


def get_and_format_languages_as_dict():
    """
    从 Judge0 API 获取语言列表，并格式化为以语言名为键的字典。
    使用文件缓存结果，并根据指定的时间间隔更新缓存。
    """

    def fetch_from_api():
        """从 API 获取数据并更新缓存文件"""
        print("Fetching languages from API...")
        url = "https://judge0-ce.p.rapidapi.com/languages"
        headers = {
            'x-rapidapi-host': 'judge0-ce.p.rapidapi.com',
            'x-rapidapi-key': judge0_api_key,
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            languages = response.json()
            formatted_languages = {}
            for lang in languages:
                lang_id = lang["id"]
                lang_name = lang["name"]
                parts = lang_name.split("(", 1)
                name = parts[0].strip()
                if len(parts) > 1:
                    version = parts[1].replace(")", "").strip()
                else:
                    version = ""
                if name not in formatted_languages:
                    formatted_languages[name] = []
                formatted_languages[name].append({"id": lang_id, "version": version})

            # 更新缓存文件
            with open(CACHE_FILE, "w") as f:
                json.dump({"timestamp": time.time(), "data": formatted_languages}, f)
            return formatted_languages
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            # 如果API请求失败且有缓存文件，则返回缓存数据
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    cached_data = json.load(f)
                    print("Using cached data due to API error.")
                    return cached_data["data"]
            return None

    # 检查缓存文件是否存在以及是否过期
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                cached_data = json.load(f)
                timestamp = cached_data.get("timestamp", 0)
                if time.time() - timestamp < UPDATE_INTERVAL:
                    print("Using cached languages data.")
                    return cached_data["data"]
                else:
                    print("Cached data is outdated.")
                    return fetch_from_api()
            except json.JSONDecodeError:
                print("Error decoding cached data.")
                return fetch_from_api()
    else:
        print("Cache file not found.")
        return fetch_from_api()

def find_best_language_match_dict(query):
    """
    根据查询字符串在语言字典中找到最佳匹配的语言。
    """
    lang_dict = get_and_format_languages_as_dict()

    query = query.lower()
    matches = []

    # 1. 分离语言名称和版本
    match = re.match(r"([a-z]+)(\+*)(\d*\.?\d*)?", query)
    if not match:
        return None

    query_name, plus_signs, query_version = match.groups()
    query_name = query_name.strip()
    query_version = query_version.strip()

    # 2. 特殊处理 C 和 C++
    if query_name == "c" and plus_signs:
        query_name = "c++"

    for lang_name, versions in lang_dict.items():
        lang_name_lower = lang_name.lower()

        # 3. 名称匹配 (精确 + C/C++ 特殊处理)
        name_match = False
        if query_name == lang_name_lower:
            name_match = True
        elif query_name == "c++" and "c++" in lang_name_lower:
            name_match = True
        elif query_name == "c" and lang_name_lower.startswith("c "):
            name_match = True

        if name_match:
            for version_info in versions:
                lang_version = version_info["version"]

                # 4. 版本匹配 (精确 + 前缀 + 特定版本优化)
                version_match = False
                if query_version:
                    if query_version == lang_version:
                        version_match = True
                    elif lang_version.startswith(query_version):
                        version_match = True
                    # 对 C++14 和 C7 这种特定版本进行优化
                    elif query_name == "c++" and query_version == "14" and "gcc 8" in lang_version.lower():
                         version_match = True
                    elif query_name == "c" and query_version == "7" and "gcc 7" in lang_version.lower():
                         version_match = True

                else:
                    version_match = True

                if version_match:
                    matches.append((version_info, lang_version))

    if not matches:
        return None

    # 5. 排序和选择最佳匹配 (版本号排序优化)
    if len(matches) > 1:
        def sort_by_version(match_tuple):
            version_str = match_tuple[1]
            try:
                version_parts = re.findall(r'\d+', version_str)
                version_float = float(version_parts[0]) * 1000
                for i, part in enumerate(version_parts[1:]):
                    version_float += int(part) / (100 ** (i + 1))
                return version_float
            except ValueError:
                return 0

        best_match = max(matches, key=sort_by_version)[0]
    else:
        best_match = matches[0][0]
        
    if best_match:
        print(f"Query: '{query}', Best Match: {best_match}")
    else:
        print(f"Query: '{query}', No Match Found.")
    
    return best_match["id"]










def submit_code(source_code, language_id=100, stdin=None):
    """
    提交代码并获取执行结果。
    """
    url = "https://judge0-ce.p.rapidapi.com/submissions?base64_encoded=true&wait=true&fields=stdout,stderr,compile_output,exit_code,exit_signal,created_at,finished_at,time,wall_time,memory"

    payload = {
       "language_id": language_id,
       "source_code": source_code,
       "cpu_time_limit": cpu_time_limit,
       "cpu_extra_time": 1,
       "wall_time_limit": wall_time_limit
    }
    
    if stdin:
        payload["stdin"] = stdin
        
    payload = json.dumps(payload)

    headers = {
       'x-rapidapi-host': 'judge0-ce.p.rapidapi.com',
       'x-rapidapi-key': judge0_api_key,
       'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    
    try:
      response.raise_for_status()
      return response.json()
    except requests.exceptions.RequestException as e:
      print(f"An error occurred: {e}")
      return None


def format_submission_result(result):
    """
    解码 stdout 和 stderr 并格式化其他字段。
    """
    if not result:
        return None
    formatted_result = result.copy()

    # 解码 stdout
    if "stdout" in result and result["stdout"]:
        try:
            formatted_result["stdout"] = base64.b64decode(result["stdout"]).decode("utf-8")
        except Exception as e:
            formatted_result["stdout"] = f"Decode error: {e}"
    else:
        formatted_result["stdout"] = ""

    # 解码 stderr
    if "stderr" in result and result["stderr"]:
        try:
            formatted_result["stderr"] = base64.b64decode(result["stderr"]).decode("utf-8")
        except Exception as e:
            formatted_result["stderr"] = f"Decode error: {e}"
    else:
        formatted_result["stderr"] = ""

    # 格式化时间
    for key in ["created_at", "finished_at"]:
        if key in result and result[key]:
            try:
                datetime_obj = datetime.fromisoformat(result[key].replace("Z", "+00:00"))
                formatted_result[key] = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                formatted_result[key] = f"Parse error: {e}"

    # 移除 status 的id，description。
    if "status" in formatted_result:
        formatted_result.pop("status")

    return formatted_result


def base64_code(source_code, stdin=None):
    """
    对源代码进行格式化，然后进行 Base64 编码。
    如果提供了 stdin，也进行 Base64 编码。
    """
    formatted_source_code = source_code.replace('\n', '\\n').replace('"', '\\"').strip()
    code_dict = {"code": formatted_source_code}
    json_string = json.dumps(code_dict)
    encoded_source_code = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
    if stdin:
        encoded_stdin = base64.b64encode(stdin.encode("utf-8")).decode("utf-8")
    result = {"source_code": encoded_source_code}
    if stdin:
        result["stdin"] = encoded_stdin

    return result


@tool
def code_runner(source_code: str, language: str, stdin: str = None):
    """运行代码并返回详细的运行数据和结果。
    Args:
        source_code: 源代码
        language: 编程语言  e.g., "python3.12", "c++14", "c7", "c", "java", "javascript", "typescript5.0"
        stdin: 需要运行程序的标准输入，可选，默认为 None
    """
    language_id = find_best_language_match_dict(language)
    if language_id is None:
        return "未找到匹配的编程语言。"

    base64_result = base64_code(source_code, stdin)
    base64_source_code = base64_result["source_code"]
    base64_stdin = base64_result.get("stdin")
    print(base64_source_code, language_id, base64_stdin)
    result = submit_code(base64_source_code, language_id, base64_stdin)
    print(result)
    formatted_result = format_submission_result(result)
    print(formatted_result)
    return formatted_result


tools = [code_runner]

