from typing import List
from langchain.tools import BaseTool
import importlib.util
import sys
from pathlib import Path

def load_tools(tool_names: List[str]) -> List[BaseTool]:
    all_tools = []
    
    # 获取项目根目录
    root_path = Path(__file__).parent.parent.parent
    tools_dir = root_path / "tools"
    
    # 确保 tools 目录在 Python 路径中
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))
    
    # 加载工具
    for name in tool_names:
        try:
            module = importlib.import_module(f"tools.{name.replace('-', '_')}")
            if hasattr(module, 'tools'):
                all_tools.extend(module.tools)
            else:
                print(f"Warning: Tool module {name} does not have 'tools' list")
        except Exception as e:
            print(f"Error loading tool {name}: {str(e)}")
            continue
    
    return all_tools