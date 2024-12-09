from typing import Annotated, Dict
from nonebot import on_message, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, GroupMessageEvent
from nonebot.plugin import PluginMetadata
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict
from .config import Config
import os
from langgraph.checkpoint.memory import MemorySaver
from datetime import datetime
from nonebot.params import CommandArg
from nonebot.exception import MatcherException

__plugin_meta__ = PluginMetadata(
    name="LLM Chat",
    description="基于 LangGraph 的chatbot",
    usage="@机器人 进行对话，或使用命令前缀触发对话",
    config=Config,
)

plugin_config = Config.load_config()

os.environ["OPENAI_API_KEY"] = plugin_config.llm.api_key
os.environ["OPENAI_BASE_URL"] = plugin_config.llm.base_url

class State(TypedDict):
    messages: Annotated[list, add_messages]

# 会话模板
class Session:
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.memory = MemorySaver()
        self.last_accessed = datetime.now()
        self.graph = None

sessions: Dict[str, Session] = {}

def get_or_create_session(thread_id: str) -> Session:
    """获取或创建会话"""
    if thread_id not in sessions:
        sessions[thread_id] = Session(thread_id)
    session = sessions[thread_id]
    session.last_accessed = datetime.now()
    return session

def cleanup_old_sessions():
    """清理过期的会话"""
    if len(sessions) > plugin_config.plugin.max_sessions:
        # 按最后访问时间排序，删除最旧的会话
        sorted_sessions = sorted(
            sessions.items(),
            key=lambda x: x[1].last_accessed,
            reverse=True
        )
        # 保留配置指定数量的会话
        for thread_id, _ in sorted_sessions[plugin_config.plugin.max_sessions:]:
            del sessions[thread_id]

def cleanup_old_messages(session: Session):
    """清理过期的消息"""
    max_messages = plugin_config.plugin.max_messages_per_session
    if hasattr(session.memory, 'messages') and len(session.memory.messages) > max_messages:
        # 只保留最新的消息
        session.memory.messages = session.memory.messages[-max_messages:]

graph_builder = StateGraph(State)

llm = ChatOpenAI(
    model=plugin_config.llm.model,
    temperature=plugin_config.llm.temperature,
    max_tokens=plugin_config.llm.max_tokens,
)

from .tools import load_tools
tools = load_tools(plugin_config.tools.enabled)
llm_with_tools = llm.bind_tools(tools)

from langchain_core.messages import trim_messages
trimmer = trim_messages(
    strategy="last",
    max_tokens=plugin_config.llm.max_context_messages,
    token_counter=len,
    include_system=True,
    allow_partial=False,
    start_on="human",
    end_on=("human", "tool"),
)


def chatbot(state: State):
    messages = state["messages"]
    if plugin_config.llm.system_prompt:
        messages = [SystemMessage(content=plugin_config.llm.system_prompt)] + messages
    
    trimmed_messages = trimmer.invoke(messages)
    print(trimmed_messages)
    response = llm_with_tools.invoke(trimmed_messages)
    
    return {"messages": [response]}

graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

def check_trigger(event: MessageEvent) -> bool:
    """检查是否触发对话
    支持三种触发方式：
    1. 艾特触发（默认）
    2. 关键词触发
    3. 前缀触发
    """

    msg_text = event.get_plaintext()
    
    # 命令触发
    if hasattr(plugin_config.plugin, 'command_start') and plugin_config.plugin.command_start:
        if any(msg_text.startswith(cmd) for cmd in plugin_config.plugin.command_start):
            return True
    
    # 关键词触发
    if hasattr(plugin_config.plugin, 'keywords') and plugin_config.plugin.keywords:
        if any(keyword in msg_text for keyword in plugin_config.plugin.keywords):
            return True
    
    # 默认艾特触发
    if (not hasattr(plugin_config.plugin, 'command_start') and 
        not hasattr(plugin_config.plugin, 'keywords')) or \
        plugin_config.plugin.need_at:
        return event.is_tome()
    
    return False

chat_handler = on_message(rule=check_trigger, priority=5, block=True)

@chat_handler.handle()
async def handle_chat(event: MessageEvent):
    if isinstance(event, GroupMessageEvent) and not plugin_config.plugin.enable_group:
        return
    if not isinstance(event, GroupMessageEvent) and not plugin_config.plugin.enable_private:
        return
        
    msg_text = event.get_plaintext()
    
    image_urls = []
    for seg in event.message:
        if seg.type == "image" and seg.data.get("url"):
            image_urls.append(seg.data["url"])
    
    full_content = msg_text
    print(image_urls)
    
    if image_urls:
        full_content += "\n图片：" + "\n".join(image_urls)
    
    if isinstance(event, GroupMessageEvent):
        thread_id = f"group_{event.group_id}_{event.user_id}"
    else:
        thread_id = f"private_{event.user_id}"
    
    cleanup_old_sessions()

    session = get_or_create_session(thread_id)

    cleanup_old_messages(session)

    if session.graph is None:
        session.graph = graph_builder.compile(checkpointer=session.memory)

    result = session.graph.invoke(
        {"messages": [HumanMessage(content=full_content)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    if result["messages"]:
        response = result["messages"][-1].content
    else:
        response = "对不起，我现在无法回答。"

    await chat_handler.finish(Message(response))

# 添加模型切换命令处理器
change_model = on_command("chat model", priority=1, block=True)

@change_model.handle()
async def handle_change_model(event: MessageEvent, args: Message = CommandArg()):
    model_name = args.extract_plain_text().strip()
    if not model_name:
        await change_model.finish("请指定要切换的模型名称")
        
    # 更新模型配置
    global llm, llm_with_tools
    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=plugin_config.llm.temperature,
            max_tokens=plugin_config.llm.max_tokens,
        )
        llm_with_tools = llm.bind_tools(tools)
        await change_model.finish(f"已切换到模型: {model_name}")
    except MatcherException:
        raise
    except Exception as e:
        await change_model.finish(f"切换模型失败: {str(e)}")