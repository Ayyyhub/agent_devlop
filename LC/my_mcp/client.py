import asyncio
import json
import os
import sys
from typing import List, Dict
from contextlib import AsyncExitStack
from openai import OpenAI
from dotenv import load_dotenv

# 保证从项目根（LC）能找到 my_mcp 包：用 python my_mcp/client.py 时把上级目录加入 path
_LC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _LC_ROOT not in sys.path:
    sys.path.insert(0, _LC_ROOT)

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from LC.my_mcp.skills.loader import get_system_prompt


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")
gaode_demo_key = os.getenv("gaode_demo_key")


def _extract_message_content(msg) -> str:
    """从 API 返回的 message 中提取文本，兼容 content 为 None 或列表的情况"""
    if msg is None:
        return "（模型未返回内容）"
    content = getattr(msg, "content", None)
    if content is None:
        return "（模型未返回内容）"
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        for block in content:
            if hasattr(block, "text") and block.text:
                return block.text
            if isinstance(block, dict) and block.get("text"):
                return block["text"]
    return str(content) if content else "（模型未返回内容）"


class MCPClient:

    def __init__(self):
        """为什么需要 AsyncExitStack ？
            在 MCP client 中，每个服务器连接需要管理：
                1、子进程（python sever.py）
                2、stdio 管道（stdin/stdout）
                3、会话对象（ClientSession）
            如果手动管理，需要：
                1、启动时：创建进程、建立管道、创建会话
                2、退出时：关闭会话、关闭管道、终止进程
            使用 AsyncExitStack 后：
                1、启动时：用 enter_async_context() 注册资源
                2、退出时：调用 aclose()，自动按顺序清理所有资源
            """
        # AsyncExitStack：上下文管理器（Context Manager）：实现 __enter__/__exit__（同步）或 __aenter__/__aexit__（异步）的对象，用于自动获取和释放资源
        # 数据结构：一个“栈”，可以动态地添加多个异步上下文管理器，退出时按后进先出（LIFO）顺序自动清理所有资源

        self.exit_stack = AsyncExitStack()    # 在创建 MCPClient 实例时，创建一个 AsyncExitStack 对象，用来管理这个客户端的所有异步资源
        self.opanai_api_key = openai_api_key  # 调用模型的api_key
        self.base_url = openai_base_url  # 调用模型url, 这里以deepseek作演示
        self.model = "gpt-4o-mini"
        self.client = OpenAI(api_key=self.opanai_api_key, base_url=self.base_url)
        self.mcp_client_sessions_list: List[ClientSession] = []  # 存储多个服务器会话
        self.tool_to_session: Dict[str, ClientSession] = {}  # 工具名 -> 会话的映射
        self._server_stacks: List[AsyncExitStack] = []    # 在 MCPClient 初始化时，声明并创建一个空列表，用来存「每个 MCP 服务器对应的 AsyncExitStack」

    async def connect_to_servers(self, server_configs: List[Dict]):
        """连接多个 MCP 服务器
        Args:
            server_configs: 服务器配置列表，每个配置包含：
                - "name": 服务器名称（用于显示）
                - "command": 启动命令（如 "python" 或 "uvx"）
                - "args": 命令参数列表
        """
        for config in server_configs:
            if config.get("disabled"):
                continue
            server_name = config.get("name", "Unknown")
            server_params = StdioServerParameters(
                command=config["command"],
                args=config["args"],
                env=config.get("env")  # 从配置里读 env，没有则为 None
            )

            # 每个服务器用独立栈，某个连接失败时只关该进程，不拖垮整个客户端
            stack = AsyncExitStack()

            # AsyncExitStack 作用：
            # 0、stdio_transport：返回一个元组 (stdio, write)，用于后续通信
            # 1、self.exit_stack.enter_async_context: a、调用 stdio_client 的 __aenter__()，实际执行：
            #                                           - 启动子进程（如 python my_mcp/sever.py）
            #                                           - 创建 stdin/stdout 管道
            #                                           - 启动后台任务读取服务器输出
            #                                           - 返回 (read_stream, write_stream) 元组
            #                                         b、将 __aexit__() 注册到栈，用于退出时清理
            # 2、stdio_client(server_params)：创建一个异步 stdio 客户端上下文管理器, 根据 server_params 启动服务器子进程
            try:
                """AsyncExitStack.enter_async_context() 的作用：
                        1、调用上下文管理器的 __aenter__()（启动进程、建立连接）
                        2、把 __aexit__() 注册到栈里
                        3、返回 __aenter__() 的结果
                    最后调用 await self.exit_stack.aclose() 时：
                        1、按后进先出顺序调用所有已注册的 __aexit__()
                        2、自动清理所有资源
                """
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                stdio, write = stdio_transport
                # ClientSession：创建 MCP 协议层的客户端会话对象，后续的交互（比如调用工具）都靠这个 session
                mcp_client_session = await self.exit_stack.enter_async_context(   # 调用 ClientSession 的 __aenter__()（通常做基础设置），将 __aexit__() 注册到栈，用于退出时关闭会话
                    ClientSession(stdio, write)
                )
                await mcp_client_session.initialize()  # 正式初始化和服务器的连接，相当于 "握手"
            except Exception as e:
                await stack.aclose()
                print(f"\n⚠ 连接服务器 '{server_name}' 失败（已跳过）: {e}")
                continue
            
            # 获取该服务器的工具列表
            response = await mcp_client_session.list_tools()
            tools = response.tools
            
            # 建立工具名到会话的映射（用于后续路由工具调用）
            for tool in tools:
                if tool.name in self.tool_to_session:
                    print(f"警告：工具 '{tool.name}' 在多个服务器中存在，将使用第一个")
                else:
                    self.tool_to_session[tool.name] = mcp_client_session
            
            self.mcp_client_sessions_list.append(mcp_client_session)
            print(f"\n✓ 已连接到服务器 '{server_name}'，支持工具: {[tool.name for tool in tools]}")

    async def process_query(self, query: str) -> str:
        """用大模型处理一次 query + 工具调用"""
        # 方案一：从 skills 加载 System Prompt，引导模型在合适时使用 Time/Map 等工具
        tool_names = list(self.tool_to_session.keys())
        system_prompt = get_system_prompt(tool_names)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        # 合并所有服务器的工具
        all_tools = []
        for session in self.mcp_client_sessions_list:
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                all_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                })

        # model_response(ChatCompletion
        # 对象)
        # ├── choices: List[Choice]  # 候选回答列表
        # │   └── [0](第一个
        # Choice
        # 对象) ← content
        # 指向这里
        # │       ├── finish_reason: str
        # │       ├── index: int
        # │       ├── message: ChatCompletionMessage
        # │       │   ├── content: str | None
        # │       │   ├── tool_calls: List[ToolCall] | None  # 如果调用了工具，这里有工具调用信息
        # │       │   └── role: str
        # │       └── logprobs: Optional[...]
        # └── usage: CompletionUsage

        # 一、调用大模型，传入问题和可用工具
        # 0、self.client.chat.completions.create：这里是“自己写 Agent 框架”，所以必须用底层客户端
        # 1. 换成 ChatOpenAI，返回的是 LangChain 的消息对象，不是 response.choices[0] 那种结构
        # 2. 换成 create_react_agent，create_react_agent 本身 就是一个 Agent，内部已经帮你：《调工具》 《处理多轮循环》 《管理状态》, 你不用再在外面写 chat.completions.create(...) 和 finish_reason == "tool_calls" 这些底层逻辑
        model_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=all_tools
        )

        # # 处理返回内容
        content = model_response.choices[0]

        # 判断这一次模型输出，是“直接给最终答案”，还是“想要调用工具”
        if content.finish_reason == "tool_calls":
            # 先追加 assistant 消息（只追加一次）
            messages.append(content.message.model_dump())

            # 模型可能一次返回多个 tool_calls，必须逐个执行并为每个 tool_call_id 回一条 tool 消息
            tool_calls = content.message.tool_calls or []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    tool_args = {}

                # 自动补充缺失的必需参数
                if tool_name == "get_current_time" and "timezone" not in tool_args:
                    tool_args["timezone"] = "Asia/Shanghai"
                    print(f"[INFO] 自动补充 timezone 参数: {tool_args['timezone']}")
                elif tool_name == "convert_time":
                    if "timezone" not in tool_args:
                        tool_args["timezone"] = "Asia/Shanghai"

                # 根据工具名找到对应的会话
                if tool_name not in self.tool_to_session:
                    tool_content = f"错误：找不到工具 '{tool_name}'。可用工具: {list(self.tool_to_session.keys())}"
                    print(f"[ERROR] {tool_content}")
                else:
                    session = self.tool_to_session[tool_name]
                    # 调用对应服务器上的工具
                    try:
                        result = await session.call_tool(tool_name, tool_args)
                        print(f"\n[调用工具 {tool_name}，参数: {tool_args}]\n")
                        # 提取工具返回的文本内容（兼容多种格式）
                        tool_content = ""
                        if hasattr(result, 'content') and result.content:
                            if isinstance(result.content, list) and len(result.content) > 0:
                                if hasattr(result.content[0], 'text'):
                                    tool_content = result.content[0].text
                                elif isinstance(result.content[0], str):
                                    tool_content = result.content[0]
                                else:
                                    tool_content = str(result.content[0])
                            else:
                                tool_content = str(result.content)
                        else:
                            tool_content = str(result)
                        if getattr(result, 'isError', False):
                            print(f"[警告] 工具返回错误: {tool_content}\n")
                    except Exception as e:
                        tool_content = f"调用工具 {tool_name} 时出错: {str(e)}"
                        print(f"[ERROR] {tool_content}")

                # 每个 tool_call 必须对应一条 role=tool 的消息，且 tool_call_id 一致
                messages.append({
                    "role": "tool",
                    "content": tool_content,
                    "tool_call_id": tool_call.id,
                })

            # 二、再次调用大模型，将上面的结果返回给大模型用于生产最终结果
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return _extract_message_content(response.choices[0].message)

        # 模型未调用工具，直接返回文字回复
        return _extract_message_content(content.message)

    async def chat_loop(self):
        """运行交互式聊天"""
        print("\n MCP客户端已启动！输入quit退出")
        print(f"当前可用工具: {list(self.tool_to_session.keys())}")

        # 无限循环，直到输入quit
        while True:
            try:
                query = input("\n用户:").strip()      # 获取用户输入
                if query.lower() == 'quit':     # 输入quit则退出
                    break
                response = await self.process_query(query)      # 处理用户查询
                print(f"\n{self.model}: {response}")        # 打印回答
            except Exception as e:          # 捕获错误，避免程序崩溃
                print(f"发生错误: {str(e)}")


    async def clean(self):
        for s in self._server_stacks:
            await s.aclose()
        self._server_stacks.clear()      # 清空列表，避免重复关闭或持有已无效的引用
        await self.exit_stack.aclose()   # 最后关闭客户端自己的 exit_stack

