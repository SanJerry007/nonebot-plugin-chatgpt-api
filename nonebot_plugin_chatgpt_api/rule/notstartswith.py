import re
from typing import Union

from nonebot.adapters import Event
from nonebot.rule import Rule as Rule
from nonebot.typing import T_State


class NotstartswithRule:
    """检查消息纯文本是否 **不** 以指定字符串开头。
    由`nonebot.rule.StartswithRule`修改。

    参数:
        msg: 指定消息开头字符串元组
        ignorecase: 是否忽略大小写
    """

    __slots__ = ("ignorecase", "msg")

    def __init__(self, msg: tuple[str, ...], ignorecase: bool = False):
        self.msg = msg
        self.ignorecase = ignorecase

    def __repr__(self) -> str:
        return f"NotstartswithRule(msg={self.msg}, ignorecase={self.ignorecase})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NotstartswithRule)
            and frozenset(self.msg) == frozenset(other.msg)
            and self.ignorecase == other.ignorecase
        )

    def __hash__(self) -> int:
        return hash((frozenset(self.msg), self.ignorecase))

    async def __call__(self, event: Event, state: T_State) -> bool:
        try:
            text = event.get_plaintext()
        except Exception:
            return False
        if re.match(
            f"^(?:{'|'.join(re.escape(prefix) for prefix in self.msg)})",
            text,
            re.IGNORECASE if self.ignorecase else 0,
        ):
            return False
        return True


def notstartswith(msg: Union[str, tuple[str, ...]], ignorecase: bool = False) -> Rule:
    """匹配消息纯文本开头。
    由`nonebot.rule.startswith`修改。

    参数:
        msg: 指定消息开头字符串元组
        ignorecase: 是否忽略大小写
    """
    if isinstance(msg, str):
        msg = (msg,)

    return Rule(NotstartswithRule(msg, ignorecase))
