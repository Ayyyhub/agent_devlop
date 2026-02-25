from langgraph.types import Command

from agent_figure import app

if __name__ == '__main__':
    initial_state = {
        "email_content": "我遇到了一个紧急bug, 有客户重复订阅了一个产品",
        "sender_email": "test@163.com",
        "email_id": "email_123",
    }
    config = {"configurable": {"thread_id": "customer_123"}}

    # 在compile(checkpointer=memory)中配置memory是为了赋予这个图（app）存储和读取记忆的能力
    # 在invoke或stream时，配置thread_id是为了告诉图具体要去读取哪一段记忆
    result = app.invoke(initial_state, config=config)

    # result["__interrupt__"]：是一个列表，因为可能有多个中断。
    # result["__interrupt__"][-1].value：这就是你在 interrupt(...) 括号里填写的那个字典或字符串。
    print(f"准备审核的回复内容:{result['draft_response']}...\n")
    if "__interrupt__" in result:
        print(f"Interrupt:{result}")
        msg = result["__interrupt__"][-1].value
        print(msg)
        human = input("请输入: ")
        human_response = Command(
            resume=human
        )
        final_result = app.invoke(human_response, config)
