"""
    交互式 Agent
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_community.utilities import RequestsWrapper

# 尝试导入 Google Search（新版本）
try:
    from langchain_google_community import GoogleSearchAPIWrapper

    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    try:
        # 回退到旧版本（如果新包不可用）
        from langchain_community.utilities import GoogleSearchAPIWrapper

        GOOGLE_SEARCH_AVAILABLE = True
    except ImportError:
        GOOGLE_SEARCH_AVAILABLE = False
        print("提示：Google Search 工具不可用。安装 langchain-google-community 以启用搜索功能：")
        print("  pip install langchain-google-community")


def create_interactive_agent():
    """创建并配置 Agent"""
    # 加载环境变量
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 1. 初始化 llm
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo',
        openai_api_key=openai_api_key,
        openai_api_base=openai_base_url
    )

    # 2. 初始化 tools（Requests + 可选 Search）
    tools = []
    # 初始化 Requests 工具（必需）
    try:
        requests_wrapper = RequestsWrapper()
        tools.append(
            Tool(
                # - name="Requests"：工具名称（Agent 决策时会参考这个名称）；
                name="Requests",
                # - func=requests_wrapper.get：工具的核心执行函数（调用该工具时，实际执行get方法，即获取网页内容）；
                func=requests_wrapper.get,
                # - description=...：工具的描述（关键！Agent 会根据这个描述判断 “什么时候该用这个工具”，比如 “需要从 URL 获取网页内容时用”）
                description="Useful for when you need to fetch content from a URL or webpage. Input should be a valid URL."
            )
        )
    except Exception as e:
        print(f"错误：Requests 工具初始化失败：{e}")
        return None

    # 初始化 Google Search 工具（可选）
    if GOOGLE_SEARCH_AVAILABLE:
        try:
            # 检查是否有 Google API 密钥
            google_api_key = os.getenv("GOOGLE_API_KEY")
            google_cse_id = os.getenv("GOOGLE_CSE_ID")

            if not google_api_key or not google_cse_id:
                print("提示：Google Search 工具需要配置以下环境变量：")
                print("  GOOGLE_API_KEY=your_api_key")
                print("  GOOGLE_CSE_ID=your_cse_id")
                print("  当前将只使用 Requests 工具\n")
            else:
                search = GoogleSearchAPIWrapper(
                    google_api_key=google_api_key,
                    google_cse_id=google_cse_id
                )
                tools.append(
                    Tool(
                        name="Search",
                        func=search.run,
                        description="Useful for when you need to search Google to answer questions about current events, facts, or information that requires up-to-date data."
                    )
                )
                print("✓ Google Search 工具已启用\n")
        except Exception as e:
            print(f"警告：Google Search 工具初始化失败：{e}")
            print("  将继续使用其他可用工具\n")

    if not tools:
        print("错误：没有可用的工具")
        return None

    print(f"已加载 {len(tools)} 个工具：{', '.join([tool.name for tool in tools])}\n")

    # 3. 创建 ReAct风格的 prompt 模板
    prompt = PromptTemplate.from_template("""You are a helpful assistant that can use tools to answer questions.

        You have access to the following tools:
        {tools}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Begin!

        Question: {input}
        Thought: {agent_scratchpad}""")  # 占位符：替换为 Agent 的历史思考 / 行动记录（实现 “思维记忆”，让 Agent 知道自己之前做了什么）

    try:
        # 4. 创建 Agent（使用新 API）
        agent = create_react_agent(llm, tools, prompt)

        # 5. 包装成 agent_executor（执行器）
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,  # 开启verbose = True（打印流程日志）
            return_intermediate_steps=True,  # - return_intermediate_steps=True：返回中间步骤（比如思考、行动记录，方便调试）；
            handle_parsing_errors=True  # - handle_parsing_errors=True：自动处理 Agent 输出格式错误（比如 Agent 没按规定格式输出时，尝试修复）
        )
        return agent_executor
    except Exception as e:
        print(f"Agent 创建失败：{e}")
        return None


def interactive_agent():
    """交互式 Agent 模式"""
    agent_executor = create_interactive_agent()

    if not agent_executor:
        print("无法创建 Agent，请检查配置")
        return

    print("\n" + "=" * 60)
    print("交互式 Agent（输入 'exit' 退出）")
    print("=" * 60)

    while True:
        user_input = input("\n请输入问题：").strip()

        if user_input.lower() in ['exit', 'quit', '退出']:
            print("再见！")
            break

        if not user_input:
            continue

        try:
            response = agent_executor.invoke({"input": user_input})
            print(f"\n回答：{response.get('output', 'No output')}")
        except Exception as e:
            print(f"查询失败：{e}")


if __name__ == '__main__':
    # 方式2：交互式模式（取消注释以启用）
    interactive_agent()
