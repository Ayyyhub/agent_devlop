import os
from typing import Literal, TypedDict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# 特点：
# 先决定“要做哪一类任务”，再把输入转给对应的专门节点。

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")

# 全局 LLM 实例，供各个节点复用
llm = ChatOpenAI(
    temperature=0.7,
    model_name="gpt-4o-mini",
    openai_api_key=openai_api_key,
    base_url=openai_base_url,
)

class State(TypedDict):
    input: str                      # 用户输入内容
    decision: Optional[str]         # 路由决策 (story, joke, poetry)
    output: Optional[str]           # 最终生成的文本内容

# 1. 定义节点
def generate_story(state: State):
    """
    写故事节点
    """
    print('--- 进入写故事处理逻辑 ---')
    result = llm.invoke(state['input'])
    return {
        'output': result.content
    }

def generate_joke(state: State):
    """
    写笑话节点
    """
    print('--- 进入写笑话处理逻辑 ---')
    result = llm.invoke(state['input'])
    return {
        'output': result.content
    }

def generate_poetry(state: State):
    """
    写诗歌节点
    """
    print('--- 进入写诗歌处理逻辑 ---')
    result = llm.invoke(state['input'])
    return {
        'output': result.content
    }


# 你定义了Classification，结果必须是一个字典，里面必须有个键叫 response_format，值必须是三选一
class Classification(TypedDict):
    response_format: Literal['story', 'joke', 'poetry']


def llm_call_router(state: State):
    """
    使用结构化输出将输入路由转到适当的节点
    """
    print('--- 正在进行路由决策 ---')

    # 将 Classification 传入 with_structured_output 函数的意义在于：给大模型戴上“紧箍咒”，强制它返回符合你要求的、格式标准的 Python 对象
    structed_llm = llm.with_structured_output(Classification)
    input_content = state['input']
    response = structed_llm.invoke([
        SystemMessage(content="你是一个分类路由，根据用户的输入进行分类，分类结果只能是 'story', 'joke', 'poetry' 中的一种。"),
        HumanMessage(content=input_content)
    ])

    # response 是实例（真实数据）： 它是大模型根据上面的“蓝图”真正吐出的数据，
    # 它是实实在在的内容，比如 {'response_format': 'poetry'}。
    return {
        'decision': response['response_format']
    }


# 定义条件边函数
def route_decision(state: State) -> Literal['llm_story', 'llm_joke', 'llm_poetry']:
    if state['decision'] == 'story':
        return 'llm_story'
    elif state['decision'] == 'joke':
        return 'llm_joke'
    else:  # 'poetry'
        return 'llm_poetry'

# 2. 定义边和图
router_builder = StateGraph(State)

router_builder.add_node('llm_story', generate_story)
router_builder.add_node('llm_joke', generate_joke)
router_builder.add_node('llm_poetry', generate_poetry)
router_builder.add_node('llm_call_router', llm_call_router)

router_builder.add_edge(START, 'llm_call_router')

router_builder.add_conditional_edges(
    'llm_call_router',
    route_decision,
    {
        'llm_story': 'llm_story',
        'llm_joke': 'llm_joke',
        'llm_poetry': 'llm_poetry'
    }
)

router_builder.add_edge('llm_story', END)
router_builder.add_edge('llm_joke', END)
router_builder.add_edge('llm_poetry', END)

# 编译工作流
workflow = router_builder.compile()

# 3. 测试运行
if __name__ == "__main__":
    # 可以尝试不同的输入来测试路由逻辑，例如：
    # "给我写一个关于大海的诗"
    # "讲个笑话"
    # "写一个勇者斗恶龙的故事"
    test_input = "给我讲个冷笑话"
    
    result = workflow.invoke({'input': test_input})

    print(f"\n【用户请求】: {test_input}")
    print(f"【分类结果】: {result.get('decision')}")
    print("-" * 30)
    print(f"【最终生成内容】:\n{result.get('output')}")
