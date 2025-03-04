import datetime
import os.path
from typing import Optional

from nonebot import get_driver, get_plugin_config
from nonebot.log import logger
from pydantic import BaseModel

from .utils import load_json


class ChatGPTAPIConfig(BaseModel):
    chatgpt_bot_name: str = "ChatGPT"  # 机器人的名称，在一些特定的回复中会用到
    chatgpt_model: str = "gpt-4o"
    chatgpt_api_key: str = None
    chatgpt_base_url: Optional[str] = None
    chatgpt_http_proxy_url: Optional[str] = None  # HTTP 代理地址

    chatgpt_gen_args_json_file: Optional[str] = None  # 生成参数的 JSON 文件路径，包含temperature等信息
    chatgpt_gen_args: Optional[dict] = None  # 具体的生成参数，优先级低于文件配置

    chatgpt_return_image: bool = False  # 是否将回复以markdown格式渲染为图片，然后回复此图片，而不是直接回复文本
    chatgpt_cd_time: int = 5  # 聊天对话的冷却时间(秒), <=0 代表无冷却
    chatgpt_timeout_time_chat: int = 10  # 聊天的超时时间(分钟), <=0 代表无超时
    chatgpt_timeout_time_setting: int = 5  # 与设置相关的命令的超时时间(分钟), <=0 代表无超时
    chatgpt_timeout_respond: bool = True  # 超时后是否自动回复

    chatgpt_log_api_stats: bool = True  # 是否保存`API调用统计信息`到文件
    chatgpt_log_system_prompt: bool = True  # 是否保存`系统提示词历史`到文件（若关闭则每次重启bot后，用户都要手动设置提示词）
    chatgpt_log_chat_history: bool = True  # 是否保存`对话历史`到文件（若关闭则无法恢复上次对话）

    def post_init(self):
        if self.chatgpt_cd_time <= 0:
            self.chatgpt_cd_time = 0
        self.chatgpt_cd_time = datetime.timedelta(seconds=self.chatgpt_cd_time)

        if self.chatgpt_gen_args_json_file is not None:
            if os.path.exists(self.chatgpt_gen_args_json_file):
                try:
                    self.chatgpt_gen_args = load_json(self.chatgpt_gen_args_json_file)
                except:
                    logger.warning(f"从 {self.chatgpt_gen_args_json_file} 读取生成参数失败，请检查文件格式是否正确，当前使用默认生成参数。")
            else:
                logger.warning(f"生成参数文件 {self.chatgpt_gen_args_json_file} 不存在，请检查路径是否正确，当前使用默认生成参数。")
        else:
            logger.info("无生成参数文件配置，使用默认生成参数。")

        if self.chatgpt_gen_args is None:
            self.chatgpt_gen_args = {}


NONEBOT_CONFIG = get_driver().config
PLUGIN_CONFIG = get_plugin_config(ChatGPTAPIConfig)
PLUGIN_CONFIG.post_init()
logger.info(PLUGIN_CONFIG)
