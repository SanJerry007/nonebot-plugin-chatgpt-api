from typing import Any, AsyncGenerator

from nonebot import Bot
from nonebot.adapters import Event
from nonebot.matcher import Matcher
from nonebot.params import Depends, _command_arg
from nonebot.plugin import on_message
from nonebot.rule import startswith, to_me
from nonebot.typing import T_State

from .chat import add_chat_timeout
from ..chatgpt_api import ChatGPT, get_chatgpt
from ..config import NONEBOT_CONFIG, PLUGIN_CONFIG
from ..data_storage import get_latest_chat_history
from ..rule import notstartswith

__all__ = ["matcher_chat_recover"]

matcher_chat_recover = on_message(
    rule=to_me() & startswith("恢复") & notstartswith(tuple(NONEBOT_CONFIG.command_start)),
    permission=None,  # GROUP
    block=False,
    priority=1,
)


def chat_recover_command_checker() -> Any:
    """
    检查是否为提示词相关的命令，要求输入内容必须以`恢复`开头，且后面无内容
    通过示例：
        @bot 恢复
    拒绝示例：
        @bot 恢复生命值需要多长时间？
    """

    async def check_command(event: Event, state: T_State, matcher: Matcher) -> AsyncGenerator[None, None]:
        # extract user input
        message = _command_arg(state) or event.get_message()
        user_content = message.extract_plain_text().strip()

        # extract mode & content
        extracted_user_content = user_content.split(" ")  # "恢复"
        if extracted_user_content[0] == "恢复":
            matcher.stop_propagation()  # verify that this is a prompt-related command, block the matcher
        else:
            await matcher.finish()  # skip this matcher if the command is not related to the prompt
        yield

    return Depends(check_command)


@matcher_chat_recover.handle(parameterless=[chat_recover_command_checker()])
async def handle_system_prompt(event: Event, matcher: Matcher, bot: Bot) -> None:
    """恢复对话相关逻辑"""
    if hasattr(event, "user_id"):
        user_id = event.get_user_id()
    else:
        user_id = "GLOBAL"

    # prepare the chatgpt
    chatgpt: ChatGPT = get_chatgpt(user_id)
    chat_history = get_latest_chat_history(user_id)

    # reset the scheduler for chat
    add_chat_timeout(user_id, event, matcher, bot, minutes=PLUGIN_CONFIG.chatgpt_timeout_time_chat, respond=PLUGIN_CONFIG.chatgpt_timeout_respond)

    if chat_history is None:
        await matcher.finish(f"无可恢复的历史对话", at_sender=True)
    else:
        chatgpt.set_chat_history(chat_history)
        last_round_content = f"[用户]\n{chat_history[-2]['content']}\n[{PLUGIN_CONFIG.chatgpt_bot_name}]\n{chat_history[-1]['content']}"
        await matcher.finish(f"对话恢复成功：\n{last_round_content}", at_sender=True)
