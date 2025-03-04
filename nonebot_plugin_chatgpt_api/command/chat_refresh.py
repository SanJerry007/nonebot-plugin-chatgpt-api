from typing import Any, AsyncGenerator

from nonebot.adapters import Event
from nonebot.matcher import Matcher
from nonebot.params import Depends, _command_arg
from nonebot.plugin import on_message
from nonebot.rule import startswith, to_me
from nonebot.typing import T_State

from .chat import remove_chat_timeout
from ..chatgpt_api import ChatGPT, get_chatgpt
from ..config import NONEBOT_CONFIG
from ..rule import notstartswith

__all__ = ["matcher_chat_refresh"]

matcher_chat_refresh = on_message(
    rule=to_me() & startswith("刷新") & notstartswith(tuple(NONEBOT_CONFIG.command_start)),
    permission=None,  # GROUP
    block=False,
    priority=1,
)


def chat_refresh_command_checker() -> Any:
    """
    检查是否为提示词相关的命令，要求输入内容必须以`刷新`开头，且后面无内容
    通过示例：
        @bot 刷新
    拒绝示例：
        @bot 刷新桌面有什么作用？
    """

    async def check_command(event: Event, state: T_State, matcher: Matcher) -> AsyncGenerator[None, None]:
        # extract user input
        message = _command_arg(state) or event.get_message()
        user_content = message.extract_plain_text().strip()

        # extract mode & content
        extracted_user_content = user_content.split(" ")  # "刷新"
        if extracted_user_content[0] == "刷新":
            matcher.stop_propagation()  # verify that this is a prompt-related command, block the matcher
        else:
            await matcher.finish()  # skip this matcher if the command is not related to the prompt
        yield

    return Depends(check_command)


@matcher_chat_refresh.handle(parameterless=[chat_refresh_command_checker()])
async def handle_system_prompt(event: Event, matcher: Matcher) -> None:
    """刷新对话相关逻辑"""
    if hasattr(event, "user_id"):
        user_id = event.get_user_id()
    else:
        user_id = "GLOBAL"

    # prepare the chatgpt
    chatgpt: ChatGPT = get_chatgpt(user_id)
    chatgpt.reset_chat_history()

    # remove the scheduler for chat
    remove_chat_timeout(user_id)

    await matcher.finish(f"对话已刷新！", at_sender=True)
