from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# LangChain Expression Language 其实他的用处就是使用 “|” 运算符链接LangChain应用的各个组件，如提示词模版ChatPromptTemplate、大语言模型ChatOpenAI、输出解析器StrOutputParser

def a():
    # 加载.env文件的环境变量
    load_dotenv()

    # 创建一个大语言模型，model指定了大语言模型的种类
    model = ChatOpenAI(model="gpt-3.5-turbo")

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "把下面的语句翻译为{language}。"),
        ("user", "{text}")]
    )
    parser = StrOutputParser()

    chain = prompt_template | model | parser

    print(chain.invoke({"language": "英文", "text": "今天天气怎么样？"}))


if __name__ == "__main__":
    a()