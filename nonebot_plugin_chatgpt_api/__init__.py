from nonebot import require
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_htmlrender")

from .matcher import *  # must import this to enable `matcher.enhanced_got()`
from .command import *
from .config import ChatGPTConfig

# DEBUG = True
# if DEBUG:
#     import pydevd_pycharm
#     pydevd_pycharm.settrace("127.0.0.1", port=5678, stdoutToServer=True, stderrToServer=True)

__plugin_meta__ = PluginMetadata(
    name="chatgpt_api",
    description="通过调用OpenAI API进行多轮对话、图像生成等任务，支持ChatGPT、Genimi、DeepSeek等多个模型，基于nonebot-plugin-chatgpt插件修改",
    usage="@bot [内容]",
    type="application",
    homepage="https://github.com/SanJerry007/nonebot-plugin-chatgpt-api",
    config=ChatGPTConfig,
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~qq",
        "~console",
    },
)
