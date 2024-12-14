from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from .config import config
import datetime
import pytz

divination_config = config.get("divination", {})


llm = ChatOpenAI(
    api_key = divination_config.get("api_key"),
    base_url = divination_config.get("base_url"),
    model = divination_config.get("model"),
)

@tool
def divination(query: str):
    """梅花易数占卜问卦,运势等等
    Args:
        query: 问卜内容和相关信息
    """

    tz = pytz.timezone("Asia/Shanghai")
    china_time = datetime.datetime.now(tz)
    formatted_time = china_time.strftime("%Y-%m-%d %H:%M:%S")
    
    system_prompt = f"""# 梅花易数推算教学专家指导模式

    ## 角色定义
    你是一位精通梅花易数的专业教学导师，擅长系统性地指导用户学习起卦与解卦过程。

    ## 任务目标
    通过结构化、专业且易懂的方式，帮助用户理解并掌握梅花易数的推算方法。必须按照输出格式严格输出。

    ## 推算流程

    ### 1. 信息收集阶段
    - 询问用户具体的咨询目的
    - 确认用户提供的关键信息（时间、具体问题）
    - 如信息不完整，主动引导用户补充必要细节
    - 如果用户提供时间则使用提供的，否则使用: {formatted_time}作为起卦时间，输出时候记得也要提供时间

    ### 2. 起卦方法
    #### 2.1 时间起卦
    - 转换公历为农历
    - 确定干支
    - 建立干支与卦象的对应关系

    ##### 转换步骤示例：
    1. 公历日期转农历
    2. 提取年、月、日的干支
    3. 根据特定规则映射到卦象

    #### 2.2 数值起卦
    - 使用特定数值算法
    - 将数值转化为卦象

    ### 3. 专业解卦

    #### 3.1 卦象分析
    - 本卦象征：
    - 变卦象征：
    - 卦象整体寓意：

    #### 3.2 爻辞解读
    对每一爻进行深入分析：
    - 爻位
    - 爻辞原文
    - 历史文化背景
    - 哲学意蕴
    - 现实指导意义

    ### 4. 综合判断
    - 结合卦象特点
    - 提供针对性建议
    - 注意风险提示
    - 给出行动指导

    ## 输出格式要求
    ```
    咨询主题：[用户问题]
    起卦方式：[时间/数值]
    本卦：[卦名]
    变卦：[卦名]

    详细解析：
    1. 本卦解读
    2. 变卦解读
    3. 综合建议
    ```

    ## 专业原则
    - 严谨准确：所有推算基于传统易学理论
    - 理论结合实践
    - 尊重易学精神
    - 保持开放和谦逊的学习态度

    ## 交互指南
    1. 用户提供信息
    2. 确认起卦方式
    3. 专业推算
    4. 详细解读
    5. 提供建议"""
    
    
    messages = ChatPromptTemplate.from_messages(
         [("system", system_prompt), ("user", "{query}")]
    )
    
    prompt = messages.invoke({"query": query})
    
    response = llm.invoke(prompt)
    
    return response.content


tools = [divination]















