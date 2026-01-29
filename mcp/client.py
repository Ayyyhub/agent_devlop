import asyncio
import json
from typing import Optional
from contextlib import AsyncExitStack
from openai import OpenAI
import os

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")

class MCPClient:

    def __init__(self):
        self.exit_stack = AsyncExitStack()    # 用 AsyncExitStack 管理异步资源（子进程、连接等）
        self.opanai_api_key = openai_api_key  # 调用模型的api_key
        self.base_url = openai_base_url  # 调用模型url, 这里以deepseek作演示
        self.model = "gpt-4o-mini"
        self.client = OpenAI(api_key=self.opanai_api_key, base_url=self.base_url)
        self.session: Optional[ClientSession] = None  # Optional提醒用户该属性是可选的，可能为None
        self.exit_stack = AsyncExitStack()  # 用来存储和清楚对话中上下文的，提高异步资源利用率

    async def connect_to_server(self, server_script_path):
        """连接 MCP 服务器的异步函数"""
        server_params = StdioServerParameters(    # 配置启动 MCP 服务器的参数 —— 用 python 命令执行传入的 server_script_path（比如 server.py）
            command="python",
            args=[server_script_path],
            env=None
        )  # 设置启动服务器的参数, 这里是要用python执行server.py文件

        # 启动MCP服务器并建立通信通道
        # 1、stdio_client(server_params)：创建一个 stdio 客户端上下文管理器, 根据 server_params（如 python sever.py）启动服务器子进程
        # 2、self.exit_stack.enter_async_context：使用 AsyncExitStack 管理异步资源, 进入上下文时启动服务器进程, 退出时自动清理（关闭进程、管道等）
        # 3、stdio_transport：返回一个元组 (stdio, write)，用于后续通信
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        # 元组解包，分别赋值给实例属性，self.stdio：保存读取流，self.write：保存写入函数
        self.stdio, self.write = stdio_transport
        # ClientSession：创建 MCP 客户端会话对象，后续的交互（比如调用工具）都靠这个 self.session；
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()  # 正式初始化和服务器的连接，相当于 “握手”；

        # 列出MCP服务器上的工具
        response = await self.session.list_tools()    # list_tools() 从服务器 sever 拿到所有 MCP 工具，并打印
        tools = response.tools
        print("\n已连接到服务器，支持以下工具:", [tool.name for tool in tools])  # 打印服务端可用的工具

    async def process_query(self, query: str) -> str:
        """用大模型处理一次 query + 工具调用"""
        messages = [{"role": "user", "content": query}]    # 构造用户消息（符合大模型的消息格式）
        tools_response = await self.session.list_tools()      # 获取服务器可用工具

        # 把服务器工具转换成大模型能识别的格式
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
        } for tool in tools_response.tools]

        # 1、调用大模型，传入问题和可用工具
        model_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools
        )
        # 0、self.client.chat.completions.create：这里是“自己写 Agent 框架”，所以必须用底层客户端
        # 1. 换成 ChatOpenAI，返回的是 LangChain 的消息对象，不是 response.choices[0] 那种结构
        # 2. 换成 create_react_agent，create_react_agent 本身 就是一个 Agent，内部已经帮你：《调工具》 《处理多轮循环》 《管理状态》
        # 你不会再在外面写 chat.completions.create(...) 和 finish_reason == "tool_calls" 这些底层逻辑

        # 处理返回内容
        content = model_response.choices[0]
        # 判断这一次模型输出，是“直接给最终答案”，还是“想要调用工具”？
        if content.finish_reason == "tool_calls":
            # 模型判断需要调用工具：解析工具名和参数
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            # 调用MCP服务器上的工具
            result = await self.session.call_tool(tool_name, tool_args)
            print(f"\n\n[Calling tool {tool_name} with args {tool_args}]\n\n")
            # 将模型返回的调用工具的对话记录保存在messages中
            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result.content[0].text,
                "tool_call_id": tool_call.id,
            })
            # 2、再次调用大模型，将上面的结果返回给大模型用于生产最终结果
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content

        # 模型不需要调用工具，直接返回最终答案
        return content.message.content

    async def chat_loop(self):
        """运行交互式聊天"""
        print("\n MCP客户端已启动！输入quit退出")

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
        """清理资源"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:       # 检查命令行参数是否足够
        print("使用方法是： python client.py server.py")
        sys.exit(1)

    client = MCPClient()        # 创建客户端实例
    try:
        # 连接服务器,sys.argv[1] 就是你传进来的 sever.py 路径，然后在 connect_to_server 里用来启动服务器
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()         # 启动聊天循环
    finally:
        await client.clean()        # 无论是否出错，最后都清理资源


"""
运行方式：
    python mcp/client.py mcp/sever.py
"""
if __name__ == "__main__":
    import sys

    asyncio.run(main())

