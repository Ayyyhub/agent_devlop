# 概括来说，使用文档作为上下文进行QA系统的构建过程类似于 llm(your context + your question) = your answer
# Simple Q&A Example
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def a():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    context = """
    Rachel is 30 years old
    Bob is 45 years old
    Kevin is 65 years old
    """

    question = "Who is under 40 years old?"

    # from_messages是带角色的对话式Prompt，适合Chat模型的交互逻辑，规则和输入分工清晰；
    # from_template是无角色的纯文本Prompt，适合简单场景，兼容性强但不够贴合Chat模型；
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("user", "context:{context} question:{question}")
    ])
    # 把传入的参数值填充到 Prompt 模板的对应占位符里，生成 Chat 模型能识别的「角色 + 内容」消息列表（和invoke()类似，但invoke()返回ChatPromptValue对象，format_messages()直接返回消息列表，更底层）。
    messages = prompt.format_messages(context=context, question=question)
    output = llm.invoke(messages)
    parser = StrOutputParser()
    result = parser.invoke(output)
    print(result)

if __name__ == "__main__":
    a()