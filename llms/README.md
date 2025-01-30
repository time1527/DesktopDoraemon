**BaseChatModel**类：

- `_preprocess_messages*`：预处理消息，包括 根据最大输入 token 数截取，转换成多模态消息，转换成文本消息（如果大模型不支持多模态输入）
- `_postprocess_messages*`：后处理消息，包括 转换成多模态消息，后处理 stop words，转换成文本消息（如果大模型不支持多模态输入）
- 对话函数：根据配置以及是否 function call 选择
  - （未实现）`_chat_with_functions`
  - （未实现）`_continue_assistant_response`
  - （未实现）`_chat`
    - （未实现）`_chat_stream`
    - （未实现）`_chat_no_stream`
- `_convert_messages_*_to_target_type`：`Message`类转换成目标类

**BaseFnCallModel(BaseChatModel, ABC)**类：

- 关于 function call 更多的消息预处理和后处理
- 实现了`_chat_with_functions`和`_continue_assistant_response`

**TextChatAtOAI(BaseFnCallModel)**类：

- 实现了`_chat_stream`和`_chat_no_stream`

**QwenChatAtDS(BaseFnCallModel)**类：

- 实现了`_chat_stream`和`_chat_no_stream`
- 重写`_continue_assistant_response`
