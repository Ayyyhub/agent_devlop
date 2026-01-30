"""
MCP 客户端 Skills：通过 Markdown 文件管理 System Prompt，按已连接工具按需加载。
"""
from my_mcp.skills.loader import get_system_prompt, get_system_prompt_for_tools

__all__ = ["get_system_prompt", "get_system_prompt_for_tools"]
