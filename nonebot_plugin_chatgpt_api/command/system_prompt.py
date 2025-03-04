from typing import Any, AsyncGenerator

from nonebot import Bot
from nonebot.adapters import Event
from nonebot.log import logger
from nonebot.params import ArgPlainText, Depends, _command_arg
from nonebot.rule import startswith, to_me
from nonebot.typing import T_State
from nonebot_plugin_apscheduler import scheduler

from ..chatgpt_api import ChatGPT, get_chatgpt
from ..config import NONEBOT_CONFIG, PLUGIN_CONFIG
from ..data_storage import get_latest_system_prompt, save_system_prompt_to_csv
from ..matcher import enhanced_on_message, EnhancedMatcher
from ..rule import notstartswith
from ..scheduled_jobs import add_to_timeout_job_storage, remove_from_timeout_job_storage

__all__ = ["matcher_system_prompt"]

matcher_system_prompt = enhanced_on_message(
    rule=to_me() & startswith("提示词") & notstartswith(tuple(NONEBOT_CONFIG.command_start)),
    permission=None,  # GROUP
    block=False,
    priority=1,
)


def add_system_prompt_timeout(user_id, bot, event, matcher, minutes=5, respond=True):
    """为`提示词设置`命令添加超时"""
    if minutes > 0:
        job_id = user_id + "-system_prompt"
        add_to_timeout_job_storage(user_id, job_id)  # 记录此任务到超时任务列表
        scheduler.add_job(
            finish_system_prompt_timeout,
            trigger='interval',
            args=[user_id],
            kwargs={
                "event": event,
                "matcher": matcher,
                "bot": bot,
                "respond": respond,
            },
            id=job_id,
            minutes=minutes,
            replace_existing=True,
        )


def remove_system_prompt_timeout(user_id):
    """移除`提示词设置`命令的超时"""
    job_id = user_id + "-system_prompt"
    remove_from_timeout_job_storage(user_id, job_id)  # 移除此超时任务


async def finish_system_prompt_timeout(user_id, event, matcher, bot, respond=True):
    """`提示词设置`命令超时后的处理函数"""
    await matcher.finish()
    remove_system_prompt_timeout(user_id)
    if respond:
        response_content = f"超过{PLUGIN_CONFIG.chatgpt_timeout_time_setting}分钟，已自动退出提示词设置！"
        await bot.send(event, response_content, at_sender=True)


def system_prompt_command_checker() -> Any:
    """
    检查是否为提示词相关的命令，要求输入内容必须以`提示词`开头，且后面有空格或无内容
    通过示例：
        @bot 提示词
        @bot 提示词 查看
        @bot 提示词 更新 你是一只猫娘！
    拒绝示例：
        @bot 提示词是什么？请给我一个例子。
    """

    async def check_command(event: Event, state: T_State, matcher: EnhancedMatcher) -> AsyncGenerator[None, None]:
        # extract user input
        message = _command_arg(state) or event.get_message()
        user_content = message.extract_plain_text().strip()

        # extract mode & content
        extracted_user_content = user_content.split(" ")  # "提示词" [命令] [内容]
        if extracted_user_content[0] == "提示词":
            matcher.stop_propagation()  # verify that this is a prompt-related command, block the matcher
        else:
            await matcher.finish()  # skip this matcher if the command is not related to the prompt
        yield

    return Depends(check_command)


@matcher_system_prompt.handle(parameterless=[system_prompt_command_checker()])
async def handle_system_prompt(event: Event, state: T_State, matcher: EnhancedMatcher, bot: Bot) -> None:
    """系统提示词相关逻辑"""
    if hasattr(event, "user_id"):
        user_id = event.get_user_id()
    else:
        user_id = "GLOBAL"

    # extract raw input
    message = _command_arg(state) or event.get_message()
    message_type = type(message)
    user_content = message.extract_plain_text().strip()
    logger.info(f"User \"{user_id}\": {user_content}")
    logger.debug(f"Message type: {type(message)}")

    # extract `mode` & `content`
    extracted_user_content = user_content.split(" ")  # "提示词" [命令] [内容]
    if extracted_user_content[0] == "提示词":
        extracted_user_content = extracted_user_content[1:]  # [命令] [内容]
    mode = extracted_user_content[0] if len(extracted_user_content) > 0 else None  # [命令] / None

    # set a scheduler that ends the setting when timeout
    add_system_prompt_timeout(user_id, bot, event, matcher, minutes=PLUGIN_CONFIG.chatgpt_timeout_time_setting, respond=PLUGIN_CONFIG.chatgpt_timeout_respond)

    # handle the command
    if mode is None:
        # "提示词"
        # get the `mode` variable from `matcher.got()` function
        pass
    else:
        # set the `mode` for function `dispatch_system_prompt_operations`
        if mode == "查看":
            # "提示词" "查看"
            matcher.set_arg("mode", message_type("查看"))
            matcher.set_arg("content", None)
        elif mode == "重置":
            # "提示词" "重置"
            matcher.set_arg("mode", message_type("重置"))
            matcher.set_arg("content", None)
        elif mode == "更新":
            # "提示词" "更新" [内容]
            matcher.set_arg("mode", message_type("更新"))
            # set the `content` for function `update_system_prompt`
            if len(extracted_user_content) > 1:
                matcher.set_arg("content", message_type(" ".join(extracted_user_content[1:])))
        else:
            # matcher.set_arg("content", None)
            await matcher.reject(f"\"{mode}\"命令无效，请重新输入！\n1.查看\n2.重置\n3.更新\n输入\"退出\"离开提示词设置。", at_sender=True)


