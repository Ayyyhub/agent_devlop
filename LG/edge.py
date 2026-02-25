from typing import TypedDict, List, Annotated
from langgraph.graph import START, END, StateGraph
from typing import TypedDict, List, Annotated

def deduplicate_merge(old_list: List[str], new_list: List[str]) -> List[str]:
    """自定义Reducer：合并列表并去重"""
    combined = old_list + new_list
    # dict.fromkeys(combined)：用字典的键来去重（字典键不重复）。
    return list(dict.fromkeys(combined)) # 保持顺序的去重

class MyState(TypedDict):
    # Annotated[类型, 额外信息] 里的第二个参数 deduplicate_merge 作为额外元数据，
    # 在 LangGraph 里可以解释为：“这个字段在多次更新时，用这个函数当 reducer 来合并”。
    unique_items: Annotated[List[str], deduplicate_merge]

class State(TypedDict):
    unique_items: Annotated[List[str], deduplicate_merge]

def node_a(state: State) -> State:
    print(f"Adding 'A' to {state['unique_items']}")
    return State(unique_items=["A"])

def node_A_extra(state: State) -> State:
    print(f"Adding 'A' to {state['unique_items']}")
    return State(unique_items=["A"])

builder = StateGraph(State)

builder.add_node("a", node_a)
builder.add_node("a_extra", node_A_extra)

builder.add_edge(START, "a")
builder.add_edge("a", "a_extra")
builder.add_edge("a_extra", END)

graph = builder.compile()

initial_state = State(
    unique_items = ['Initial String']
)

# 调用 graph.invoke(initial_state)：
# 把 initial_state 作为起始状态送进图；
# 按顺序执行：
# 节点 "a"：打印当前列表，然后返回 {"unique_items": ["A"]}；
# 节点 "a_extra"：再打印当前列表，然后再次返回 {"unique_items": ["A"]}；
# 因为 unique_items 使用了 Annotated[..., deduplicate_merge]，LangGraph 会用 deduplicate_merge 来合并旧值和新值：
# 第一次合并：['Initial String'] + ['A'] → 去重 → ['Initial String', 'A']
# 第二次合并：['Initial String', 'A'] + ['A'] → 去重 → ['Initial String', 'A']（不会重复多一个 'A'）
print(graph.invoke(initial_state))
