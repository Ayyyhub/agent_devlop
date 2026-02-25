from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


def a():
    load_dotenv()
    model = ChatOpenAI(model="gpt-3.5-turbo")

    messages = [
        SystemMessage(content="把下面的语句翻译为英文。"),
        HumanMessage(content="飞流直下三千尺，百尺高楼平地起"),
    ]
    print("messages的结构：", messages)  # 原messages的结构（包含多个字段）

    # 把模型返回的结果存到变量里
    ai_response = model.invoke(messages)
    print("\nAIMessage的完整结构：", ai_response)  # 打印完整的AIMessage对象
    print("\n只取content字段：", ai_response.content)  # 只取文本内容
    # print(model.invoke(messages).content)


if __name__ == "__main__":
    a()