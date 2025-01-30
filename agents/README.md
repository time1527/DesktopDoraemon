**BaseAgent**类：

- 初始化：

  - `function_list`
  - `llm`
  - `memory`：长期记忆

- tool 相关：
  - `_init_tool`：将工具实例化
  - `_detect_tool`：检测一段文本是否意在调用工具，以及调用什么工具，参数是什么
  - `_call_tool`：调用工具
  - `get_tools_info`：得到所有工具的描述信息
  - `get_tools_name`：得到所有工具的名称
- llm 相关：
  - `_call_llm`：调用大模型
- `run`：整理消息和 config，再调用`_run`
- `_run`：agent 内部逻辑，when/where/how `_call_llm`/`_call_tool`

**ChatAgent(BaseAgent)**类：相当于只`_call_llm`

**ReAct(BaseAgent)**类：

- `_format_react_messages`：将消息整理成 ReAct 格式

- `_detect_tool`：根据 ReAct 关键词去检测是否意在调用工具，以及调用什么工具，参数是什么
- `_run`：ReAct 逻辑。在最大尝试次数内，调用`_call_llm`和`_detect_tool`，如果不需要调用工具，结束；否则调用工具，继续生成

**DoraemonAgent(ReAct)**类：

* `_format_text_messages`：将消息整理成文本格式（`ReAct._format_react_messages`的前部分）
* `_check`：额外调用一次llm从`MemoryTool`的`Observation`里提取有用的相关信息——可以使用另一个llm，也可以进一步拆解成两个agent（multi-agent）
* `_run`：ReAct 逻辑，但如果调用的工具是`MemoryTool`，则工具返回的`Observation`使用`_check`进一步处理，处理后作为“正式”的`Observation`



