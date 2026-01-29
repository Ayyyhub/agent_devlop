"""
天气预测 Agent 示例 - 使用 LangChain 新 API

功能说明：
1. 创建一个会说双关语的天气预测专家 Agent
2. 使用自定义工具获取天气和用户位置
3. 支持结构化输出和对话记忆
4. 演示如何使用 context 和 checkpointer

"""
from dataclasses import dataclass
from typing import Union

from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
# from langgraph.agents import create_agent, AgentState
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver


# Define system prompt
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""


# LangChain（或对应 Agent 框架）的工具装饰器，标记该函数为 Agent 可调用的工具
@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


# 标记该函数为 Agent 可调用的工具；
@tool
def get_user_location() -> str:
    """Retrieve user information based on user ID from context.

    Note: This is a simplified version. In a production environment,
    you would access the runtime context through ToolRuntime or similar mechanism.
    """
    # 简化版本：返回默认位置
    # 在实际应用中，需要通过运行时上下文获取 user_id
    # 这里暂时返回一个默认值，实际使用时需要通过 context 传递
    return "Florida"


# 标记该类为数据类，自动生成__init__等方法，方便初始化和使用
@dataclass
class Context:
    # 注释：自定义运行时上下文的结构模板
    """Custom runtime context schema."""
    # 定义上下文的核心字段：用户 ID（字符串类型），工具可通过这个字段区分不同用户
    user_id: str


# 标记为数据类，自动生成初始化方法，确保结构化输出；
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # 必选字段：存储 Agent 的双关语回复（字符串类型，无默认值，必须返回）；
    punny_response: str
    # 可选字段：存储天气信息（字符串或 None，默认值 None，无天气信息时返回 None）。
    weather_conditions: Union[str, None] = None


def create_weather_agent():
    """创建天气预测 Agent"""
    load_dotenv()
    # Configure model，支持多种（OpenAI、Claude、Gemini 等），自动从环境变量中获取配置
    model = init_chat_model(
        "gpt-4o-mini",
        # "gpt-3.5-turbo",
        temperature=0
    )
    # 初始化内存存储器（会话记忆组件）：
    # - 作用是保存会话历史（通过thread_id区分不同会话）；
    # - InMemorySaver表示将记忆存在内存中（重启程序后丢失，生产环境可替换为持久化存储）。
    memory_checkpointer = InMemorySaver()

    # 创建 Agent 核心对象，传入关键配置：
    agent = create_react_agent(
        model=model,                                            # - model=model：绑定 Claude 模型（Agent 的 “大脑”）；
        prompt=SYSTEM_PROMPT,                                   # - system_prompt=SYSTEM_PROMPT：传入系统指令，定义 Agent 的行为规则；
        tools=[get_user_location, get_weather_for_location],    # - tools=[...]：传入 Agent 可调用的工具列表；
        context_schema=Context,                                 # - context_schema=Context：指定运行时上下文的结构（创建agent时注册，告诉 Agent 能接收哪些上下文参数）；
        checkpointer=memory_checkpointer,                       # - checkpointer=checkpointer：绑定记忆组件，实现会话记忆；
        response_format=ResponseFormat,                         # - response_format=ResponseFormat：强制 Agent 按该格式返回结果；
        # response_format={"type": "json_object"}               # 可选：结构化输出配置（如果需要固定格式）
    )
    
    return agent


def run_weather_queries():
    """执行天气查询示例"""
    # Create agent
    agent = create_weather_agent()
    
    # 定义 Agent 的配置：
    # - thread_id="1"：会话唯一标识（同一会话用相同 ID，Agent 会通过这个 ID 读取 / 保存记忆）；
    # - 作用：实现 “多会话隔离”，不同thread_id的对话互不干扰。
    usid_config = {"configurable": {"thread_id": "1"}}
    
    # First query: Ask about weather
    print("=" * 60)
    print("查询 1：询问天气")
    print("=" * 60)
    
    try:
        # 调用 Agent 执行第一个查询：
        # - {"messages": [...]}：传入用户消息（角色 = user，内容 =“外面天气怎么样？”）；
        # - config=config：传入会话配置（绑定 thread_id=1）；
        # - context=Context(user_id="1")：传入上下文（用户 ID=1，工具会基于此返回 Florida）；
        # - Agent 执行逻辑：
        # 1. 识别用户问天气但未指定位置 → 调用get_user_location工具；
        # 2. 工具返回 Florida → 调用get_weather_for_location工具获取 Florida 天气；
        # 3. 生成双关语回复，按ResponseFormat格式返回。
        response = agent.invoke(
            {"messages": [{"role": "user", "question": "what is the weather outside?"}]},
            config=usid_config,
            context=Context(user_id="1")
        )
        
        print("\n结构化响应：")
        print(response['structured_response'])

    except Exception as e:
        print(f"查询失败：{e}")
        return
    
    # Second query: Continue conversation (using same thread_id)
    print("\n\n" + "=" * 60)
    print("查询 2：继续对话（使用相同的 thread_id）")
    print("=" * 60)
    
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "question": "thank you!"}]},
            config=usid_config,
            context=Context(user_id="1")
        )
        
        print("\n结构化响应：")
        print(response['structured_response'])

    except Exception as e:
        print(f"查询失败：{e}")


if __name__ == '__main__':
    run_weather_queries()