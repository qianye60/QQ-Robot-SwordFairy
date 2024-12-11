from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, trim_messages
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from .tools import load_tools
from .config import Config

plugin_config = Config.load_config()

def get_llm():
    """根据配置获取适当的 LLM 实例"""
    if plugin_config.llm.provider == "google":
        return ChatGoogleGenerativeAI(
            model=plugin_config.llm.model,
            temperature=plugin_config.llm.temperature,
            max_tokens=plugin_config.llm.max_tokens,
        )
    else:  # 默认使用 OpenAI
        return ChatOpenAI(
            model=plugin_config.llm.model,
            temperature=plugin_config.llm.temperature,
            max_tokens=plugin_config.llm.max_tokens,
        )

class State(TypedDict):
    messages: Annotated[list, add_messages]

def build_graph(config: Config, llm):
    """构建并返回对话图"""
    tools = load_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    trimmer = trim_messages(
        strategy="last",
        max_tokens=config.llm.max_context_messages,
        token_counter=len,
        include_system=True,
        allow_partial=False,
        start_on="human",
        end_on=("human", "tool"),
    )

    def chatbot(state: State):
        messages = state["messages"]
        if config.llm.system_prompt:
            messages = [SystemMessage(content=config.llm.system_prompt)] + messages
        
        trimmed_messages = trimmer.invoke(messages)
        print(trimmed_messages)
        response = llm_with_tools.invoke(trimmed_messages)
        print("----------------------------------------------------------")
        print(response)
        return {"messages": [response]}

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_conditional_edges("chatbot", tools_condition)
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    
    return graph_builder
