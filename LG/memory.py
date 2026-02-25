import operator
from typing import TypedDict, List, Annotated, Literal

from langgraph.graph import START, END, StateGraph
from langgraph.types import Command
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    """在各节点之间传递的状态。"""
    # 使用 Annotated + operator.add，使多次更新时 nList 自动拼接
    nList: Annotated[List[str], operator.add]

# Command[Literal["b", "c", END]] 是“以这个Literal类型作为泛型参数的 Command对象”：表示“这个 Command 的 goto 目标，只允许是 'b'、'c' 或 END”
def node_a(state: State) -> Command[Literal["b", "c", END]]:
    """起始节点：根据用户输入决定跳转到 b / c / END，并把选择写入状态。"""
    select = state["nList"][-1]

    if select == "b":
        # Literal["b", "c", END] 是一个“类型”：表示“值必须是 'b'、'c' 或 END 这几种之一”
        next_node: Literal["b", "c", END] = "b"     # 有类型标注
    elif select == "c":                             
        next_node = "c"                             # 无类型标注
    elif select == "q":
        next_node = END
    else:
        next_node = END

    print(f"node_a 收到: {state['nList']}，跳转到: {next_node}")

    return Command(
        update=State(nList=[select]),
        goto=next_node,
    )


def node_b(state: State) -> Command[Literal[END]]:
    """节点 b：这里可以处理与 b 相关的逻辑，当前只是直接结束。"""
    print(f"node_b 收到: {state['nList']}，即将结束")
    return Command(goto=END)


def node_c(state: State) -> Command[Literal[END]]:
    """节点 c：这里可以处理与 c 相关的逻辑，当前只是直接结束。"""
    print(f"node_c 收到: {state['nList']}，即将结束")
    return Command(goto=END)


# 构建带记忆的状态图
builder = StateGraph(State)
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)

builder.add_edge(START, "a")

#  从 langgraph.checkpoint.memory 导入 InMemorySaver，并实例化。
#  config 中的 thread_id 是关键，它标识了会话线程, 相同 thread_id 下的所有调用将共享状态历史。
memory = InMemorySaver()
# 注意：configurable 这里应该是一个 dict，而不是 set
config = {
    "configurable": {
        "thread_id": "1",
    }
}

# 在编译图时，通过 checkpointer 参数传入检查点器实例。
graph = builder.compile(checkpointer=memory)

if __name__ == "__main__":
    while True:
        user = input("请输入 b, c 或 q (q 退出): ").strip()
        input_state: State = State(
            nList=[user]
        )
        result = graph.invoke(input_state, config)

        if result["nList"][-1] == "q":
            print("quit")
            break
