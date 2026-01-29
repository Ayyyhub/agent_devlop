import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

"""
    task_planner.py：将查询分解为多个搜索关键词（5-7 个）
"""
# 加载环境变量
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")

# 1. 初始化 LLM
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o-mini",
    openai_api_key=openai_api_key,
    openai_api_base=openai_base_url
)

PLANNER_INSTRUCTIONS = (
    "You are a helpful research assistant. Given a query, come up with a set of web searches "
    "to perform to best answer the query. Output between 5 and 7 search terms to query for."
)

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", PLANNER_INSTRUCTIONS),
    ("human", "{query}")
])


class WebSearchItem(BaseModel):
    """单个搜索项"""
    # Field 是 pydantic 库的工具，用来给字段加 “描述说明”,告诉AI这些字段该填什么
    query: str = Field(description="The search term to use for the web search. 用于网络搜索的关键词")
    reason: str = Field(description="Your reasoning for why this search is important to the query. 为什么这个搜索对于解答该问题很重要的理由")


class WebSearchPlan(BaseModel):
    """搜索计划"""
    # searches 是这个类的属性,代表这个字段是一个列表（List），里面可以装多个 WebSearchItem
    # 列表里的每一个元素都必须是上面定义的 WebSearchItem 类型（也就是每个元素都有 query 和 reason）
    searches: List[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query. 为了尽可能全面回答该问题而需要执行的网页搜索列表"
    )

# with_structured_output(WebSearchPlan)：让 AI 输出 “结构化数据” 的关键---告诉 AI 不要返回杂乱的文本（比如 “我觉得要搜 xxx，还要搜 xxx”），
# 而是必须按照 WebSearchPlan 这个模板来输出（也就是一个包含 searches 列表的结构，每个元素有 query 和 reason
planner_chain = planner_prompt | llm.with_structured_output(WebSearchPlan)