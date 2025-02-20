from typing import Any, Callable, Iterable, Optional, Union

from nonebot.adapters import Event
from nonebot.consts import ARG_KEY
from nonebot.dependencies import Dependent
from nonebot.internal.adapter import (
    Message,
    MessageSegment,
    MessageTemplate,
)
from nonebot.internal.matcher import Matcher
from nonebot.internal.params import Depends
from nonebot.typing import T_Handler


def enhanced_got(
    cls,
    key: str,
    prompt: Optional[Union[str, Message, MessageSegment, MessageTemplate]] = None,
    parameterless: Optional[Iterable[Any]] = None,
    **kwargs,
) -> Callable[[T_Handler], T_Handler]:
    """
    由`nonebot.internal.matcher.Matcher.got()`修改，添加了reject的发送的kwargs。

    当要获取的 `key` 不存在时接收用户新的一条消息再运行该函数，
    如果 `key` 已存在则直接继续运行

    参数:
        key: 参数名
        prompt: 在参数不存在时向用户发送的消息
        parameterless: 非参数类型依赖列表
    """

    async def _key_getter(event: Event, matcher: "Matcher"):
        matcher.set_target(ARG_KEY.format(key=key))
        if matcher.get_target() == ARG_KEY.format(key=key):
            matcher.set_arg(key, event.get_message())
            return
        if matcher.get_arg(key, ...) is not ...:
            return
        await matcher.reject(prompt, **kwargs)

    _parameterless = (Depends(_key_getter), *(parameterless or ()))

    def _decorator(func: T_Handler) -> T_Handler:
        if cls.handlers and cls.handlers[-1].call is func:
            func_handler = cls.handlers[-1]
            new_handler = Dependent(
                call=func_handler.call,
                params=func_handler.params,
                parameterless=Dependent.parse_parameterless(
                    tuple(_parameterless), cls.HANDLER_PARAM_TYPES
                ) + func_handler.parameterless,
            )
            cls.handlers[-1] = new_handler
        else:
            cls.append_handler(func, parameterless=_parameterless)

        return func

    return _decorator


setattr(Matcher, "enhanced_got", classmethod(enhanced_got))
