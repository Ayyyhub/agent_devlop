《功能》	             《create_agent + checkpointer(weather_agent)》	  《create_react_agent + AgentExecutor(agent_example)》

单次调用内的思维记忆	 ✅ 框架自动处理（LangGraph 内部状态管理）	          ✅ 通过 agent_scratchpad 手动管理
跨次调用的会话记忆	     ✅ 通过 checkpointer + thread_id	              ❌ 没有
状态管理方式	         LangGraph 自动管理	                              手动在 prompt 中定义 {agent_scratchpad}
