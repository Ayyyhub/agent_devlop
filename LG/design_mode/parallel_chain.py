import os
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END


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
    topic: str                      # 处理的主题
    joke: Optional[str]             # 生成的笑话
    story: Optional[str]            # 生成的故事
    poetry: Optional[str]           # 生成的诗歌
    combined_output: Optional[str]  # 最终聚合成的内容

# --- 定义节点函数 ---

def generate_joke(state: State):
    """
    生成笑话的节点
    """
    print("--- 正在并行生成笑话 ---")
    topic = state['topic']
    msg = llm.invoke(f'写一个关于{topic}的简短笑话')
    return {'joke': msg.content}

def generate_story(state: State):
    """
    生成故事的节点
    """
    print("--- 正在并行生成故事 ---")
    topic = state['topic']
    msg = llm.invoke(f'写一个关于{topic}的简短故事（100字以内）')
    return {'story': msg.content}

def generate_poetry(state: State):
    """
    生成诗歌的节点
    """
    print("--- 正在并行生成诗歌 ---")
    topic = state['topic']
    msg = llm.invoke(f'写一个关于{topic}的现代诗句')
    return {'poetry': msg.content}

def aggregator(state: State):
    """
    聚合节点：等待并行任务全部完成后，将结果合并
    """
    print("--- 正在执行聚合逻辑 ---")
    topic = state.get('topic', '未知主题')
    joke = state.get('joke', '（笑话生成失败）')
    story = state.get('story', '（故事生成失败）')
    poetry = state.get('poetry', '（诗歌生成失败）')
    
    combined = (
        f"【全能创作报告：关于 {topic}】\n"
        "================================\n\n"
        "📜 [短故事]\n"
        f"{story}\n\n"
        "😆 [冷笑话]\n"
        f"{joke}\n\n"
        "✍️ [现代诗]\n"
        f"{poetry}\n\n"
        "================================"
    )
    return {'combined_output': combined}

# --- 构建图 ---
parallel_builder = StateGraph(State)

# 添加节点
parallel_builder.add_node('generate_joke', generate_joke)
parallel_builder.add_node('generate_story', generate_story)
parallel_builder.add_node('generate_poetry', generate_poetry)
parallel_builder.add_node('aggregator', aggregator)

# 定义并行路径 (Fan-out)
# 从 START 同时流向三个并行节点
parallel_builder.add_edge(START, 'generate_joke')
parallel_builder.add_edge(START, 'generate_story')
parallel_builder.add_edge(START, 'generate_poetry')

# 定义聚合路径 (Fan-in)
# 三个节点全部完成后流向 aggregator
parallel_builder.add_edge('generate_joke', 'aggregator')
parallel_builder.add_edge('generate_story', 'aggregator')
parallel_builder.add_edge('generate_poetry', 'aggregator')

# aggregator 完成后结束
parallel_builder.add_edge('aggregator', END)

# 编译工作流
workflow = parallel_builder.compile()

# --- 测试运行 ---
if __name__ == "__main__":
    test_input = "程序员的格子衫"
    print(f"开始创作关于 '{test_input}' 的合集...\n")
    
    result = workflow.invoke({'topic': test_input})
    
    print("\n" + result['combined_output'])
