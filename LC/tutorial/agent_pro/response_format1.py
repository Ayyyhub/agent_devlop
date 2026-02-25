"""
提供者策略 (ProviderStrategy)
ProviderStrategy 使用模型提供者原生的结构化输出生成。这更可靠，但仅适用于支持原生结构化输出的提供者（例如 OpenAI）。

"""
from langgraph.prebuilt import create_react_agent
from langchain.agents.structured_output import ProviderStrategy

from LC.tutorial.agent_pro.response_format import ContactInfo

agent = create_react_agent(
    model="gpt-4o",
    response_format=ProviderStrategy(ContactInfo)
)