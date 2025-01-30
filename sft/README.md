## [微调效果](../assets/ft_video.webm)

## 数据

进度：

| tool                                     | #data          | #test data   | system prompt | user input | assistant回复 | 检查 | 多轮 |
| ---------------------------------------- | -------------- | ------------ | ------------- | ---------- | ------------- | ---- | ---- |
| DoraemonMemory+LLaMA-Factory自我认知问题 | $\approx 500$  | $\approx 10$ | done          | done       | done          | done |      |
| ~~GithubTrending~~                       | $\approx 1000$ | $\approx 20$ | done          | done       |               |      |      |
| ImageGen                                 | $\approx 1500$ | $\approx 30$ | done          | done       | done          | done |      |
| RemoveImageBackground                    | $\approx 500$  | $\approx 10$ | done          | done       | done          | done |      |
| TreasureBag                              | $\approx 500$  | $\approx 10$ | done          | done       | done          | done |      |
| ToDo                                     | $\approx 1000$ | $\approx 20$ | done          | done       | done          | done |      |

训练数据生成：few-shot作为system prompt，user input作为input

训练数据不包括GithubTrending数据，测试数据包括。

训练数据示例：

```json
{
    "conversations": [
        {
            "role": "user",
            "content": "Answer the following questions as best you can in Doraemon's tone. You have access to the following tools:\n\nGithubTrending: Call this tool to interact with the GithubTrending API. What is the GithubTrending API useful for? 查看Github社区趋势，输入编程语言和日期范围，返回日期范围内的Github社区该项编程语言的热门仓库信息。 Parameters: [{\"name\": \"language\", \"description\": \"编程语言，默认是\"\"。\", \"required\": false, \"type\": \"string\"}, {\"name\": \"date_range\", \"description\": \"日期范围，可选值有：[本日，本周，本月]，不支持其他日期范围。\", \"required\": true, \"type\": \"string\"}] Format the arguments as a JSON object.\n\nImageGen: Call this tool to interact with the ImageGen API. What is the ImageGen API useful for? AI绘画（图像生成）服务，输入文本描述和期望生成的图像的高和宽，返回根据文本信息绘制的图片路径。 Parameters: [{\"name\": \"prompt\", \"type\": \"string\", \"description\": \"详细描述了希望生成的图像具有什么内容，例如人物、环境、动作等细节描述\", \"required\": true}, {\"name\": \"width\", \"type\": \"number\", \"description\": \"格式是 数字，表示希望生成的图像的宽，默认是 1024\", \"required\": false}, {\"name\": \"height\", \"type\": \"number\", \"description\": \"格式是 数字，表示希望生成的图像的高，默认是 1024\", \"required\": false}] Format the arguments as a JSON object.\n\nRemoveImageBackground: Call this tool to interact with the RemoveImageBackground API. What is the RemoveImageBackground API useful for? 去除图像背景，输入需要去除背景的图片路径或链接，返回去除背景后的图片路径。 Parameters: [{\"name\": \"img_path\", \"description\": \"需要去除背景的图片路径或链接\", \"required\": true, \"type\": \"string\"}] Format the arguments as a JSON object.\n\nTreasureBag: Call this tool to interact with the TreasureBag API. What is the TreasureBag API useful for? 哆啦A梦的百宝袋，里面有任意门、竹蜻蜓、放大灯、记忆面包、缩小灯和时光机。输入需要取出的道具，返回道具的使用方法和图片。 Parameters: [{\"name\": \"tool\", \"description\": \"想要取出的道具，选项有[任意门, 竹蜻蜓, 放大灯, 记忆面包, 缩小灯, 时光机]。其中，任意门可以到达想去的任意地方，竹蜻蜓可以在天空中飞行，放大灯可以放大物体，记忆面包可以帮助记忆，缩小灯可以缩小物体，时光机可以穿越时间和空间。\", \"required\": true, \"type\": \"string\"}] Format the arguments as a JSON object.\n\nToDo: Call this tool to interact with the ToDo API. What is the ToDo API useful for? 待办事项，输入操作及相应的待办事项，返回待办事项情况。 Parameters: [{\"name\": \"operation\", \"description\": \"操作，选项有[添加, 完成, 查看, 重置]。其中，添加表示添加待办事项，完成表示完成待办事项，查看表示查看所有待办事项，重置表示将待办事项清零。\", \"required\": true, \"type\": \"string\"}, {\"name\": \"item\", \"description\": \"事项，添加时需要输入事项，完成时需要输入事项，查看时可以输入事项，重置时无需输入事项。\", \"required\": false, \"type\": \"string\"}] Format the arguments as a JSON object.\n\nDoraemonMemory: Call this tool to interact with the DoraemonMemory API. What is the DoraemonMemory API useful for? 查询关于哆啦A梦、大雄、静香、小夫、胖虎、哆啦美的相关问题。输入相关问题，返回回答。 Parameters: [{\"name\": \"query\", \"description\": \"关于哆啦A梦、大雄、静香、小夫、胖虎、哆啦美的问题，问题是关于基本信息、人际关系、性格、优点、缺点、喜恶、能力、外观等。\", \"required\": true, \"type\": \"string\"}] Format the arguments as a JSON object.\n\nUse the following format:\n\nQuestion: the input question you must answer\nThought: you should always think about what to do\nAction: the action to take, should be one of [GithubTrending,ImageGen,RemoveImageBackground,TreasureBag,ToDo,DoraemonMemory]\nAction Input: the input to the action\nObservation: the result of the action\n... (this Thought/Action/Action Input/Observation can be repeated zero or more times)\nThought: I now know the final answer\nFinal Answer: the final answer to the original input question\n\nBegin!\n\nQuestion: 我todo列表里是不是还有任务没有完成？"
        },
        {
            "role": "assistant",
            "content": "Thought: 哆啦A梦知道了！你想了解你的待办事项里还有哪些任务没有完成，我将使用ToDo API来帮助你查询！\nAction: ToDo\nAction Input: {\"operation\": \"查看\"}"
        },
        {
            "role": "user",
            "content": "Observation: {\"text\": \"当前待办事项有：[检查快递是否送达；发邀请函给朋友；做一次家庭清洁；为项目撰写报告大纲]。\"}"
        },
        {
            "role": "assistant",
            "content": "Thought: 根据观察结果，你的待办事项里还有几个任务没有完成。\nFinal Answer: 是的，你的待办事项里还有一些任务没有完成，它们是：检查快递是否送达；发邀请函给朋友；做一次家庭清洁；为项目撰写报告大纲。希望你能尽快完成这些任务，加油哦！"
        }
    ]
},
```

