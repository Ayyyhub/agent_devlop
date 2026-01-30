# MCP 客户端 Skills（方案一：System Prompt）

通过 Markdown 文件管理 **System Prompt**，按当前已连接的工具按需加载，引导模型在合适时使用 Time、地图、计算等工具。

## 结构

- **base_prompt.md**：通用角色说明，始终加载。
- **time_prompt.md**：时间相关（`get_current_time`、`convert_time`）时加载。
- **map_prompt.md**：存在以 `maps_` 开头的地图工具时加载。
- **calculator_prompt.md**：存在 `add` 工具时加载。

## 扩展新技能

1. 在 `mcp/skills/` 下新增 `xxx_prompt.md`，写好何时使用、如何传参等说明。
2. 在 `loader.py` 的 `SKILL_TOOLS` 中增加一项：
   - key：文件名，如 `"xxx_prompt.md"`
   - value：`None`（始终加载）、工具名集合 `{"tool_a", "tool_b"}`，或前缀字符串 `"prefix_"`。
3. 客户端无需改逻辑，下次请求会自动按当前可用工具合并并注入 System Prompt。

## 使用

客户端在 `process_query` 中调用 `get_system_prompt(tool_names)`，将返回内容作为第一条 `role=system` 的消息传入大模型即可（已集成在 `mcp/client.py`）。
