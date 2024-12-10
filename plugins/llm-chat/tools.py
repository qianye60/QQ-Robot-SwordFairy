from typing import List, Dict, Optional
from langchain.tools import BaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
import importlib.util
import sys
import os
from pathlib import Path
import tomli

# 内置工具定义
BUILTIN_TOOLS: Dict[str, BaseTool] = {
    "tavily_search": lambda: TavilySearchResults(max_results=2)
}

def load_tools(enabled_tools: Optional[List[str]] = None, tool_paths: Optional[List[str]] = None) -> List[BaseTool]:
    """加载启用的工具

    Args:
        enabled_tools: 可选的已启用工具列表,如果为None则从配置文件加载
        tool_paths: 可选的工具路径列表
    """
    all_tools = []

    if enabled_tools is None:
        root_path = Path(__file__).resolve().parents[2]
        config_path = root_path / "config-tools.toml"

        try:
            with open(config_path, "rb") as f:
                config = tomli.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Tools config file not found at {config_path}")

        # 初始化内置工具配置
        tavily_config = config.get("tavily")
        if tavily_config and "api_key" in tavily_config:
            os.environ["TAVILY_API_KEY"] = tavily_config["api_key"]

        # 加载内置工具
        builtin_tools = config.get("tools", {}).get("builtin", [])
        for name in builtin_tools:
            tool = BUILTIN_TOOLS.get(name)
            if tool:
                all_tools.append(tool())
            else:
                print(f"Warning: Built-in tool {name} not found")


        # 加载外部工具
        enabled_tools = config.get("tools", {}).get("enabled", [])

    search_paths = [str(Path(__file__).resolve().parents[2])]
    if tool_paths:
        search_paths.extend(tool_paths)

    for path in search_paths:
        if path not in sys.path:
            sys.path.insert(0, path)

    for name in enabled_tools:
        try:
            module = importlib.import_module(f"tools.{name.replace('-', '_')}")
            all_tools.extend(module.tools if hasattr(module, 'tools') else [])
        except (ModuleNotFoundError, ImportError) as e:
            print(f"Error loading tool {name}: {str(e)}")


    return all_tools