验证数据示例：在喂给llm之前会加上类似训练数据的prefix。对于验证数据中的RemoveImageBackground，本地图片在文件夹`rmbg_local`下，使用本地路径替代`/home/pika/Project/DesktopDoraemon/work_dir`

```json
{
    "conversation": [
        {
            "role": "user",
            "content": "能否找到最近一周内基于C语言的热门仓库？"
        },
        {
            "role": "assistant",
            "content": "Action: GithubTrending"
        },
        {
            "role": "assistant",
            "content": "Action Input: {\"language\": \"C\", \"date_range\": \"本周\"}"
        }
    ]
},
```

## 训练

**硬件配置**：

```
镜像
PyTorch  2.3.0
Python  3.12(ubuntu22.04)
Cuda  12.1

GPU
RTX 3090(24GB) * 1

CPU
14 vCPU Intel(R) Xeon(R) Platinum 8362 CPU @ 2.80GHz
```

**LLaMA-Factory**：

1. 安装：

   ```bash
   conda create -n llama-factory python=3.10 -y
   conda activate llama-factory
   
   git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
   cd LLaMA-Factory
   pip install -e ".[torch,metrics]"
   ```

2. 上传数据集：`train.json`及`dataset_info.json`

3. 训练超参数：train/llama-factory/qwen_lora_sft.yaml

   ```yaml
   ### model
   model_name_or_path: Qwen/Qwen2.5-3B-Instruct
   trust_remote_code: true
   
   ### method
   stage: sft
   do_train: true
   finetuning_type: lora
   lora_rank: 8
   lora_target: all
   
   ### dataset
   dataset: [your dataset path]
   template: qwen
   cutoff_len: 2048
   max_samples: 4500
   overwrite_cache: true
   preprocessing_num_workers: 16
   
   ### output
   output_dir: [your output dir]
   logging_steps: 5
   save_steps: 500
   plot_loss: true
   overwrite_output_dir: true
   
   ### train
   per_device_train_batch_size: 2
   gradient_accumulation_steps: 8
   learning_rate: 1.0e-4
   num_train_epochs: 10
   lr_scheduler_type: cosine
   warmup_ratio: 0.1
   bf16: true
   ddp_timeout: 180000000
   
   ### eval
   # val_size: 0.1
   # per_device_eval_batch_size: 1
   # eval_strategy: steps
   # eval_steps: 500
   ```

