from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")
require("nonebot_plugin_htmlrender")

from .matcher import *  # must import this to enable `matcher.enhanced_got()`
from .command import *
from .config import ChatGPTAPIConfig

__plugin_meta__ = PluginMetadata(
    name="ChatGPT (OpenAI API 接口版)",
    description="通过调用 OpenAI API 接口进行多轮对话、图像生成等任务，支持 ChatGPT、Gemini、DeepSeek 等多个模型，基于 `nonebot-plugin-chatgpt` 插件修改",
    usage="@bot [内容]",
    type="application",
    homepage="https://github.com/SanJerry007/nonebot-plugin-chatgpt-api",
    config=ChatGPTAPIConfig,
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~console",
    },
)
