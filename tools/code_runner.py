# judge0
# 测试通过语言: Assembly,Bash,C,C++,Clojure,C#,COBOL,Common Lisp,D,Elixir,F#,Fortran,Go,Groovy,Haskell,Java,JavaScript,Kotlin,Lua,OCaml,Octave,Pascal,Perl,PHP,Plain Text,Python,Python2,R,Ruby,Rust,Scala,SQL,Swift,TypeScript,Visual Basic.Net
from langchain_core.tools import tool
from datetime import datetime, timezone, timedelta
from .config import config
import requests
import base64
import json
import re

code_runner = config.get("code_runner", {})

judge0_api_key = code_runner.get("judge0_api_key")
cpu_time_limit = code_runner.get("cpu_time_limit", 5)
wall_time_limit = code_runner.get("wall_time_limit", 8)
judge0_url = code_runner.get("judge0_url")
CACHE_FILE = "languages_cache.json"
UPDATE_INTERVAL = 2 * 24 * 60 * 60
# submit_fields = "stdout,stderr,compile_output,exit_code,exit_signal,created_at,finished_at,time,wall_time,memory,source_code"
submit_fields = "*"
# 定义需要转义的字符
escaped_chars = {
        '\\': '\\\\',
        '\n': '\\n',
        '\t': '\\t',
        '\r': '\\r',
        '\b': '\\b',
        '\f': '\\f',
        '\a': '\\a',
        '"': '\\"',
        "'": "\\'"
}

# 语言匹配id
def get_and_format_languages_as_dict():
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    languages = data["data"]
    formatted_languages = {}
    for lang, versions in languages.items():
        formatted_languages[lang] = versions
    return formatted_languages

def normalize_language_name(query_name):
    """规范化语言名称"""
    name_mapping = {
        "c#": "csharp",
        "objective-c": "objective-c",
        "objectivec": "objective-c",
        "plain text": "plain text",
        "visual basic.net": "visual basic.net",
        "visual basic net": "visual basic.net",
        "vb.net": "visual basic.net",
        "objc": "objective-c", # 添加 objc 作为 objective-c 的别名
    }
    return name_mapping.get(query_name, query_name)
    
def is_name_match(query_name, lang_name_lower):
    """判断语言名称是否匹配"""
    if query_name == lang_name_lower:
        return True
    if query_name == "c++" and "c++" in lang_name_lower:
        return True
    if query_name == "c" and lang_name_lower.startswith("c "):
        return True
    if query_name == "csharp" and "c#" in lang_name_lower:
        return True
    if query_name == "objective-c" and ("objective-c" in lang_name_lower  or "Objective-C" in lang_name_lower):
         return True
    if query_name == "plain text" and "plain text" in lang_name_lower:
        return True
    if query_name == "visual basic.net" and "visual basic.net" in lang_name_lower:
        return True
    return False
    
def is_version_match(query_name, query_version, lang_version):
    """判断版本是否匹配"""
    if not query_version:
        return True
    if query_version == lang_version:
        return True
    if lang_version.startswith(query_version):
        return True
    if query_name == "c++" and query_version == "14" and "gcc 8" in lang_version.lower():
        return True
    if query_name == "c" and query_version == "7" and "gcc 7" in lang_version.lower():
        return True
    return False

