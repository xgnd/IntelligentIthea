import asyncio
import os
import random

from nonebot import get_driver, message, on_message, on_regex, on_startswith
from nonebot.adapters.cqhttp import Bot, Event, MessageSegment
from nonebot.adapters.cqhttp.permission import GROUP

from .config import Config
from .data_source import *

global_config = get_driver().config
config = Config(**global_config.dict())


gobang_start_h = on_startswith("五子棋", permission=GROUP, priority=2, block=True)


@gobang_start_h.handle()
async def gobang_start_handle(bot: Bot, event: Event, state: dict):
    msg = str(event.message)
    if msg == "五子棋":

        msg = "◇━五子棋━◇\n⭐️五子棋开始\n⭐五子棋加入\n◇━结束对局━◇\n⭐认输"
        await gobang.finish(msg)


gobang = on_regex(r"^[a-oA-O][0-9]{1,2}",
                  permission=GROUP, priority=2, block=True)


@gobang.handle()
async def gobang_handle(bot: Bot, event: Event, state: dict):
    msg = str(event.message)
    flag = match(event.group_id, event.user_id)
    if flag != 0:
        if flag.index(str(event.user_id))+1 == flag[2]:
            pos = parse_cmd(r"^[a-oA-O][0-9]{1,2}", str(event.message))[0]

            if int(pos[1:]) > 0 and int(pos[1:]) <= 15:
                if pos[0] >= 'A' and pos[0] <= 'O':
                    col = ord(pos[0]) - 65
                elif pos[0] >= 'a' and pos[0] <= 'o':
                    col = ord(pos[0]) - 97
                row = int(pos[1:]) - 1
                flag = gobang_canmove(flag, col, row)
                if flag:
                    image = gobang_draw(
                        flag, col, row, event.group_id, event.user_id)
                    flag = gobang_move(flag, col, row)
                    print(flag[2], pos[0]+str(row+1), col, row)
                    await gobang.send(image)
                    await asyncio.sleep(1)
                    gobang_save(flag, event.group_id, event.user_id)
                    r = is_win(flag[3])
                    if r == 3:
                        msg = MessageSegment.at(
                            flag[flag[2]-1])+"对方下了{}，现在到你下棋咯~".format(pos[0]+str(row+1))
                        await gobang.finish(msg)
                    else:
                        msg = "恭喜"+MessageSegment.at(flag[r])+"赢得了比赛！"
                        gobang_end(flag, event.group_id, event.user_id)
                        await gobang.finish(msg)
                else:
                    msg = MessageSegment.at(event.user_id)+"这个位置已经有棋啦！请换个位置吧"
                    await gobang.finish(msg)
            else:
                msg = MessageSegment.at(event.user_id)+"落子位置超出棋盘范围啦！请重新落子"
                await gobang.finish(msg)
        else:
            msg = MessageSegment.at(event.user_id)+"还没到你落子哟~"
            await gobang.finish(msg)


gobang_start_h = on_startswith(
    "五子棋开始", permission=GROUP, priority=2, block=True)


@gobang_start_h.handle()
async def gobang_start_handle(bot: Bot, event: Event, state: dict):
    msg = str(event.message)
    if msg == "五子棋开始":
        flag = gobang_start(event.group_id, event.user_id)
        if flag:
            msg = MessageSegment.at(event.user_id) + \
                "已创建棋局（持续60s），人数(1/2)\n等待其他玩家加入..."
            await gobang_start_h.send(msg)
            await asyncio.sleep(60)
            if not is_ready(event.group_id, event.user_id):
                msg = MessageSegment.at(event.user_id)+"未够人数，房间已关闭！"
                await gobang_start_h.send(msg)
        else:
            msg = MessageSegment.at(event.user_id)+"正在棋局中，无法开始其它棋局"
            await gobang_start_h.finish(msg)


gobang_join_h = on_startswith(
    "五子棋加入", permission=GROUP, priority=2, block=True)


@gobang_join_h.handle()
async def gobang_start_handle(bot: Bot, event: Event, state: dict):
    msg = str(event.message)
    if msg == "五子棋加入":
        flag = gobang_join(event.group_id, event.user_id)
        if flag == 0:
            msg = "无棋局可加入"
            await gobang_join_h.finish(msg)
        elif flag == 1:
            msg = "正在棋局中，无法加入其它棋局"
            await gobang_join_h.finish(msg)
        else:
            msg = MessageSegment.at(event.user_id) + \
                "已加入"+MessageSegment.at(flag)+"的房间"
            await gobang_join_h.send(msg)
            msg = "请输入“字母+数字”来表示落子位置"
            await gobang_join_h.send(msg)
            background_path = os.path.join(os.path.dirname(
                os.path.abspath(__file__)), "background.png")
            await gobang_join_h.finish(MessageSegment.image(file="file:///"+background_path))


gobang_start_h = on_startswith("认输", permission=GROUP, priority=2, block=True)


@gobang_start_h.handle()
async def gobang_start_handle(bot: Bot, event: Event, state: dict):
    msg = str(event.message)
    if msg == "认输":
        flag = match(event.group_id, event.user_id)
        if flag != 0:
            if flag[0] == "" or flag[1] == "":
                return
            if str(event.user_id) == flag[0]:
                r = 1
            else:
                r = 0
            msg = "恭喜"+MessageSegment.at(flag[r])+"赢得了比赛！"
            gobang_end(flag, event.group_id, event.user_id)
            await gobang.finish(msg)
