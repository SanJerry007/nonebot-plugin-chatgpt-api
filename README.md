<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-chatgpt-api

_✨ ChatGPT (OpenAI API 接口版) ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/SanJerry007/nonebot-plugin-chatgpt-api.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-chatgpt-api">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-chatgpt-api.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 介绍

通过调用 OpenAI API 接口进行多轮对话、图像生成等任务，支持 ChatGPT、Genimi、DeepSeek 等多个模型。基于 `nonebot-plugin-chatgpt` 插件进行修改和扩展，提供更高效的 API 调用和自定义配置。

## 💿 安装

<details>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行，输入以下指令即可安装：

    nb plugin install nonebot-plugin-chatgpt-api

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下，打开命令行，根据你使用的包管理器，输入相应的安装命令：

<details>
<summary>pip</summary>

    pip install nonebot-plugin-chatgpt-api

</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-chatgpt-api

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-chatgpt-api

</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-chatgpt-api

</details>

打开 nonebot2 项目的 `bot.py` 文件，在其中写入：

    nonebot.load_plugin('nonebot_plugin_chatgpt_api')

</details>

## ⚙️ 配置

在 nonebot2 项目的 `.env` 文件中添加下表中的必填配置：

|             配置项              | 必填 |       默认值        |           说明            |
|:----------------------------:|:--:|:----------------:|:-----------------------:|
|       chatgpt_api_key        | 是  |                  |      OpenAI API 密钥      |
|       chatgpt_base_url       | 否  |       None       |   OpenAI API 调用的 URL    |
|    chatgpt_http_proxy_url    | 否  |       None       |        HTTP 代理地址        |
|        chatgpt_model         | 否  |      gpt-4o      |         调用的模型名称         |
|       chatgpt_bot_name       | 否  |     ChatGPT      |    机器人的名称（用于一些特定回复）     |
|  chatgpt_gen_args_json_file  | 否  |       None       |     生成参数的 JSON 文件路径     |
|     chatgpt_return_image     | 否  |      False       | 是否将回复以 markdown 格式渲染为图片 |
|       chatgpt_cd_time        | 否  |        5         |      聊天对话的冷却时间（秒）       |
|  chatgpt_timeout_time_chat   | 否  |        10        |       聊天的超时时间（分钟）       |
| chatgpt_timeout_time_setting | 否  |        5         |    与设置相关的命令的超时时间（分钟）    |
|   chatgpt_timeout_respond    | 否  |       True       |        超时后是否自动回复        |
|    chatgpt_log_api_stats     | 否  |       True       |    是否保存 API 调用统计信息日志    |
|  chatgpt_log_system_prompt   | 否  |       True       |      是否保存系统提示词历史日志      |
|   chatgpt_log_chat_history   | 否  |       True       |       是否保存对话历史日志        |

如果要更改日志保存路径，请在 `.env` 文件中额外设置 `LOCALSTORE_CACHE_DIR`，默认路径请参考[此处](https://github.com/nonebot/plugin-localstore?tab=readme-ov-file#cache-path)。

## 🎉 使用

默认配置下，`@机器人`加任意文本即可开始聊天。

|    指令    |  范围   |    说明     |
|:--------:|:-----:|:---------:|
|   /帮助    | 群聊/私聊 | 查看插件的使用帮助 |
| @机器人 提示词 | 群聊/私聊 |  修改系统提示词  |
| @机器人 刷新  | 群聊/私聊 |  开启新的对话   |
| @机器人 恢复  | 群聊/私聊 |  恢复上次的对话  |

## 🤝 贡献

### 🎉 鸣谢

感谢以下开发者对该项目做出的贡献：

<a href="https://github.com/SanJerry007/nonebot-plugin-chatgpt-api/graphs/contributors"> 
<img src="https://contrib.rocks/image?repo=SanJerry007/nonebot-plugin-chatgpt-api" /> 
</a>