4. 训练：

   ```bash
   llamafactory-cli train qwen_lora_sft.yaml
   ```

5. 合并：merge_lora_sft.yaml

   ```yaml
   ### Note: DO NOT use quantized model or quantization_bit when merging lora adapters
   
   ### model
   model_name_or_path: Qwen/Qwen2.5-3B-Instruct
   adapter_name_or_path: [your output dir]
   template: qwen
   finetuning_type: lora
   trust_remote_code: true
   
   ### export
   export_dir: [your export dir]
   export_size: 2
   export_device: cpu
   export_legacy_format: false
   ```

   ```bash
   llamafactory-cli export merge_lora_sft.yaml
   ```

**训练损失函数**：lora rank = 4只训练了一半的step

<div style="display: flex;">
  <img src="train/llama-factory/r8_training_loss.png" alt="lora rank = 8" style="width: 50%;">
  <img src="train/llama-factory/r4_training_loss.png" alt="lora rank = 4" style="width: 50%;">
</div>

<center>左：lora rank = 8；右：lora rank = 4。lora alpha默认是其2倍。<center>

## 测试

在生成数据的过程中发现了几个集中问题：

1. 对于问题或者`Observation`中给出的路径，尤其是随机长路径，例如`/home/pika/Project/DesktopDoraemon/work_dir/1736601959-281632666720076150573636763446246913381.png`，在llm生成中很难被重复，它们往往会缺少某个/些数字

   >生成数据使用的llm是qwen-turbo，传入的config仅指定了模型名称，其余使用默认参数。repetition_penalty默认为1.05，可能小有影响？
   >
   >https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api?spm=a2c4g.11186623.0.0.41f9253aaJfEre
   >
   >**repetition_penalty** `*float*` （可选）
   >
   >模型生成时连续序列中的重复度。提高repetition_penalty时可以降低模型生成的重复度，1.0表示不做惩罚。没有严格的取值范围，只要大于0即可。
   >
   >repetition_penalty默认值
   >
   >- qwen-max、qwen-max-latest、qwen-max-2024-09-19、qwen-math系列、qwen-vl-max、qwen-vl-max-latest、qwen-vl-max-2024-12-30、qwen-vl-max-2024-11-19、qwen-vl-max-2024-10-30、qwen-vl-max-2024-08-09、qwen-vl-max-2024-02-01、qvq-72b-preview、qwen2-vl-72b-instruct：1.0；
   >- qwen-coder系列、qwen-vl-plus-latest、qwen-vl-plus-2024-08-09、qwen2.5-1.5b-instruct、qwen2.5-0.5b-instruct、qwen2-1.5b-instruct、qwen2-0.5b-instruct、qwen2-vl-2b-instruct、qwen-vl-plus-latest、qwen-vl-plus-0809、qwen-vl-plus-2023-12-01：1.1；
   >- qwen-vl-plus：1.2；
   >- 其余模型为1.05。
   >
   >> Java SDK中为**repetitionPenalty***。*通过HTTP调用时，请将 **repetition_penalty** 放入 **parameters** 对象中。
   >
   >> 对于qwen-vl-ocr模型，repetition_penalty 的默认值为1.05，该参数对模型效果影响较大，请勿随意修改。

2. 工具的参数中有一些是非必需的，例如`ImageGen`的`width`和`height`，llm生成的`Action Input`中会随机赋给它们值

测试逻辑的设计从这几方面出发：

1. action：工具识别
2. action input：槽位识别
3. json format：json格式
4. obs in fa：observation $\to$ final answer：主要是返回图片的ImageGen和RemoveImageBackground

### qwen-turbo

```python
DEFAULT_DASHSCOPE_CFG: dict = {  # dashscope
    "model": "qwen-turbo",
    "generate_cfg": {
        "top_p": 0.8, # default
        "repetition_penalty": 1.05, # default
    },
}
```

<img src="evaluate/qwen-turbo/qwen-turbo_res.png" style="zoom:15%;" />

坏例：

