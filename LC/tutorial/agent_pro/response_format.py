"""
在某些情况下，您可能希望智能体以特定格式返回输出。LangChain 通过 response_format 参数提供结构化输出策略。
工具策略 (ToolStrategy)
ToolStrategy 使用人工工具调用来生成结构化输出。这适用于任何支持工具调用的模型。
"""
from langchain_community.utilities import RequestsWrapper
from langchain_core.tools import tool
from langchain_core.tools import Tool
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

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

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str

agent = create_agent(
    model="gpt-4o-mini",
    tools=[web_search],
    response_format=ToolStrategy(ContactInfo)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})

result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')