def find_best_language_match_dict(query):
    """
    根据查询字符串在语言字典中找到最佳匹配的语言。
    """
    lang_dict = get_and_format_languages_as_dict()

    query = query.lower()
    matches = []

    # 1. 分离语言名称和版本
    match = re.match(r"([a-z#\.\s]+)(\+*)(\d*\.?\d*)?", query)
    if not match:
        return None

    query_name, plus_signs, query_version = match.groups()
    query_name = query_name.strip()
    query_version = query_version.strip()

    # 2. 特殊处理 C/C++ 和规范化语言名称
    if query_name == "c" and plus_signs:
        query_name = "c++"
    query_name = normalize_language_name(query_name)

    for lang_name, versions in lang_dict.items():
        lang_name_lower = lang_name.lower()

        # 3. 名称匹配 
        if is_name_match(query_name, lang_name_lower):
            for version_info in versions:
                lang_version = version_info["version"]

                # 4. 版本匹配
                if is_version_match(query_name, query_version, lang_version):
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
    url = f"{judge0_url}/submissions?base64_encoded=true&wait=true&fields={submit_fields}"

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
       'X-Auth-Token': judge0_api_key,
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
    解码 stdout, stderr 和 compile_output 并格式化其他字段。
    """
    if not result:
        return None
    formatted_result = result.copy()

    # 解码 stdout, stderr, compile_output
    for key in ["stdout", "stderr", "compile_output", "source_code", "message"]:
        if key in result and result[key]:
            try:
                formatted_result[key] = base64.b64decode(result[key]).decode("utf-8")
            except Exception as e:
                formatted_result[key] = f"Decode error: {e}"
        else:
            formatted_result[key] = ""

    # 格式化时间为中国时间
    china_tz = timezone(timedelta(hours=8))
    for key in ["created_at", "finished_at"]:
        if key in result and result[key]:
            try:
                datetime_obj = datetime.fromisoformat(result[key].replace("Z", "+00:00"))
                china_time = datetime_obj.astimezone(china_tz)
                formatted_result[key] = china_time.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                formatted_result[key] = f"Parse error: {e}"

    # 移除 status 的id，description。
    if "status" in formatted_result:
        formatted_result.pop("status")

    return formatted_result


def base64_code(source_code, stdin=None):
    """
    对源代码进行 Base64 编码。
    如果提供了 stdin，也进行 Base64 编码。
    """
    # 彻底去除多余的反斜杠
    source_code = source_code.replace('\\\\', '\\')
    # 彻底处理 HTML 实体编码
    source_code = source_code.replace('[', '[').replace(']', ']')
    # 去除多余的换行符
    source_code = source_code.replace('\\n', '\n')
    
    encoded_source_code = base64.b64encode(source_code.encode("utf-8")).decode("utf-8")
    result = {"source_code": encoded_source_code}
    if stdin:
        encoded_stdin = base64.b64encode(stdin.encode("utf-8")).decode("utf-8")
        result["stdin"] = encoded_stdin

    return result


@tool
def code_runner(source_code: str, language: str, stdin: str = None):
    """运行代码并返回详细的运行数据和结果。
    Args:
        source_code: 保持原格式的源代码
        language: 编程语言  e.g., "python3", "python2", "c++14", "c7", "c", "java", "javascript", "typescript5"
        stdin: 需要运行程序的标准输入，可选，默认为 None
    """
    # print("********************")
    # print(source_code)
    # print("********************")
    language_id = find_best_language_match_dict(language)
    if language_id is None:
        return "未找到匹配的编程语言。"

    # # 对源代码中的特殊字符进行转义
    # for char, escaped_char in escaped_chars.items():
    #     source_code = source_code.replace(char, escaped_char)
    base64_result = base64_code(source_code, stdin)
    base64_source_code = base64_result["source_code"]
    base64_stdin = base64_result.get("stdin")
    # print(base64_source_code, language_id, base64_stdin)
    result = submit_code(base64_source_code, language_id, base64_stdin)
    # print(result)
    formatted_result = format_submission_result(result)
    print(formatted_result)
    return formatted_result


tools = [code_runner]




# 全部语言测试
# if __name__ == "__main__":
    # test_cases = {
    #     "Assembly": {
    #         "code": "section .data\n    msg db 'Hello, World!', 0x0A\n    len equ $ - msg\n\nsection .text\n    global _start\n\n_start:\n    mov eax, 4\n    mov ebx, 1\n    mov ecx, msg\n    mov edx, len\n    int 0x80\n\n    mov eax, 1\n    xor ebx, ebx\n    int 0x80",
    #         "language": "Assembly",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Bash": {
    #         "code": "echo 'Hello, World!'",
    #         "language": "Bash",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Basic": {
    #         "code": "10 PRINT \"Hello, World!\"\n20 END",
    #         "language": "Basic",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "C": {
    #         "code": "#include <stdio.h>\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}",
    #         "language": "C",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "C++": {
    #         "code": "#include <iostream>\nint main() {\n    std::cout << \"Hello, World!\" << std::endl;\n    return 0;\n}",
    #         "language": "C++",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Clojure": {
    #         "code": '(println "Hello, World!")',
    #         "language": "Clojure",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "C#": {
    #         "code": "using System;\npublic class Program {\n    public static void Main(string[] args) {\n        Console.WriteLine(\"Hello, World!\");\n    }\n}",
    #         "language": "C#",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "COBOL": {
    #         "code": "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO-WORLD.\n       PROCEDURE DIVISION.\n           DISPLAY \"Hello, World!\".\n           STOP RUN.",
    #         "language": "COBOL",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Common Lisp": {
    #         "code": '(format t "Hello, World!~%")',
    #         "language": "Common Lisp",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "D": {
    #         "code": "import std.stdio;\nvoid main() {\n    writeln(\"Hello, World!\");\n}",
    #         "language": "D",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Elixir": {
    #         "code": "IO.puts \"Hello, World!\"",
    #         "language": "Elixir",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Erlang": {
    #         "code": "-module(main).\n-export([main/0]).\nmain() ->\n    io:fwrite(\"Hello, World!\\n\").",
    #         "language": "Erlang",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Executable": {
    #         "code": "",  # 可执行文件需要预先编译好
    #         "language": "Executable",
    #         "expected_output": ""
    #     },
    #     "F#": {
    #         "code": "printfn \"Hello, World!\"",
    #         "language": "F#",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Fortran": {
    #         "code": "program hello\n    print *, 'Hello, World!'\nend program hello",
    #         "language": "Fortran",
    #         "expected_output": " Hello, World!\n"
    #     },
    #     "Go": {
    #         "code": "package main\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello, World!\")\n}",
    #         "language": "Go",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Groovy": {
    #         "code": "println 'Hello, World!'",
    #         "language": "Groovy",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Haskell": {
    #         "code": "main = putStrLn \"Hello, World!\"",
    #         "language": "Haskell",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Java": {
    #         "code": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}",
    #         "language": "Java",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "JavaScript": {
    #         "code": "console.log('Hello, World!');",
    #         "language": "JavaScript",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Kotlin": {
    #         "code": "fun main() {\n    println(\"Hello, World!\")\n}",
    #         "language": "Kotlin",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Lua": {
    #         "code": "print('Hello, World!')",
    #         "language": "Lua",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Objective-C": {
    #         "code": "#import <Foundation/Foundation.h>\nint main() {\n    @autoreleasepool {\n        NSLog(@\"Hello, World!\");\n    }\n    return 0;\n}",
    #         "language": "Objective-C",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "OCaml": {
    #         "code": "print_endline \"Hello, World!\";;",
    #         "language": "OCaml",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Octave": {
    #         "code": "disp('Hello, World!');",
    #         "language": "Octave",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Pascal": {
    #         "code": "program HelloWorld;\nbegin\n    writeln('Hello, World!');\nend.",
    #         "language": "Pascal",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Perl": {
    #         "code": "print \"Hello, World!\\n\";",
    #         "language": "Perl",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "PHP": {
    #         "code": "<?php\necho 'Hello, World!\\n';\n?>",
    #         "language": "PHP",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Plain Text": {
    #         "code": "Hello, World!",
    #         "language": "Plain Text",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Prolog": {
    #         "code": "main :- write('Hello, World!'), nl.",
    #         "language": "Prolog",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Python": {
    #         "code": "print('Hello, World!')",
    #         "language": "Python",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Python2": {
    #         "code": "print 'Hello, World!'",
    #         "language": "Python2",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "R": {
    #         "code": "print(\"Hello, World!\")",
    #         "language": "R",
    #         "expected_output": "[1] \"Hello, World!\"\n"
    #     },
    #     "Ruby": {
    #         "code": "puts 'Hello, World!'",
    #         "language": "Ruby",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Rust": {
    #         "code": "fn main() {\n    println!(\"Hello, World!\");\n}",
    #         "language": "Rust",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Scala": {
    #         "code": "object Main extends App {\n  println(\"Hello, World!\")\n}",
    #         "language": "Scala",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "SQL": {
    #         "code": "SELECT 'Hello, World!';",
    #         "language": "SQL",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Swift": {
    #         "code": "print(\"Hello, World!\")",
    #         "language": "Swift",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "TypeScript": {
    #         "code": "console.log('Hello, World!');",
    #         "language": "TypeScript",
    #         "expected_output": "Hello, World!\n"
    #     },
    #     "Visual Basic.Net": {
    #         "code": "Module Module1\n    Sub Main()\n        Console.WriteLine(\"Hello, World!\")\n    End Sub\nEnd Module",
    #         "language": "Visual Basic.Net",
    #         "expected_output": "Hello, World!\n"
    #     }
    # }
    
    # for lang_data in test_cases.values():
    #     result = code_runner(lang_data["code"], lang_data["language"])
    #     print(f"Language: {lang_data['language']}")
    #     print(f"Result: {result}")
    #     print("-" * 20)
    
