import fal_client
from openai import OpenAI
import os
import base64
from .config import config
from .prompt.prompt import prompt_all

draw_config = config.get("draw", {})

os.environ["FAL_KEY"] = draw_config.get("fal_key")
os.environ["OPENAI_API_KEY"] = draw_config.get("openai_api_key")
os.environ["OPENAI_BASE_URL"]= draw_config.get("openai_base_url")
model = draw_config.get("model")


def optimization_prompt(prompt: str) -> str:
    client = OpenAI()

    system_prompt = prompt_all.get("draw")
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
    )
    content = completion.choices[0].message.content.strip()
    print("Prompt Optimization: [" + content +"]")
    return content

def fal_draw(prompt: str, image_size: str = "square_hd", style: str = "any"):
    print("Conduct prompt optimization ..........")
    optimized_prompt = optimization_prompt(prompt)
    # 提交请求
    result = fal_client.submit(
        "fal-ai/recraft-v3",
        arguments={
            "prompt": optimized_prompt,
            "image_size": image_size,
            "output_format": "png",
            "style": style,
            "sync_mode": True
        }
    )

    request_id = result.request_id

    # 获取结果
    result = fal_client.result("fal-ai/recraft-v3", request_id)

    # 只处理第一张图片
    if result and result.get('images'):
        images = result['images']
        if images:  # 确保 images 列表不为空
           image = images[0]

           url = image.get('url')
           if url:
               print(f"Image URL: {url}")
               if url.startswith("data:image"):
                   try:
                       base64_data = url.split(",")[1]
                       image_data = base64.b64decode(base64_data)
                       image_file = "image.jpeg"
                       with open(image_file, "wb") as f:
                            f.write(image_data)
                       print(f"Image saved as {image_file}")
                       return image_file  # 返回本地文件路径
                   except Exception as e:
                        print(f"Error decoding or saving Base64 image: {e}")
                        return None # 如果解码失败，返回 None
               else:
                    print("URL is not a Base64 data URI.")
                    return "图片: " + url  # 返回URL
           else:
                print("Image URL not found in the response")
                return None  # 没有 URL，返回 None
        else:
            print("No images found in the response")
            return None # images 为空，返回 None
    else:
        print("Invalid result or no images in the response")
        return None  # result 或 images 不存在，返回 None


from langchain_core.tools import tool
@tool
def draw(prompt: str, image_size: str = "square_hd", style: str = "any"):
    """根据prompt要求进行绘画然后返回链接
    Args:
         prompt: 要画的内容
         image_size: 图片尺寸，可选值为 "square_hd", "square", "portrait_4_3", "portrait_16_9", "landscape_4_3", "landscape_16_9". 默认为 "square_hd"。
         style: 图片风格，可选值为 "any", "realistic_image", "digital_illustration", "vector_illustration". 默认为 "any"。
    """

    return fal_draw(prompt, image_size, style)

        
tools = [draw]