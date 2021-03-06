import random
import asyncio
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot import get_driver, message, on_message
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment

from .config import Config
from .data_source import *

global_config = get_driver().config
config = Config(**global_config.dict())


game = on_message(permission=GROUP,block=False, priority=3)


@game.handle()
async def handle_first_receive(bot: Bot, event: Event):
    message = str(event.message)
    if message == "1A2B" or message == "1a2b":
        await game.finish("ð¥âââ1A2Bâââð¥\nåéã1A2Bè§åãéè¯»æ¸¸æè§å\nåéã1A2Bå¼å§ãå¼å§æ¸¸æ\nåéã1A2Bç»æãç»ææ¸¸æ")
    if message == "1A2Bè§å" or message == "1a2bè§å":
        await game.finish("ð¥âââè§åâââð¥\næ¸¸æå¼å§æ¶ä¼éæºçæä¸ä¸ªåä½æ°ï¼åä½æ°å­ä¸º0~9ï¼ä¸éå¤ï¼å¯è½æ¯0å¼å¤´ï¼\næ¨å¯ä»¥å°æ¨çæµçåä½æ°ååº\nçæµçç»æå°ä¼ä»¥AåBæ¥è¡¨ç¤º\nAä»£è¡¨çæµçæ°å­ä¸­ï¼æ°å­ç¸åä¸ä½ç½®ä¹æ­£ç¡®çä¸ªæ°\nBä»£è¡¨çæµçæ°å­ä¸­ï¼æ°å­ç¸åä½ä½ç½®ä¸ä¸æ ·çä¸ªæ°\nä¸¾ä¾æ¥è¯´ï¼å¦æçæçæ°å­ä¸º1234ï¼ä¸ä½ ççæ°å­ä¸º5283ï¼å¶ä¸­2è¢«çå°ä¸ä½ç½®æ­£ç¡®ï¼3ä¹è¢«çå°ä½ä½ç½®ä¸å¯¹ï¼æä»¥ç»æä¼åºç°1A1B\nå½åºç°4A0Bæ¶ï¼å³ä¸ºçä¸­")

    gid = str(event.group_id)
    uid = str(event.user_id)
    handle = GlobalHandle(gid, uid)
    if message == "1A2Bå¼å§" or message == "1a2bå¼å§":
        if handle.get_score()["coin"] < 5:
            await game.finish(MessageSegment.at(uid)+"å¢¨é±¼å¸ä¸å¤ç¨å¦ï¼")
        result = start(gid, uid)
        if result:
            await game.finish(MessageSegment.at(uid)+"å·²éæºçæäºä¸ä¸ªåä½æ°ï¼è¯·ç´æ¥ååºæ¨çæµçæ°")
        else:
            await game.finish(MessageSegment.at(uid)+"å½åæ¸¸æå°æªç»æ~")
    if message == "1A2Bç»æ" or message == "1a2bç»æ":
        result = end(gid,uid)
        if result:
            await game.finish(MessageSegment.at(uid)+"æ¸¸æå·²ç»æï¼\næ¨ä¼¼ä¹å15ä¸ªå¢¨é±¼å¸æ¦è©èè¿å¯~")
        else:
            await game.finish(MessageSegment.at(uid)+"å½åå¹¶æ²¡ææ­£å¨è¿è¡çæ¸¸æ")
    if message.isdigit() and len(message) == 4:
        for i in message:
            a = message.count(i, 0, len(message))
            if a>1:
                await game.finish("ç­æ¡ä¸å¾åºç°éå¤çæ°å­å~")
        result,round_times = guess(gid, uid, message)
        if result != 0:
            await game.send(MessageSegment.at(uid)+f"ç¬¬{round_times}è½®çæµç»æï¼" + result)
            if result == "4A0B" and round_times <= 10:
                # handle.add_score(0,0,15)
                await asyncio.sleep(1)
                msg = MessageSegment.at(uid)+"æ­åæ¨å¨10è½®åå®æäº1A2Bï¼"
                # å¯è½ä¼è·ä¸å¼ å¾
                if random.choices([True, False], [0.7, 0.3])[0]:
                    await game.finish(msg)
                else:
                    await game.send(msg)
                    await asyncio.sleep(random.randint(1, 4))
                    msg = await get_sticker(2)
                    await game.finish(msg)
            elif result == "4A0B" and round_times > 10:
                await asyncio.sleep(1)
                msg = MessageSegment.at(uid)+"æ­åæ¨å®æäº1A2Bï¼ä½æ²¡è½å¨10è½®åå®æï¼çéæ¾~\nä»ä¹é½è«å¾"+MessageSegment.face(174)
                if random.choices([True, False], [0.7, 0.3])[0]:
                    await game.finish(msg)
                else:
                    await game.send(msg)
                    await asyncio.sleep(random.randint(1, 4))
                    msg = await get_sticker(2)
                    await game.finish(msg)
