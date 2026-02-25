import os
from typing import Literal, TypedDict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

# 特点：
# 始终围绕同一件事：只做一类任务——“写一个笑话”，只是分成几步加工。

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")

# 全局 LLM 实例，供各个节点复用
llm = ChatOpenAI(
    temperature=0.7,  # 稍微增加随机性让笑话更有趣
    model_name="gpt-4o-mini",
    openai_api_key=openai_api_key,
    base_url=openai_base_url,
)

# 1. 定义图状态
class State(TypedDict):
    topic: str                      # 主题
    joke: Optional[str]             # 笑话
    improved_joke: Optional[str]    # 优化后的笑话
    final_joke: Optional[str]       # 最终版笑话

# 2. 定义节点函数
def generate_joke(state: State):
    """
    第一个大模型调用，根据主题生成初始笑话
    """
    topic = state['topic']
    prompt = f"写一个关于{topic}的简短笑话"
    msg = llm.invoke(prompt)
    return {
        "joke": msg.content
    }

def check_punchline(state: State) -> Literal["Fail", "Pass"]:
    """
    模拟门控函数——笑话中是否包含问号或感叹号
    """
    joke = state.get("joke", "")
    # 同时检查中英文标点
    if any(mark in joke for mark in ["?", "？", "!", "！"]):
        return "Fail"  # 未能通过门控检查, 需要继续增强
    return "Pass"

def improve_joke(state: State):
    """
    第二个大模型调用，通过添加文字游戏改进笑话
    """
    joke = state["joke"]
    prompt = f"通过添加文字游戏使笑话更有趣，当前笑话是: {joke}"
    msg = llm.invoke(prompt)
    return {
        "improved_joke": msg.content
    }

def polish_joke(state: State):
    """
    第三个大模型调用，最终润色笑话，添加令人惊讶的转折
    """
    improved_joke = state["improved_joke"]
    prompt = f"为这个笑话添加一个令人惊讶的转折: {improved_joke}"
    msg = llm.invoke(prompt)
    return {
        "final_joke": msg.content
    }

# 3. 定义边和图
workflow = StateGraph(State)

workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

workflow.add_edge(START, "generate_joke")

# 根据 check_punchline 的结果决定流向，如果不包含特殊符号直接 END
workflow.add_conditional_edges(
    "generate_joke", 
    check_punchline, 
    {
        "Fail": "improve_joke",
        "Pass": END
    }
)

workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# 编译图
chain = workflow.compile()

# 4. 测试运行
if __name__ == "__main__":
    initial_input = {"topic": "小猫"}
    result = chain.invoke(initial_input)

    print("\n--- 笑话生成流水线结果 ---")
    print(f"【主题】: {result['topic']}")
    print(f"【初始笑话】:\n{result.get('joke')}")

    if result.get("improved_joke"):
        print(f"\n【改进后的笑话】:\n{result.get('improved_joke')}")
        
    if result.get("final_joke"):
        print(f"\n【最终润色的笑话】:\n{result.get('final_joke')}")
    else:
        print("\n(注: 初始笑话已足够优秀，未进入改进环节)")

