from typing import TypedDict, List

from langgraph.graph import StateGraph, START, END

# 状态，其实急救室一个字典
class State(TypedDict):
    """用于在各节点之间传递的状态结构。"""

    nList: List[str]

# 节点a，接收一条消息并返回新的消息。
def node_a(state: State) -> State:
    """示例节点：接收一条消息并返回新的消息。"""
    print(f"node_a 接收到: {state['nList']}")
    note = "Hello, 我是节点 a"
    return State(nList=[note])

# 创建一个“图构造器”，告诉它“我传递的状态类型是 State”。
builder = StateGraph(State)
# 向图里加一个节点
builder.add_node("a", node_a)
builder.add_edge(START, "a")
builder.add_edge("a", END)
# 把上面定义好的节点和连线“编译”成一个可执行的图对象 graph
graph = builder.compile()



# initial_state：初始状态，里面放了一条字符串：
#   {"nList": ["Hello node a, how are you?"]}

# graph.invoke(initial_state)：
# 把 initial_state 送进图的起点 START，
# 然后流到节点 "a"，执行 node_a(initial_state)，
# 得到一个新的 State（{"nList": ["Hello, 我是节点 a"]}），
# 流到 END，流程结束。

# result：就是节点 a 返回的那个新的 State。
if __name__ == "__main__":
    initial_state: State = State(nList=["Hello node a, how are you?"])
    result = graph.invoke(initial_state)
    print(result)