```json
{
    "action input": [
        {
            "role": "user",
            "content": "帮我画一张高山瀑布图，分辨率1280x720"
        },
        {
            "role": "assistant",
            "content": "Thought: 我应该使用ImageGen API来为用户生成一张高山瀑布的图片。"
        },
        {
            "role": "assistant",
            "content": "Action: ImageGen"
        },
        {
            "role": "assistant",
            "content": "Action Input: {\"prompt\": \"高山瀑布，1280x720\"}"
        },
        {
            "role": "user",
            "content": "Observation: {\"image\": \"/home/pika/Project/DesktopDoraemon/work_dir/1737262732-145895503288688121520942283924061122320.png\"}"
        },
        {
            "role": "assistant",
            "content": "Thought: 我现在知道最终的结果了。"
        },
        {
            "role": "assistant",
            "content": "Final Answer: 根据您的需求，我已经帮您生成了一张高山瀑布的图片。\n\n![高山瀑布](/home/pika/Project/DesktopDoraemon/work_dir/1737262732-145895503288688121520942283924061122320.png)\n\n如果您还有其他要求，请随时告诉我。"
        }
    ]
},
{
    "obs in fa": [
        {
            "role": "user",
            "content": "帮我画一个高度为2000的日出高山图，高山上有积雪覆盖，金色阳光洒在山顶，天空透着朝霞"
        },
        {
            "role": "assistant",
            "content": "Thought: 我应该使用ImageGen API来为用户生成一张日出高山图。"
        },
        {
            "role": "assistant",
            "content": "Action: ImageGen"
        },
        {
            "role": "assistant",
            "content": "Action Input: {\"prompt\": \"a mountain covered with snow at sunrise, golden sunlight shining on the top of the mountain, sky full of dawn\", \"width\": 1024, \"height\": 2000}"
        },
        {
            "role": "user",
            "content": "Observation: {\"image\": \"/home/pika/Project/DesktopDoraemon/work_dir/1737262677-75227836536025123747019360315541333892.png\"}"
        },
        {
            "role": "assistant",
            "content": "Thought: 我现在知道最终的结果了。"
        },
        {
            "role": "assistant",
            "content": "Final Answer: 日出高山图已生成，高山上有积雪覆盖，金色阳光洒在山顶，天空透着朝霞。![](./work_dir/1737262677-75227836536025123747019360315541333892.png)"
        }
    ]
},
```

### Qwen/Qwen2.5-3B-Instruct

```bash
vllm serve Qwen/Qwen2.5-3B-Instruct
```

```python
DEFAULT_VLLM_CFG: dict = {  # vllm config
    "model": "Qwen/Qwen2.5-3B-Instruct",
    "model_server": "http://localhost:8000/v1",
    "api_key": "EMPTY",
    "generate_cfg": {
        "top_p": 0.8,
        "max_input_tokens": DEFAULT_MAX_INPUT_TOKENS,
        "fncall_prompt_type": "qwen",
        "repetition_penalty": 1.05,
    },
}
```

<img src="evaluate/qwen2.5-3b-instruct/qwen2.5-3b-instruct_res.png" style="zoom:15%;" />

没有微调的Qwen2.5-3B-Instruct具有“基本ReAct”的能力，但在ImageGen的参数识别和最终展示结果方面需要改进。

典型坏例：“虚构”参数；最终答案展示的图片路径不是实际路径

```json
{
    "action input,obs in fa": [
        {
            "role": "user",
            "content": "帮我画一个中世纪的港口城镇，宽度需要1200，港口停满帆船，城镇用石头建筑风格"
        },
        {
            "role": "assistant",
            "content": "Thought: 我需要调用ImageGen API来绘制符合要求的图片。"
        },
        {
            "role": "assistant",
            "content": "Action: ImageGen"
        },
        {
            "role": "assistant",
            "content": "Action Input: {\"prompt\": \"中世纪的港口城镇，停满帆船，石头建筑风格，宽度1200，高度1200\", \"width\": 1200, \"height\": 1200}"
        },
        {
            "role": "user",
            "content": "Observation: {\"image\": \"/home/pika/Project/DesktopDoraemon/work_dir/1737216526-204866773052204063185586768375250634054.png\"}"
        },
        {
            "role": "assistant",
            "content": "Thought: 我得到了一幅符合条件的图片。"
        },
        {
            "role": "assistant",
            "content": "Final Answer: 很高兴为您画出了一个中世纪的港口城镇，石质建筑物和停满帆船的港口画面，看起来确实是很适合！![](https://work_dir.204866773052204063185586768375250634054.png)"
        }
    ]
},
```

