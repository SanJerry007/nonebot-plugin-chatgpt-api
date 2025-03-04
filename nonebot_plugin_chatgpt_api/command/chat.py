import datetime
from collections.abc import Hashable
from typing import Any, AsyncGenerator, Dict

from nonebot import Bot
from nonebot.adapters import Event, MessageSegment
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, _command_arg
from nonebot.plugin import on_message
from nonebot.rule import to_me
from nonebot.typing import T_State
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_htmlrender import md_to_pic

from ..chatgpt_api import ChatGPT, get_chatgpt
from ..config import NONEBOT_CONFIG, PLUGIN_CONFIG
from ..data_storage import save_api_call_stat_to_jsonl, save_chat_history_to_jsonl
from ..rule import notstartswith
from ..scheduled_jobs import add_to_timeout_job_storage, remove_from_timeout_job_storage

__all__ = ["matcher_chat"]

matcher_chat = on_message(
    rule=to_me() & notstartswith(tuple(NONEBOT_CONFIG.command_start)),
    permission=None,  # GROUP
    block=True,
    priority=1000,
)


def add_chat_timeout(user_id, event, matcher, bot, minutes=10, respond=True):
    """为`对话`命令添加超时"""
    if minutes > 0:
        job_id = user_id + "-chat"
        # remove_all_timeout_jobs(user_id)  # 移除此用户的其他超时任务，避免冲突
        add_to_timeout_job_storage(user_id, job_id)  # 记录此任务到超时任务列表
        scheduler.add_job(
            finish_chat_timeout,
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


def remove_chat_timeout(user_id):
    """移除`对话`命令的超时"""
    job_id = user_id + "-chat"
    remove_from_timeout_job_storage(user_id, job_id)  # 移除此超时任务


async def finish_chat_timeout(user_id, event, matcher, bot, respond=True):
    """`对话`命令超时后的处理函数"""
    chatgpt: ChatGPT = get_chatgpt(user_id)
    chatgpt.reset_chat_history()
    matcher.finish()
    remove_chat_timeout(user_id)
    if respond:
        response_content = (f"距离上轮对话已超过{PLUGIN_CONFIG.chatgpt_timeout_time_chat}分钟，{PLUGIN_CONFIG.chatgpt_bot_name}自动结束啦！\n"
                            f"如需恢复对话，请使用指令\"@bot 恢复\"。")
        await bot.send(event, response_content, at_sender=True)


LAST_TIME: Dict[Hashable, datetime.datetime] = {}  # 用户上次对话的发送时间


def cooldown_checker(cd_time: datetime.timedelta) -> Any:
    """检查对话是否已经冷却"""

    async def check_cooldown(event: Event, matcher: Matcher) -> AsyncGenerator[None, None]:
        if hasattr(event, "user_id"):
            user_id = event.get_user_id()
        else:
            user_id = "GLOBAL"

        if user_id not in LAST_TIME:
            LAST_TIME[user_id] = datetime.datetime.now()
            logger.debug(f"[Cooldown] User \"{user_id}\" (Newly created): last_time={LAST_TIME[user_id]}")
        else:
            if isinstance(event.time, datetime.datetime):  # Console Adapter
                event_time = event.time
            elif isinstance(event.time, int):  # OneBot Adapter
                event_time = datetime.datetime.fromtimestamp(event.time)
            else:
                event_time = None
                logger.debug(f"[Cooldown] Unknown event time type: {type(event.time)}, skip cooldown check.")

            if event_time is not None:
                cooldown_time = LAST_TIME[user_id] + cd_time
                logger.debug(f"[Cooldown] User \"{user_id}\": last_time={LAST_TIME[user_id]}, event_time={event_time}, cooldown_time={cooldown_time}, cd_time={cd_time}")

                if event_time < cooldown_time:
                    await matcher.finish(f"{PLUGIN_CONFIG.chatgpt_bot_name}冷却中，剩余{(cooldown_time - event_time).total_seconds():.0f}秒", at_sender=True)
                else:
                    LAST_TIME[user_id] = event_time
        yield

    return Depends(check_cooldown)


LAST_RESPONDED: Dict[Hashable, bool] = {}  # 用户的上次对话是否已回复


def last_chat_finish_checker() -> Any:
    """检查上轮对话是否已经回复"""

    async def check_responded(event: Event, matcher: Matcher) -> AsyncGenerator[None, None]:
        if hasattr(event, "user_id"):
            user_id = event.get_user_id()
        else:
            user_id = "GLOBAL"

        if user_id in LAST_RESPONDED and not LAST_RESPONDED[user_id]:
            await matcher.finish(f"请等待上轮对话回复！", at_sender=True)
        yield

    return Depends(check_responded)


@matcher_chat.handle(parameterless=[cooldown_checker(PLUGIN_CONFIG.chatgpt_cd_time), last_chat_finish_checker()])
async def handle_chat(event: Event, state: T_State, matcher: Matcher, bot: Bot) -> None:  # , message: Message = CommandArg()
    """进行聊天对话"""
    if hasattr(event, "user_id"):
        user_id = event.get_user_id()
    else:
        user_id = "GLOBAL"

    # extract raw input
    message = _command_arg(state) or event.get_message()
    user_content = message.extract_plain_text().strip()
    logger.info(f"User \"{user_id}\": {user_content}")

    # prepare the chatgpt
    chatgpt: ChatGPT = get_chatgpt(user_id)

    # get response content
    LAST_RESPONDED[user_id] = False
    stat = await chatgpt.multi_round_chat(user_content, input_type="text")
    LAST_RESPONDED[user_id] = True

    total_cost = stat["cache_cost"] + stat["prompt_cost"] + stat["completion_cost"]
    response_content = stat["output"]
    logger.info(f"Response for \"{user_id}\" (${round(total_cost, 5)}): {response_content}")

    # check content validity
    if response_content is None:
        response_content = "出错啦QAQ"
    else:
        chat_history = chatgpt.chat_history[-2:]
        create_new_file = (len(chatgpt.chat_history) == 2)  # only create for new chat
        if PLUGIN_CONFIG.chatgpt_log_chat_history:
            save_chat_history_to_jsonl(user_id, chat_history, create_new_file=create_new_file)

    # log stat to file
    if PLUGIN_CONFIG.chatgpt_log_api_stats:
        save_api_call_stat_to_jsonl(user_id, stat)

    # set a scheduler that ends the chat when timeout
    if len(chatgpt.chat_history) > 0:
        add_chat_timeout(user_id, event, matcher, bot, minutes=PLUGIN_CONFIG.chatgpt_timeout_time_chat, respond=PLUGIN_CONFIG.chatgpt_timeout_respond)

    if not PLUGIN_CONFIG.chatgpt_return_image:
        await matcher_chat.finish(response_content, at_sender=True)
        # await Text(response_content).send(at_sender=True, reply=True)
    else:
        response_content = await md_to_pic(response_content, width=500)
        response_content = MessageSegment.image(response_content)
        await matcher_chat.finish(response_content, at_sender=True)
        # await Image(response_content).send(at_sender=True, reply=True)