async def main():
    # 配置多个 MCP 服务器

    server_configs = [
        {
            "name": "Demo Server (add工具)",
            "command": "python",
            "args": ["my_mcp/sever.py"]
        },
        {
            "name": "Time MCP Server",
            "command": "python",
            "args": ["-m", "mcp_server_time", "--local-timezone=Asia/Shanghai"]
        },
        # 高德地图 MCP（Node.js，npx 运行；Windows 用 cmd /c）
        {
            "name": "Amap Maps MCP Server",
            "command": "cmd",
            "args": ["/c", "npx", "-y", "@amap/amap-maps-mcp-server"],  
            "env": {**os.environ, "AMAP_MAPS_API_KEY": gaode_demo_key} if gaode_demo_key else None,
            "disabled": not bool(gaode_demo_key),
        },
    ]

    client = MCPClient()        # 创建客户端实例
    try:
        # 连接多个服务器
        await client.connect_to_servers(server_configs)
        await client.chat_loop()         # 启动聊天循环
    finally:
        await client.clean()        # 无论是否出错，最后都清理资源


"""
运行方式：
    python my_mcp/client.py
    
现在支持多个 MCP 服务器：
- Demo Server: add 工具（计算两个数的和）
- Time MCP Server: get_current_time, convert_time 工具（时间相关）
- Amap Maps MCP Server: 高德地图 MCP 服务器
"""
if __name__ == "__main__":
    asyncio.run(main())

