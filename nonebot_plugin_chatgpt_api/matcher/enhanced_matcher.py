from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Optional, Union

from nonebot.adapters import Event, Message, MessageSegment, MessageTemplate
from nonebot.consts import ARG_KEY
from nonebot.dependencies import Dependent
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.permission import Permission
from nonebot.plugin.on import get_matcher_source, store_matcher
from nonebot.rule import Rule
from nonebot.typing import T_Handler, T_PermissionChecker, T_RuleChecker, T_State


class EnhancedMatcher(Matcher):
    @classmethod
    def got(
        cls,
        key: str,
        prompt: Optional[Union[str, Message, MessageSegment, MessageTemplate]] = None,
        parameterless: Optional[Iterable[Any]] = None,
        **kwargs,
    ) -> Callable[[T_Handler], T_Handler]:
        """
        添加了reject的发送的kwargs的got
        当要获取的 `key` 不存在时接收用户新的一条消息再运行该函数，
        如果 `key` 已存在则直接继续运行

        参数:
            key: 参数名
            prompt: 在参数不存在时向用户发送的消息
            parameterless: 非参数类型依赖列表
        """

        async def _key_getter(event: Event, matcher: "EnhancedMatcher"):
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


def enhanced_on(
    type: str = "",
    rule: Optional[Union[Rule, T_RuleChecker]] = None,
    permission: Optional[Union[Permission, T_PermissionChecker]] = None,
    *,
    handlers: Optional[list[Union[T_Handler, Dependent[Any]]]] = None,
    temp: bool = False,
    expire_time: Optional[Union[datetime, timedelta]] = None,
    priority: int = 1,
    block: bool = False,
    state: Optional[T_State] = None,
    _depth: int = 0,
) -> type[EnhancedMatcher]:
    """注册一个基础事件响应器，可自定义类型。

    参数:
        type: 事件响应器类型
        rule: 事件响应规则
        permission: 事件响应权限
        handlers: 事件处理函数列表
        temp: 是否为临时事件响应器（仅执行一次）
        expire_time: 事件响应器最终有效时间点，过时即被删除
        priority: 事件响应器优先级
        block: 是否阻止事件向更低优先级传递
        state: 默认 state
    """
    matcher = EnhancedMatcher.new(
        type,
        Rule() & rule,
        Permission() | permission,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        block=block,
        handlers=handlers,
        source=get_matcher_source(_depth + 1),
        default_state=state,
    )
    store_matcher(matcher)
    return matcher


def enhanced_on_message(*args, _depth: int = 0, **kwargs) -> type[EnhancedMatcher]:
    """注册一个消息事件响应器。

    参数:
        rule: 事件响应规则
        permission: 事件响应权限
        handlers: 事件处理函数列表
        temp: 是否为临时事件响应器（仅执行一次）
        expire_time: 事件响应器最终有效时间点，过时即被删除
        priority: 事件响应器优先级
        block: 是否阻止事件向更低优先级传递
        state: 默认 state
    """
    kwargs.setdefault("block", True)
    return enhanced_on("message", *args, **kwargs, _depth=_depth + 1)
