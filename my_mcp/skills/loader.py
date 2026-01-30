"""
Skills 加载器：根据当前已连接的工具，从 my_mcp/skills 下的 Markdown 文件合并出 System Prompt。
"""
import os
from typing import List

# 当前包所在目录
_SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))

# 技能文件与工具名的对应关系：只有当前可用工具中命中时，才加载该技能说明
# key: 技能文件名（不含路径），value: 该技能对应的工具名集合或前缀
SKILL_TOOLS = {
    "base_prompt.md": None,  # None 表示始终加载
    "time_prompt.md": {"get_current_time", "convert_time"},
    "map_prompt.md": "maps_",  # 工具名以此前缀开头即视为地图相关
    "calculator_prompt.md": {"add"},
}


def _tool_matches(tool_name: str, condition) -> bool:
    if condition is None:
        return True
    if isinstance(condition, set):
        return tool_name in condition
    if isinstance(condition, str):
        return tool_name.startswith(condition)
    return False


def _should_load_skill(available_tool_names: List[str], condition) -> bool:
    if condition is None:
        return True
    for name in available_tool_names:
        if _tool_matches(name, condition):
            return True
    return False


def get_system_prompt(available_tool_names: List[str] | None = None) -> str:
    """
    根据当前可用工具名列表，加载并合并 skills 下的提示文件，生成 System Prompt。
    若 available_tool_names 为 None，则加载所有非 base 的技能（用于未连接服务器时的默认行为）。
    """
    if available_tool_names is None:
        available_tool_names = []
    parts = []
    for filename, condition in SKILL_TOOLS.items():
        if not _should_load_skill(available_tool_names, condition):
            continue
        path = os.path.join(_SKILLS_DIR, filename)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            parts.append(f.read().strip())
    return "\n\n---\n\n".join(parts) if parts else ""


def get_system_prompt_for_tools(tool_names: List[str]) -> str:
    """别名：根据工具名列表获取 system prompt。"""
    return get_system_prompt(tool_names)
