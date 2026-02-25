from typing import Literal
import uuid

from langgraph.types import Command

from agent_state import EmailAgentState, EmailClassification, llm


def read_email(state: EmailAgentState) -> EmailAgentState:
    """
    读取邮件内容的节点。

    实际生产中这一步要从邮箱提供的 API 中提取电子邮件，这里仅仅是演示，
    会将电子邮件直接传给 分类节点 ，因此简单地返回原始状态。
    """
    return state


def classify_intent(state: EmailAgentState) -> EmailAgentState:
    """
    分类节点，

    用大模型进行 意图分类 和 紧急程度 识别，然后把结构化结果写回状态。
    """
    structured_llm = llm.with_structured_output(EmailClassification)

    classification_pormpt = f"""
    分析用户输入的邮件并进行分类

    邮件: {state['email_content']}
    来自: {state['sender_email']}

    提供分类、紧急程度、主题和内容摘要
    """

    classication = structured_llm.invoke(classification_pormpt)

    # 覆盖了 EmailAgentState 中的 classification 键
    # LangGraph 规定，节点（Node）函数不需要返回一整个完整的状态字典。节点只需要返回**“发生了改变或需要新增的键值对”**
    return {
        "classification": classication,
    }


def search_documentation(state: EmailAgentState) -> EmailAgentState:
    """
    查询知识库节点，这里模拟操作。
    """
    classification = state.get("classification", {})

    query = f"{classification.get('intent', '')}  {classification.get('topic', '')}"
    # 目前 query 仅作示例，真实场景下可用于检索知识库

    try:
        # 模拟查询的逻辑
        search_results = [
            "search_result_1",
            "search_result_2",
            "search_result_3",
        ]
    except Exception:
        search_results = ["搜索接口不可用"]

    return {"search_results": search_results}


def bug_tracking(state: EmailAgentState) -> EmailAgentState:
    """
    模拟 bug 修复的相关内容，生成一个工单 ID。
    """
    ticket_id = f"Bug-{uuid.uuid4()} fixed"
    return {"ticket_id": ticket_id}



# 返回类型：这是一个特殊的 Command 对象。
# 作用：它能同时完成两件事：
# 数据更新：通过 update 参数，效果等同于第一种写法的 return {"key": value}。
# 动态路由：通过 goto 参数，直接告诉 LangGraph 下一步该运行哪个节点。
def write_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    """
    根据分类结果、搜索结果等中间结果生成邮件回复草稿，
    并根据紧急程度 / 复杂度决定是否需要人工审核。
    """
    classification = state.get("classification", {})

    context_sections: list[str] = []

    if state.get("search_results"):
        formatted_docs = "\n".join([f"- {doc}" for doc in state["search_results"]])
        context_sections.append(f"相关内容:\n{formatted_docs}")
    if state.get("customer_history"):
        context_sections.append(
            f"Customer tier: {state['customer_history'].get('tier', 'standard')}"
        )

    # 构建提示词
    draft_prompt = f"""
        撰写50字邮件回复:
        邮件内容: {state.get('email_content')}

        邮件分类: {classification.get('intent', 'unkown')}
        紧急程度: {classification.get('urgency', 'medium')}

        {chr(10).join(context_sections)}
    """

    response = llm.invoke(draft_prompt)

    # 根据紧急程度决定是否需要人类审核
    needs_review = (
        classification.get("urgency") in ["high", "critical"]
        or classification.get("intent") == "complex"
    )

    if needs_review:
        goto: Literal["human_review", "send_reply"] = "human_review"
        print("需要人工审核")
    else:
        goto = "send_reply"

    return Command(
        update={"draft_response": response.content},
        goto=goto,
    )


from langgraph.types import interrupt  # 必须导入


def human_review(state: EmailAgentState) -> EmailAgentState:
    # 这一行是关键！
    # 当程序执行到这里，它会弹出一个“中断”，并将括号里的内容作为 value 给到外部
    # 此时程序会立即停止执行，并将当前所有状态存入 checkpointer (memory)
    review_action = interrupt(
        {
            "question": "请审核邮件草稿，输入 'OK' 继续发送，输入其他内容修改草稿",
            "draft": state.get("draft_response")
        }
    )

    # 当你之后通过 Command(resume=...) 恢复时，review_action 就会拿到 resume 的值
    print(f"收到人工指令: {review_action}")

    if review_action != "OK":
        # 如果不是 OK，我们可以更新草稿（这里仅作演示）
        return {"draft_response": f"[已修改] {review_action}"}

    return state


def send_reply(state: EmailAgentState) -> EmailAgentState:
    """
    发送回复节点。

    真实场景中会调用邮件发送接口，这里仅作占位，直接返回状态。
    """
    return state
