from nonebot.plugin import on_command

__all__ = ["HELP_TEXT", "matcher_help"]

HELP_TEXT = f"""使用说明
/帮助：查看帮助
@bot [内容]: 进行聊天
@bot 提示词: 修改系统提示词
@bot 刷新: 开启新的对话
@bot 恢复: 恢复上次对话"""

# TODO: 注：在@bot后额外添加"公共"选项，即可 进行公共聊天/更改公共设置，如"@bot 公共 提示词 [内容]"。

matcher_help = on_command(
    cmd="help",
    rule=None,
    aliases={"帮助"},
    block=True,
    priority=0,
)


@matcher_help.handle()
async def handle_help():
    await matcher_help.finish(HELP_TEXT, at_sender=False)
    # await Text(HELP_TEXT).finish(at_sender=True)