@matcher_system_prompt.got(
    "mode",
    prompt=f"请选择操作：\n1.查看\n2.重置\n3.更新\n输入\"退出\"离开提示词设置。",
    at_sender=True,
)
async def dispatch_system_prompt_operations(event: Event, matcher: EnhancedMatcher, bot: Bot, mode: str = ArgPlainText()):
    """
    选择具体的提示词指令，由`@bot 提示词`命令触发。
    """
    if hasattr(event, "user_id"):
        user_id = event.get_user_id()
    else:
        user_id = "GLOBAL"

    # extract raw input
    mode = mode.strip()
    logger.info(f"User \"{user_id}\" raw `mode`: {mode}")

    # extract `mode`
    extracted_mode = mode.split(" ")  # ["提示词"] 命令
    if extracted_mode[0] == "提示词":
        extracted_mode = extracted_mode[1:]  # 命令
    mode = extracted_mode[0] if len(extracted_mode) > 0 else None  # [命令] / None
    logger.debug(f"User \"{user_id}\" extracted `mode`: {mode}")

    # handle the command
    if mode is None:
        # "提示词"
        # get the `mode` variable from `matcher.got()` function
        add_system_prompt_timeout(user_id, bot, event, matcher, minutes=PLUGIN_CONFIG.chatgpt_timeout_time_setting, respond=PLUGIN_CONFIG.chatgpt_timeout_respond)  # reset the scheduler
        await matcher.reject(f"请选择操作：\n1.查看\n2.重置\n3.更新\n输入\"退出\"离开提示词设置。", at_sender=True)
    else:
        if mode == "查看":
            remove_system_prompt_timeout(user_id)
            system_prompt = get_latest_system_prompt(user_id)
            if system_prompt == "":
                await matcher.finish("你还没有设置提示词哦！", at_sender=True)
            else:
                await matcher.finish(f"当前提示词：\n\"{system_prompt}\"", at_sender=True)
        elif mode == "重置":
            remove_system_prompt_timeout(user_id)
            chatgpt: ChatGPT = get_chatgpt(user_id)
            chatgpt.set_system_prompt(system_prompt="", reset_history=True)
            if PLUGIN_CONFIG.chatgpt_log_system_prompt:
                save_system_prompt_to_csv(user_id, "")
            await matcher.finish("提示词已重置！", at_sender=True)
        elif mode == "更新":
            # handle by the `update_system_prompt` function
            add_system_prompt_timeout(user_id, bot, event, matcher, minutes=PLUGIN_CONFIG.chatgpt_timeout_time_setting, respond=PLUGIN_CONFIG.chatgpt_timeout_respond)  # reset the scheduler
        elif mode == "退出":
            remove_system_prompt_timeout(user_id)
            await matcher.finish("已退出提示词设置！", at_sender=True)
        else:
            add_system_prompt_timeout(user_id, bot, event, matcher, minutes=PLUGIN_CONFIG.chatgpt_timeout_time_setting, respond=PLUGIN_CONFIG.chatgpt_timeout_respond)  # reset the scheduler
            await matcher.reject(f"\"{mode}\"为无效命令，请重新输入！\n1.查看\n2.重置\n3.更新\n输入\"退出\"离开提示词设置。", at_sender=True)


@matcher_system_prompt.got(
    "content",
    prompt=f"请输入更新后的提示词，或输入\"退出\"离开提示词设置！",
    at_sender=True,
)
async def update_system_prompt(event: Event, matcher: EnhancedMatcher, content: str = ArgPlainText()):
    """
    更新提示词内容，由`@bot 提示词 更新`命令触发。
    """
    if content is None:
        return

    if hasattr(event, "user_id"):
        user_id = event.get_user_id()
    else:
        user_id = "GLOBAL"

    # extract raw input
    content = content.strip()
    logger.info(f"User \"{user_id}\" raw `content`: {content}")

    # # extract `content`
    # extracted_content = content.split(" ")  # ["提示词"] ["更新"] 内容
    # if extracted_content[0] == "提示词":
    #     extracted_content = extracted_content[1:]  # ["更新"] 内容
    # if extracted_content[0] == "更新":
    #     extracted_content = extracted_content[1:]  # 内容
    # if len(extracted_content) > 0:
    #     matcher.reject(f"请输入更新后的提示词，或输入\"退出\"离开提示词设置！", at_sender=True)
    # else:
    #     content = extracted_content[0]
    # logger.debug(f"User \"{user_id}\" extracted `content`: {content}")

    # remove the timeout scheduler
    remove_system_prompt_timeout(user_id)

    # handle the command
    if content == "退出":
        await matcher.finish("已退出提示词设置！", at_sender=True)
    else:
        chatgpt: ChatGPT = get_chatgpt(user_id)
        chatgpt.set_system_prompt(system_prompt=content, reset_history=True)
        if PLUGIN_CONFIG.chatgpt_log_system_prompt:
            save_system_prompt_to_csv(user_id, content)
        await matcher.finish(f"提示词设置完成！", at_sender=True)
