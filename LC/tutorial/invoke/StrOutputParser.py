from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
"""
invoke只要记住：想让某个 LangChain 组件 “干活”，就给它传输入，然后调它的invoke()，就能拿到结果
"""
def a():
    # 加载.env文件的环境变量
    load_dotenv()

    # 创建一个大语言模型，model指定了大语言模型的种类
    model = ChatOpenAI(model="gpt-3.5-turbo")

    # 定义传递给模型的消息队列
    # SystemMessage的content指定了大语言模型的身份，即他应该做什么，对他进行设定
    # HumanMessage的content是我们要对大语言模型说的话，即用户的输入
    messages = [
        SystemMessage(content="把下面的语句翻译为英文。"),
        HumanMessage(content="今天天气怎么样？"),
    ]
    ##### 方法一，parser对象 ######
    # 使用result接收模型的输出，result就是一个AIMessage对象
    result = model.invoke(messages)

    # 定义一个解析器对象
    parser = StrOutputParser()

    # 使用解析器对result进行解析
    translated_text = parser.invoke(result)
    print("翻译结果：", translated_text)

    # ##### 方法二，有专门打印AIMessage对象的方法 pretty_print() #####
    # model.invoke(messages).pretty_print()


if __name__ == "__main__":
    a()