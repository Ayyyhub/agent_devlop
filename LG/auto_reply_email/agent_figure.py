from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from agent_state import EmailAgentState
from agent_node import (
    read_email,
    classify_intent,
    search_documentation,
    bug_tracking,
    write_response,
    human_review,
    send_reply,
)

# “显式注册”构建状态图
# 契约初始化：当你执行 builder = StateGraph(EmailAgentState) 时，LangGraph 会在内部通过 Python 的“内省反射”机制（Introspection），
# 把 EmailAgentState 这个类的结构读一遍。它知道这个 State 有哪些键，哪些键需要特殊合并（Reducer），哪些键默认直接覆盖。
builder = StateGraph(EmailAgentState)

builder.add_node("read_email", read_email)
builder.add_node("classify_intent", classify_intent)
builder.add_node("search_documentation", search_documentation)
builder.add_node("bug_tracking", bug_tracking)
builder.add_node("write_response", write_response)
builder.add_node("human_review", human_review)
builder.add_node("send_reply", send_reply)

builder.add_edge(START, "read_email")
builder.add_edge("read_email", "classify_intent")
builder.add_edge("classify_intent", "search_documentation")
builder.add_edge("classify_intent", "bug_tracking")
builder.add_edge("search_documentation", "write_response")
builder.add_edge("bug_tracking", "write_response")
builder.add_edge("send_reply", END)

memory = InMemorySaver()
# 把上面定义好的节点和连线“编译”成一个可执行的图对象
app = builder.compile(checkpointer=memory)
