import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

"""
    txt_writer.py：将搜索结果整合为结构化的 Markdown 报告
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


class ReportData(BaseModel):
    """研究报告数据"""
    markdown_report: str = Field(description="The final markdown formatted research report. 最终生成的markdown格式研究报告")


WRITER_PROMPT = (
    "You are a senior researcher tasked with writing a cohesive report for a research query."
    "You will be provided with the original query, and some initial research done by a research assistant. \n"
    "You should first come up with an outline for the report that describes the structure and flow of the report. Then, "
    "generate the report and return that as your final output. \n The final output should be in markdown format, and it should"
    "be lengthy and detailed. Aim for 10-20 pages of content, at least 1500 words. 最终生成的报告采用中文输出."
)

writer_prompt = ChatPromptTemplate.from_messages([
    ('system', WRITER_PROMPT),
    ('human', '{query}')
])

writer_chain = writer_prompt | llm.with_structured_output(ReportData)

