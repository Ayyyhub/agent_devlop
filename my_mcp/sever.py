from my_mcp.server.fastmcp import FastMCP

# 创建一个名叫 Demo 的 MCP 服务
mcp = FastMCP('Demo')

# 把 add 函数注册成一个 MCP 工具，供客户端调用
@mcp.tool()
def add(a:int, b:int) ->int:
  """"
  计算两个整数的和并返回
  """
  return a+b

if __name__ == "__main__":
  # 用 stdin/stdout 作为传输通道运行 MCP 服务器，方便被 stdio_client 连接
  mcp.run(transport='stdio')

