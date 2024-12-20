import toml
from pathlib import Path
from typing import Dict

def load_toml_data(folder_name: str) -> Dict[str, Dict]:
    """
    加载指定文件夹下所有 .toml 文件中的数据。
    """
    data_folder = Path(__file__).resolve().parents[1] / folder_name
    print(data_folder)
    all_data: Dict[str, Dict] = {}

    if not data_folder.exists():
        print(f"错误：文件夹 '{data_folder}' 不存在。")
        return all_data

    for file_path in data_folder.glob("*.toml"):
        variable_name = file_path.stem

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = toml.load(f)
                if variable_name in data:
                    all_data[variable_name] = data[variable_name]
                else:
                    print(f"警告：变量 '{variable_name}' 在文件 '{file_path.name}' 中未找到，已跳过。")
        except toml.TomlDecodeError as e:
            print(f"错误：文件 '{file_path.name}' 不是有效的 TOML 文件 - {e}")
        except Exception as e:
            print(f"处理文件 '{file_path.name}' 时发生意外错误：{e}")

    return all_data

prompt_all = load_toml_data("prompt")

# print(prompt.get("common_card"))
# print(prompt["common_card"])