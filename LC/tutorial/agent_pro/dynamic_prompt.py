from typing import TypedDict

from langchain_community.utilities import RequestsWrapper
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_core.tools import Tool
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

"""
动态系统提示
对于更高级的用例，当您需要根据运行时上下文或智能体状态修改系统提示时，可以使用中间件。
"""

class Context(TypedDict):
    user_role: str

@tool
def web_search()->str:
    tools=[]
    requests_wrapper = RequestsWrapper()
    tools.append(
        Tool(
            # - name="Requests"：工具名称（Agent 决策时会参考这个名称）；
            name="Requests",
            # - func=requests_wrapper.get：工具的核心执行函数（调用该工具时，实际执行get方法，即获取网页内容）；
            func=requests_wrapper.get,
            # - description=...：工具的描述（关键！Agent 会根据这个描述判断 “什么时候该用这个工具”，比如 “需要从 URL 获取网页内容时用”）
            description="Useful for when you need to fetch content from a URL or webpage. Input should be a valid URL."
        )
    )
    return tools

@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    """Generate system prompt based on user role."""
    user_role = request.runtime.context.get("user_role", "user")
    base_prompt = "You are a helpful assistant."

    if user_role == "expert":
        return f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        return f"{base_prompt} Explain concepts simply and avoid jargon."

    return base_prompt


agent = create_react_agent(
    model="gpt-4o",
    tools=[web_search],
    middleware=[user_role_prompt],
    context_schema=Context
)

# The system prompt will be set dynamically based on context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Explain machine learning"}]},
    context={"user_role": "expert"}
)