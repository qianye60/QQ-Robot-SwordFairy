from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
import xml.etree.ElementTree as ET
from datetime import datetime
from .config import config
from .prompt.prompt import prompt_all
from pathlib import Path
import re

#获取临时目录
root_path = Path(__file__).resolve().parents[1]
temp_server_dir = root_path / "temp_server"

#获取密钥等配置
claude_svg_config = config.get("svg_card", {})

model = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=1,
    max_tokens=2048,
    max_retries=2,
    api_key=claude_svg_config.get("claude_api_key"),
    base_url=claude_svg_config.get("claude_base_url"),
    )


def create_svg(query: str, card: str):
    if system_prompt := prompt_all.get(card):
        messages = [
            SystemMessage(system_prompt),
            HumanMessage(query),
        ]
    else:
        return "未找到该卡片"
    response = model.invoke(messages)
    return response.content

def create_svg_image(svg_content: str):
    """
    从 SVG 内容中提取有效 SVG 代码并生成 SVG 图像文件，返回文件 URL。
    """
    match = re.search(r"<svg.*</svg>", svg_content, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ValueError("未找到有效的 SVG 内容。")

    svg_code = match.group(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.svg"
    filepath = temp_server_dir / filename

    try:
        root = ET.fromstring(svg_code)
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        tree = ET.ElementTree(root)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)

        file_url = f"http://127.0.0.1:5000/{filename}"
        return file_url

    except ET.ParseError as e:
        raise ValueError(f"SVG 内容解析错误: {e}")
    except Exception as e:
        raise IOError(f"写入 SVG 文件失败: {e}")


@tool
def svg_card(query: str, card: str):
    """根据 query 要求生成信息密集的 SVG 卡片。
    Args:
        query: 要生成的卡片 e.g., "神经网络" "外星人" "秦始皇统一六国" "宇宙发展史"
        card:  卡片样式 可选："common_card","mini_card"
    """
    svg_content = create_svg(query, card)
    url = create_svg_image(svg_content)
    print(url)
    return url

tools = [svg_card]

# if __name__ == "__main__":
#     svg_card("原神", "common_card")