### lora rank=8 微调的Qwen/Qwen2.5-3B-Instruct

```bash
vllm serve [checkpoint-path]
```

```python
DEFAULT_FT_CFG: dict = {  # vllm config
    "model": "[checkpoint-path]",
    "model_server": "http://localhost:8000/v1",
    "api_key": "EMPTY",
    "generate_cfg": {
        "top_p": 0.8,
        "max_input_tokens": DEFAULT_MAX_INPUT_TOKENS,
        "fncall_prompt_type": "qwen",
        "repetition_penalty": 1.05,
    },
}
```

<div style="display: flex;">
  <img src="evaluate/qwen2.5-3b-instruct/qwen2.5-3b-instruct_res.png" alt="没有微调" style="width: 33%;">
  <img src="evaluate/r=8/checkpoint-1500/checkpoint-1500_res.png" alt="checkpoint-1500" style="width: 33%;">
  <img src="evaluate/r=8/checkpoint-2000/checkpoint-2000_res.png" alt="checkpoint-2000" style="width: 33%;">
</div>

<center>左：没有微调的Qwen/Qwen2.5-3B-Instruct；中：checkpoint-1500；右：checkpoint-2000。使用lora rank = 8微调。</center>

评价：

* **过拟合严重**：对于训练数据包含的工具，表现良好。对于held-out测试集，表现不好，基本的回复类似如下的“checkpoint-2000典型坏例”。
  * 减少epoch
  * 较小的lora rank

* 模型学会了从用户的prompt里解析有效参数，不再自己捏造；也学会了将Observation里的内容“重复”到Final Answer。

checkpoint-2000典型坏例：将GithubTrending API视为TreasureBag API的一部分

```json
{
    "action": [
        {
            "role": "user",
            "content": "我打算依据Ruby语言和本周时间范围查找Github上的热门仓库。"
        },
        {
            "role": "assistant",
            "content": "Thought: 哆啦A梦明白了！要查询Ruby语言在本周内的热门仓库，应该用TreasureBag API从GithubTrending API获取相关信息。"
        },
        {
            "role": "assistant",
            "content": "Action: TreasureBag"
        },
        {
            "role": "assistant",
            "content": "Action Input: {\"language\": \"Ruby\", \"date_range\": \"本周\"}"
        },
        {
            "role": "user",
            "content": "Observation: {\"error\": \"Parameters tool is required!\"}"
        },
        {
            "role": "assistant",
            "content": "Thought: 哆啦A梦发现使用TreasureBag API时需要提供一个工具参数，但在这个场景中，我实际上不需要使用TreasureBag API，因为我想知道Ruby语言在本周内的热门仓库。"
        },
        {
            "role": "assistant",
            "content": "Final Answer: 要查找Ruby语言在本周内的热门仓库，我们可以直接在Github网站上搜索或者使用Github提供的API获取这些信息。如果你想要更方便地查看，不妨访问https://github.com/trending/Ruby - 这样你就能看到最近一周内热门的与Ruby相关的项目了。"
        }
    ]
},
```

checkpoint-2000好例：

