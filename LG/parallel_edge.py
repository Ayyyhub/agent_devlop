import operator
from typing import TypedDict, List, Annotated

from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    """在各个节点之间传递的状态结构。"""
    # 使用 Annotated 指定 reducer：多个节点返回的列表会通过 operator.add 做拼接
    nList: Annotated[List[str], operator.add]


def node_a(state: State) -> State:
    """节点 A：在列表中加入 'A'。"""
    print(f"node_a 收到: {state['nList']}")
    return State(nList=["A"])


def node_b(state: State) -> State:
    """节点 B：在列表中加入 'B'。"""
    print(f"node_b 收到: {state['nList']}")
    return State(nList=["B"])


def node_c(state: State) -> State:
    """节点 C：在列表中加入 'C'。"""
    print(f"node_c 收到: {state['nList']}")
    return State(nList=["C"])


def node_bb(state: State) -> State:
    """节点 BB：在列表中加入 'BB'。"""
    print(f"node_bb 收到: {state['nList']}")
    return State(nList=["BB"])


def node_cc(state: State) -> State:
    """节点 CC：在列表中加入 'CC'。"""
    print(f"node_cc 收到: {state['nList']}")
    return State(nList=["CC"])


def node_d(state: State) -> State:
    """节点 D：在列表中加入 'D'。"""
    print(f"node_d 收到: {state['nList']}")
    return State(nList=["D"])


# 构建状态图
builder = StateGraph(State)

builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)
builder.add_node("bb", node_bb)
builder.add_node("cc", node_cc)
builder.add_node("d", node_d)

# 图结构：
# START ->  a -> b  -> bb ->  d -> END
#            \-> c ->  cc -/
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "bb")
builder.add_edge("c", "cc")
builder.add_edge("bb", "d")
builder.add_edge("cc", "d")
builder.add_edge("d", END)
# 把上面定义好的节点和连线“编译”成一个可执行的图对象 graph
graph = builder.compile()


if __name__ == "__main__":
    initial_state: State = State(
        nList=["Initial String"]
    )
    result = graph.invoke(initial_state)
    print("最终结果:", result)