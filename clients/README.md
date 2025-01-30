**BubbleMessage**类：类似微信消息的前端

**TextMessage**类：文本消息前端

**ImageMessage**类：图像消息前端

**BaseClient**类：

- 初始化：

  - `history`

- ui 相关：
  - `init_ui`：初始化对话界面，并展示几个消息
- agent 相关：

  - （未实现）`init_model`：初始化 agent
  - （未实现）`generate`：agent 生成，及结果整理

- `send_msg`：发送消息 + agent 生成回复，并展示在前端

- `message_to_bubble_messages`：agent 返回的`Message`类转换成前端的`BubbleMessage`类
- `add_history`：前端的`BubbleMessage`类转换成`Message`类，并添加在历史中

**ChatClient(BaseClient)**类：使用`ChatAgent`——只进行对话

**ReActClient(BaseClient)**类：使用`ReAct`——ReAct 逻辑

**DoraemonClient(BaseClient)**类：使用`DoraemonAgent`——ReAct 逻辑+对`MemoryTool`的额外llm call处理
