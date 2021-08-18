import random
import asyncio
from nonebot.adapters.cqhttp.permission import GROUP
from nonebot import get_driver, message, on_message
from nonebot.adapters.cqhttp import Bot, Event, MessageSegment

from .config import Config
from .data_source import *

global_config = get_driver().config
config = Config(**global_config.dict())


game = on_message(permission=GROUP, priority=2)


@game.handle()
async def handle_first_receive(bot: Bot, event: Event, state: dict):
    if event.group_id == 764533822:
        message = str(event.message)
        if message == "1A2B" or message == "1a2b":
            await game.finish("🔥◇━━1A2B━━◇🔥\n发送【1A2B规则】阅读游戏规则\n发送【1A2B开始】开始游戏\n发送【1A2B结束】结束游戏")
        if message == "1A2B规则" or message == "1a2b规则":
            await game.finish("🔥◇━━规则━━◇🔥\n游戏开始时会随机生成一个四位数，各位数字为0~9，不重复（可能是0开头）\n您可以将您猜测的四位数发出\n猜测的结果将会以A和B来表示\nA代表猜测的数字中，数字相同且位置也正确的个数\nB代表猜测的数字中，数字相同但位置不一样的个数\n举例来说，如果生成的数字为1234，且你猜的数字为5283，其中2被猜到且位置正确，3也被猜到但位置不对，所以结果会出现1A1B\n当出现4A0B时，即为猜中")

        gid = str(event.group_id)
        uid = str(event.user_id)
        handle = GlobalHandle(gid, uid)
        if message == "1A2B开始" or message == "1a2b开始":
            if handle.get_score()["coin"] < 5:
                await game.finish(MessageSegment.at(uid)+"墨鱼币不够用啦！")
            result = start(gid, uid)
            if result:
                await game.finish(MessageSegment.at(uid)+"已随机生成了一个四位数，请直接发出您猜测的数")
            else:
                await game.finish(MessageSegment.at(uid)+"当前游戏尚未结束~")
        if message == "1A2B结束" or message == "1a2b结束":
            result = end(gid,uid)
            if result:
                await game.finish(MessageSegment.at(uid)+"游戏已结束！\n您似乎和15个墨鱼币擦肩而过咯~")
            else:
                await game.finish(MessageSegment.at(uid)+"当前并没有正在进行的游戏")
        if message.isdigit() and len(message) == 4:
            for i in message:
                a = message.count(i, 0, len(message))
                if a>1:
                    await game.finish("答案不得出现重复的数字哟~")
            result,round_times = guess(gid, uid, message)
            if result != 0:
                await game.send(MessageSegment.at(uid)+f"第{round_times}轮猜测结果：" + result)
                if result == "4A0B" and round_times <= 10:
                    # handle.add_score(0,0,15)
                    await asyncio.sleep(1)
                    msg = MessageSegment.at(uid)+"恭喜您在10轮内完成了1A2B！"
                    # 可能会跟一张图
                    if random.choices([True, False], [0.7, 0.3])[0]:
                        await game.finish(msg)
                    else:
                        await game.send(msg)
                        await asyncio.sleep(random.randint(1, 4))
                        msg = await get_sticker(2)
                        await game.finish(msg)
                elif result == "4A0B" and round_times > 10:
                    await asyncio.sleep(1)
                    msg = MessageSegment.at(uid)+"恭喜您完成了1A2B！但没能在10轮内完成，真遗憾~\n什么都莫得"+MessageSegment.face(174)
                    if random.choices([True, False], [0.7, 0.3])[0]:
                        await game.finish(msg)
                    else:
                        await game.send(msg)
                        await asyncio.sleep(random.randint(1, 4))
                        msg = await get_sticker(2)
                        await game.finish(msg)
