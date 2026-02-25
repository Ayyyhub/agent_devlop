from langgraph.prebuilt import create_react_agent
from langchain.agents.middleware import wrap_tool_call
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

"""
工具错误处理:
要自定义工具错误的处理方式，请使用 @wrap_tool_call 装饰器创建中间件,
当工具失败时，智能体将返回一个包含自定义错误消息的 ToolMessage.
"""

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


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

agent = create_react_agent(
    model="gpt-4o",
    tools=[get_weather_for_location, get_user_location],
    middleware=[handle_tool_errors]
)