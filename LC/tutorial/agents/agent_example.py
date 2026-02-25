"""
LangChain Agent 示例 - 使用工具进行搜索和网页请求

功能说明：
1. 使用 Google Search 工具搜索信息（可选，需要配置 API 密钥）
2. 使用 Requests 工具获取网页内容（必需）
3. Agent 自动决定何时使用哪个工具

配置说明：
- Requests 工具：无需额外配置，可直接使用
- Google Search 工具：需要在 .env 文件中配置：
  GOOGLE_API_KEY=your_api_key
  GOOGLE_CSE_ID=your_cse_id
  
  安装依赖：
  pip install langchain-google-community

注意：使用 LangChain 0.3.x 的新 API
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


def create_agent():
    """创建并配置 Agent"""
    # 加载环境变量
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL")

    # 1. 初始化 llm，只支持OpenAI
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
                        # - func=search.run：执行搜索的核心函数
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
        Thought: {agent_scratchpad}""")   # 占位符：替换为 Agent 的历史思考 / 行动记录（实现 “思维记忆”，让 Agent 知道自己之前做了什么）

    try:
        # 4. 创建 Agent（使用新 API）
        agent = create_react_agent(llm, tools, prompt)

        # 5. 包装成 agent_executor（执行器）
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,                           #   开启verbose = True（打印流程日志）
            return_intermediate_steps=True,         # - return_intermediate_steps=True：返回中间步骤（比如思考、行动记录，方便调试）；
            handle_parsing_errors=True              # - handle_parsing_errors=True：自动处理 Agent 输出格式错误（比如 Agent 没按规定格式输出时，尝试修复）
        )
        return agent_executor
    except Exception as e:
        print(f"Agent 创建失败：{e}")
        return None


def run_queries():
    """执行示例查询"""
    agent_executor = create_agent()

    if not agent_executor:
        print("无法创建 Agent，请检查配置")
        return

    # 查询1：搜索问题
    print("=" * 60)
    print("查询 1：搜索问题")
    print("=" * 60)
    query1 = "What is the capital of canada?"
    print(f"\n问题：{query1}\n")

    try:
        response1 = agent_executor.invoke({"input": query1})
        print("\n" + "=" * 60)
        print("回答：")
        print("=" * 60)
        print(response1.get('output', 'No output'))

        # 显示中间步骤（如果启用）
        if 'intermediate_steps' in response1:
            print("\n中间步骤：")
            for i, step in enumerate(response1['intermediate_steps'], 1):
                print(f"步骤 {i}: {step}")
    except Exception as e:
        print(f"查询失败：{e}")

    # 查询2：网页请求
    print("\n\n" + "=" * 60)
    print("查询 2：网页内容")
    print("=" * 60)
    # 看不到内容，如果你想要真的“看到知乎文章内容 / 评论”，需要能执行 JS 的工具（Playwright、Selenium、headless browser 等），而不是简单的 HTTP 请求
    query2 = "Tell me what the content are about on this webpage https://zhuanlan.zhihu.com/p/654052645"
    print(f"\n问题：{query2}\n")

    try:
        response2 = agent_executor.invoke({"input": query2})
        print("\n" + "=" * 60)
        print("回答：")
        print("=" * 60)
        print(response2.get('output', 'No output'))
    except Exception as e:
        print(f"查询失败：{e}")


if __name__ == '__main__':
    # 方式1：执行预设查询
    run_queries()

