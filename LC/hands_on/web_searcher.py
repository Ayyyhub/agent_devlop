import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch

"""
    web_searcher.py：使用 Tavily 执行网络搜索并生成摘要
"""

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")
# 加载环境变量

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")

# 1. 初始化 LLM
llm = ChatOpenAI(
    temperature=0,
    model_name="gpt-4o-mini",
    openai_api_key=openai_api_key,
    openai_api_base=openai_base_url
)

SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300"
    "words. Capture the main points. Write succinctly, no need to have complete sentences or good"
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)
search_tool = TavilySearch(max_results=5)

search_agent = create_react_agent(
    model=llm,
    prompt=SEARCH_INSTRUCTIONS,
    tools=[search_tool]
)

