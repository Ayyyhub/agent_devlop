# 安装并引入需要的包
from fastapi import FastAPI
from langserve import add_routes
import uvicorn  # 修正：原代码是unicorn，拼写错误
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def server():
    # 修复：缩进错误（这行要和函数内其他代码对齐）
    load_dotenv()

    # 创建大语言模型实例（若用代理，补充base_url）
    model = ChatOpenAI(
        model="gpt-3.5-turbo",
        # base_url="https://你的GPT代理地址/v1"  # 有代理才加这行
    )

    # 定义翻译提示模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "把下面的语句翻译为{language}。"),
        ("user", "{text}")
    ])

    # 输出解析器：转为纯字符串
    parser = StrOutputParser()

    # 构建LangChain链
    chain = prompt_template | model | parser

    # 创建FastAPI应用
    app = FastAPI(
        title="LangChain Server",
        version="1.0",
        description="A simple API server using LangChain's Runnable interfaces",
    )

    # 注册翻译链为API接口
    add_routes(
        app,
        chain,
        path="/chain",
    )

    # 修复：unicorn → uvicorn（拼写错误）
    uvicorn.run(app, host="localhost", port=8000)


# 调用函数启动服务
if __name__ == "__main__":
    server()