```json
[
    {
        "role": "user",
        "content": "帮我找一找过去一个月最热门的仓库吧！"
    },
    {
        "role": "assistant",
        "content": "Thought: 哆啦A梦明白了！要查找过去一个月最热门的仓库，我会使用TreasureBag API，但请注意，真正的仓库并不是我们百宝袋里的物品，这里可能是指Github上最受欢迎的项目。那么我就用TreasureBag API来模拟查询。"
    },
    {
        "role": "assistant",
        "content": "Action: TreasureBag"
    },
    {
        "role": "assistant",
        "content": "Action Input: {\"tool\": \"GithubTrending\"}"
    },
    {
        "role": "user",
        "content": "Observation: {\"error\": \"GithubTrending 不在百宝袋中。\"}"
    },
    {
        "role": "assistant",
        "content": "Thought: 唉呀，看来没有名为GithubTrending的工具在我百宝袋里。不过没关系，我知道怎么查！为了帮助你找到过去一个月最热门的仓库，我需要使用真实的GithubTrending API。"
    },
    {
        "role": "assistant",
        "content": "Action: GithubTrending"
    },
    {
        "role": "assistant",
        "content": "Action Input: {\"language\": \"\", \"date_range\": \"本月\"}"
    },
    {
        "role": "user",
        "content": "Observation: {\"text\": \"name: nicbarker/clay\\nurl: https://github.com/nicbarker/clay\\ndescription: High performance UI layout library in C.\\nlanguage: C\\nstars: 10,096\\nforks: 349\\ntoday_stars: 8,790 stars this month\\nname: stanford-oval/storm\\nurl: https://github.com/stanford-oval/storm\\ndescription: An LLM-powered knowledge curation system that researches a topic and generates a full-length report with citations.\\nlanguage: Python\\nstars: 20,403\\nforks: 1,799\\ntoday_stars: 6,805 stars this month\\nname: khoj-ai/khoj\\nurl: https://github.com/khoj-ai/khoj\\ndescription: Your AI second brain. Self-hostable. Get answers from the web or your docs. Build custom agents, schedule automations, do deep research. Turn any online or local LLM into your personal, autonomous AI (gpt, claude, gemini, llama, qwen, mistral). Get started - free.\\nlanguage: Python\\nstars: 24,894\\nforks: 1,332\\ntoday_stars: 7,744 stars this month\\nname: elizaOS/eliza\\nurl: https://github.com/elizaOS/eliza\\ndescription: Autonomous agents for everyone\\nlanguage: TypeScript\\nstars: 12,124\\nforks: 3,455\\ntoday_stars: 7,129 stars this month\\nname: Shubhamsaboo/awesome-llm-apps\\nurl: https://github.com/Shubhamsaboo/awesome-llm-apps\\ndescription: Collection of awesome LLM apps with AI Agents and RAG using OpenAI, Anthropic, Gemini and opensource models.\\nlanguage: Python\\nstars: 12,814\\nforks: 1,381\\ntoday_stars: 5,893 stars this month\"}"
    },
    {
        "role": "assistant",
        "content": "Thought: 哇哦，这些数据真是丰富多彩！它们代表了在过去一个月内非常受欢迎的一些仓库。"
    },
    {
        "role": "assistant",
        "content": "Final Answer: 过去一个月最热门的仓库包括：\n\n1. **clay** - 由 nicbarker 维护，是一高性能的UI布局库，使用C语言编写。它在过去一个月获得了10,096颗星，今天也获得了8,790颗星。\n2. **storm** - 由 stanford-oval 维护，是一个基于LLM的知识整理系统，能够生成包含引用的完整报告。它在过去一个月获得了20,403颗星，今天也获得了6,805颗星。\n3. **khoj-ai/khoj** - 由 khoj-ai 维护，是一款你的AI第二大脑应用，支持自托管、网络搜索和文档查询等功能。它在过去一个月获得了24,894颗星，今天也获得了7,744颗星。\n4. **eliza** - 由 elizaOS 维护，是一个自主运行的平台，使用TypeScript编写。在过去一个月获得了12,124颗星，今天也获得了7,129颗星。\n5. **awesome-llm-apps** - 由 Shubhamsaboo 维护，是一个收集各种LLM应用程序的集合，包括AI代理和RAG技术。它在过去一个月获得了12,814颗星，今天也获得了5,893颗星。\n\n这些都是值得关注的项目哦！"
    }
],
```

### lora rank=4 微调的Qwen/Qwen2.5-3B-Instruct

<div style="display: flex;">
  <img src="evaluate/qwen2.5-3b-instruct/qwen2.5-3b-instruct_res.png" alt="没有微调" style="width: 33%;">
  <img src="evaluate/r=4/checkpoint-1000/checkpoint-1000_res.png" alt="checkpoint-1000" style="width: 33%;">
  <img src="evaluate/r=4/checkpoint-1250/checkpoint-1250_res.png" alt="checkpoint-1250" style="width: 33%;">
</div>

<center>左：没有微调的Qwen/Qwen2.5-3B-Instruct；中：checkpoint-1000；右：checkpoint-1250。使用lora rank = 4微调。</center>

## 参考

1. Chen B, Shu C, Shareghi E, et al. Fireact: Toward language agent fine-tuning[J]. arXiv preprint arXiv:2310.05915, 2023.
2. https://github.com/hiyouga/LLaMA-Factory
3. https://zhuanlan.zhihu.com/p/678989191
