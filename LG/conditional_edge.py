from typing import TypedDict, List, Annotated, Literal
import operator

from langgraph.graph import START, END, StateGraph


class State(TypedDict):
    """在各节点之间传递的状态。"""
    nList: Annotated[List[str], operator.add]


def node_a(state: State) -> State:
    """起始节点：条件分支入口。"""
    print(f"node_a 收到: {state['nList']}")
    return state


def node_b(state: State) -> State:
    """分支 b：返回包含 'B' 的状态。"""
    print(f"node_b 收到: {state['nList']}")
    return State(nList=["B"])


def node_c(state: State) -> State:
    """分支 c：返回包含 'C' 的状态。"""
    print(f"node_c 收到: {state['nList']}")
    return State(nList=["C"])


def node_bb(state: State) -> State:
    """b 的后续节点：返回 'bb'。"""
    print(f"node_bb 收到: {state['nList']}")
    return State(nList=["bb"])


def node_cc(state: State) -> State:
    """c 的后续节点：返回 'cc'。"""
    print(f"node_cc 收到: {state['nList']}")
    return State(nList=["cc"])


def conditional_edge(state: State) -> Literal["b", "c", END]:
    """
    根据当前状态里的最后一个字符串，决定从 a 走向 b / c / END。
    """
    select = state["nList"][-1]
    if select == "b":
        return "b"
    elif select == "c":
        return "c"
    elif select == "q":
        return END
    else:
        return END


# 构建状态图
builder = StateGraph(State)

builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)
builder.add_node("bb", node_bb)
builder.add_node("cc", node_cc)

# START -> a -> (条件分支到 b / c / END)
# b -> bb -> END
# c -> cc -> END
builder.add_edge(START, "a")
builder.add_conditional_edges("a", conditional_edge)
builder.add_edge("b", "bb")
builder.add_edge("c", "cc")
builder.add_edge("bb", END)
builder.add_edge("cc", END)

# 把上面定义好的节点和连线“编译”成一个可执行的图对象 graph
graph = builder.compile()


if __name__ == "__main__":
    user = input("请输入 b, c 或 q (q 退出): ").strip()
    input_state: State = State(
        nList=[user]
    )
    result = graph.invoke(input_state)
    print("最终结果:", result)