import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")

# 全局 LLM 实例，供各个节点复用
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o-mini",
    openai_api_key=openai_api_key,
    openai_api_base=openai_base_url,
)

class EmailClassification(TypedDict):
    """大模型对邮件进行结构化分类的结果。"""

    # 分类包括————问题、错误、账单、功能, 不属于这些功能就分类为复杂
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    # 紧急程度： 低、中、高、关键
    urgency: Literal["low", "medium", "high", "critical"]
    # 邮件主题
    topic: str
    # 邮件摘要
    summary: str


# 在你定义的 agent_state.py中，
# EmailAgentState继承自 TypedDict，并且没有为字段定义特殊的 reducer（例如通过 Annotated[..., operator.add] 定义累加）。
# 在 LangGraph 的默认机制下，普通的字典键遵循 覆盖（Overwrite） 逻辑。
class EmailAgentState(TypedDict):
    """自动邮件回复 Agent 在各节点之间传递的状态。"""

    # 储存读取————邮件内容, 发件人邮件地址，邮件ID
    email_content: str
    sender_email: str
    email_id: str

    # 分类意图节点的结果
    classification: EmailClassification

    # Bug tracking 错误处理系统只需要查询一些 API， 这里就存储一个工单 ID 即可
    ticket_id: str | None

    # 搜索文档结果
    search_results: list[str] | None
    # 客户历史：客户历史是一个字典，键是客户的电子邮件，值是与该客户相关的任何搜索结果
    customer_history: dict | None

    # 回复邮件的生成内容
    draft_response: str | None

