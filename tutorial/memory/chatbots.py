"""
带记忆功能的聊天机器人示例（使用 LangChain 0.3.x 新 API）

功能说明：
1. 使用 ChatMessageHistory 和 RunnableWithMessageHistory 保存对话历史
2. 每次对话都会包含之前的上下文
3. 演示如何构建一个能记住之前对话的聊天机器人

注意：使用 LangChain 0.3.x 的新 API（LCEL + RunnableWithMessageHistory）
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory


def chat_with_memory():
    """使用记忆功能的聊天机器人（新 API，无弃用警告）"""
    # 加载环境变量
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 初始化 LLM
    llm = ChatOpenAI(
        temperature=0.7,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # 使用 ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a chatbot that is unhelpful.
            Your goal is to not help the user but only make jokes.
            Take what the user is saying and make a joke out of it."""),
        MessagesPlaceholder(variable_name="history"),  # 历史消息占位符，运行时会被实际的会话历史替换，是实现 “记忆” 的关键
        ("human", "{input}")
    ])

    # 构建链（使用 LCEL）
    chain = prompt | llm | StrOutputParser()

    # 使用 RunnableWithMessageHistory 自动管理历史（新 API）
    # 这是推荐的方式，替代 ConversationBufferMemory
    store = {}  # 存储不同会话的历史记录

    # get_session_history(session_id)：工具函数 —— 根据会话 ID，要么返回已有的历史，要么新建一个空的历史对象
    def get_session_history(session_id: str):
        """获取或创建会话历史"""
        if session_id not in store:
            # ChatMessageHistory是LangChain框架提供的专门用于存储聊天消息的核心类，你可以把它理解成：
            # 一个 “智能聊天记录本”，专门用来按顺序存放对话消息；
            # 内部自带一个messages列表，会自动区分消息类型（比如HumanMessage是用户消息、AIMessage是机器人消息）；
            # 还提供了add_user_message()、add_ai_message()等便捷方法（这里是RunnableWithMessageHistory自动调用这些方法，不用你手动写）。
            store[session_id] = ChatMessageHistory()
        return store[session_id]


    chain_with_history = RunnableWithMessageHistory(
        chain,                                  # RunnableWithMessageHistory：LangChain推荐的新API，用来包装原有链，实现 “自动管理会话历史”：
        get_session_history,                    # 历史记录获取函数,把chain（核心流程）和get_session_history（历史管理函数）绑定；
        input_messages_key="input",             # input_messages_key = "input"：指定用户输入的变量名（对应提示词里的{input}）；
        history_messages_key="history",         # history_messages_key = "history"：指定历史消息的变量名（对应提示词里的history占位符）
    )

    # 测试对话
    print("=" * 60)
    print("聊天机器人测试（带记忆功能 - 新 API）")
    print("=" * 60)

    session_id = "test-session"  # 会话 ID

    # 第一个问题
    question1 = "Is a pear a fruit or vegetable?"
    print(f"\n用户: {question1}")
    response1 = chain_with_history.invoke(
        {"input": question1},
        # config参数：指定会话ID（关联历史），并开启verbose = True（打印流程日志）
        config={"configurable": {"session_id": session_id}, "verbose": True}
    )
    print(f"机器人: {response1}")

    # 第二个问题（测试记忆功能）
    question2 = "What was one of the fruits I first asked you about?"
    print(f"\n用户: {question2}")
    response2 = chain_with_history.invoke(
        {"input": question2},
        config={"configurable": {"session_id": session_id}, "verbose": True}
    )
    print(f"机器人: {response2}")

    # 显示记忆内容
    print("\n" + "=" * 60)
    print("当前对话历史：")
    print("=" * 60)
    history = get_session_history(session_id)
    for message in history.messages:
        print(f"{message.__class__.__name__}: {message.content}")

    return chain_with_history, store


if __name__ == '__main__':
    chat_with_memory()

