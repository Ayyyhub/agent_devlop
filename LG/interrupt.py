import operator
from typing import TypedDict, List, Annotated, Literal

from langgraph.graph import START, END, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver


class State(TypedDict):
    """在各节点之间传递的状态结构。"""
    nList: Annotated[List[str], operator.add]


def node_a(state: State) -> Command[Literal["b", "c", END]]:
    """起始节点：根据用户输入决定走向 b / c / END，或触发人工中断。"""
    print("进入 A 节点")
    select = state["nList"][-1]

    if select == "b":
        next_node: Literal["b", "c", END] = "b"
    elif select == "c":
        next_node = "c"
    elif select == "q":
        next_node = END
    else:
        # 未预期的输入，通过 interrupt 让外层人工介入
        admin = interrupt(f"未期望的输出: {select}")
        print("用户重新输入是:", admin)
        if admin == "continue":
            next_node = "b"
            select = "b"
        else:
            next_node = END
            select = "q"

    return Command(
        update=State(nList=[select]),
        goto=next_node,
    )


def node_b(state: State) -> Command[Literal[END]]:
    """节点 b：这里可以扩展 b 分支的逻辑，当前只是直接结束。"""
    print(f"进入 B 节点，当前状态: {state['nList']}")
    return Command(goto=END)


def node_c(state: State) -> Command[Literal[END]]:
    """节点 c：这里可以扩展 c 分支的逻辑，当前只是直接结束。"""
    print(f"进入 C 节点，当前状态: {state['nList']}")
    return Command(goto=END)


# 构建图
builder = StateGraph(State)
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)
builder.add_edge(START, "a")

# 配置内存检查点器和线程
memory = InMemorySaver()
config = {"configurable": {"thread_id": "1"}}

# 编译时传入检查点器
graph = builder.compile(checkpointer=memory)


if __name__ == "__main__":
    while True:
        user = input("b, c or q to quit: ").strip()
        input_state: State = State(
            nList=[user]
        )
        # 每次调用 graph.invoke 时都传入相同的 config，这样 LangGraph 就会自动加载该线程 (thread_id=’1’) 的上一次状态，并在执行后保存新状态。
        result = graph.invoke(input_state, config)
        print("当前结果:", result)

        if "__interrupt__" in result:
            print(f"Interrupt: {result}")
            msg = result["__interrupt__"][-1].value
            print(msg)
            human = input(f"\n{msg}, 请重新输入: ")

            # 当图从中断点恢复时，整个图会重新执行。但由于检查点保存了中断前的状态（包括nList），并且interrupt()会返回新的resume值，因此节点能基于新信息做出不同的决策。
            # __interrupt__是一个列表，因为一个图可以在不同节点触发多个中断，LangGraph 会跟踪所有中断的上下文。
            human_response = Command(
                resume=human
            )
            # 每次调用 graph.invoke 时都传入相同的 config，这样 LangGraph 就会自动加载该线程 (thread_id=’1’) 的上一次状态，并在执行后保存新状态。
            result = graph.invoke(human_response, config)

        if result["nList"][-1] == "q":
            print("quit")
            break
