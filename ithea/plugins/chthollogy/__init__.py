from nonebot import on_startswith
from nonebot.adapters import Bot, Event, Message
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.permission import GROUP
import random
from .data_source import *


chthollogy_menu = on_startswith("走进珂学", permission=GROUP, priority=2, block=True)


@chthollogy_menu.handle()
async def menu(bot: Bot, event: Event):
    if str(event.get_message()) == "走进珂学":
        msg = "可使用'珂学'随机返图或一句经典台词或一条终末的科普\n可使用'珂图 n'来获得n张图片，n可为空\n可使用'珂言'来获得一句经典台词\n可使用'珂普'来获得一条终末的科普\n使用'查看图片 k'查看编号为k的图片\n使用'图库状态'查看图库状态\n提示：使用以上指令获取的图片是缩略图哦\n如要获取高清版，请访问https://img.sukasuka.cn/post/图片id"
        await chthollogy_menu.finish(msg)



chthollogy_menu = on_startswith("珂学", permission=GROUP, priority=2, block=True)


@chthollogy_menu.handle()
async def menu(bot: Bot, event: Event):
    if str(event.get_message()) == "珂学":
        t = random.choice([1,2,3])
        if t==1:
            await chthollogy_menu.send('提示：以下是缩略图，如需高清大图，请访问https://img.sukasuka.cn')
            content=await get_random_pic()
            if not content == "error":
                cont = MessageSegment.image(file='https://img.sukasuka.cn/'+content['thumbnailUrl']) +'\n'+'图片id: '+str(content['id'])
            else:
                cont = '发生了未知错误，请再试一次＞﹏＜'
            await chthollogy_menu.send(cont)
            # if content['tags'] == []:
            #     await chthollogy_menu.send('这张图还没有标签呢＞﹏＜')
            # else:
            #     tag_cont = '图片'+str(content['id'])+'的标签:\n'
            #     for tag in content['tags']:
            #         for subname in tag['names']:
            #             if not str(subname).find('(kantai_collection)') == -1:
            #                 break
            #             tag_cont += str(subname) + ','
            #             break
            #     await chthollogy_menu.send(tag_cont[:-1])
        elif t==2:
            msg = await get_dialogue()
            await dialogue.finish(msg)
        else:
            msg = await get_kepu()
            await kepu.finish(msg)


chthollogy_pic = on_startswith("珂图", permission=GROUP, priority=2, block=True)


@chthollogy_pic.handle()
async def getpic(bot: Bot, event: Event):
    arg = str(event.get_message()).strip()
    arg = arg[2:].strip().lower()
    num = 1
    if not arg == '':
        num = int(arg)
    if num > 0:
        if num <=5:
            await chthollogy_pic.send('提示：以下是缩略图，如需高清大图，请访问https://img.sukasuka.cn')
            for i in range(0,num):
                content=await get_random_pic()
                if not content == "error":
                    cont = MessageSegment.image(file='https://img.sukasuka.cn/'+content['thumbnailUrl'])+'\n'+'图片id: '+str(content['id'])
                else:
                    cont = '发生了未知错误，请再试一次＞﹏＜'
                await chthollogy_pic.send(cont)
                # if content['tags'] == []:
                #     await chthollogy_pic.send('这张图还没有标签呢＞﹏＜')
                # else:
                #     tag_cont = '图片'+str(content['id'])+'的标签:\n'
                #     for tag in content['tags']:
                #         for subname in tag['names']:
                #             if not str(subname).find('(kantai_collection)') == -1:
                #                 break
                #             tag_cont += str(subname) + ','
                #             break
                #     await chthollogy_pic.send(tag_cont[:-1])
        else:
            await chthollogy_pic.send('不要一下子吸这么多珂毒嘛(* ￣︿￣)')
    else:
        await chthollogy_pic.send('无效的参数呢')
    

dialogue = on_startswith("珂言", permission=GROUP, priority=2, block=True)


@dialogue.handle()
async def dialogue_hander(bot: Bot, event: Event):
    if str(event.get_message()) == "珂言":
        msg = await get_dialogue()
        await dialogue.finish(msg)


kepu = on_startswith("珂普", permission=GROUP, priority=2, block=True)


@kepu.handle()
async def kepu_hander(bot: Bot, event: Event):
    if str(event.get_message()) == "珂普":
        msg = await get_kepu()
        await kepu.finish(msg)


lib_stat = on_startswith("图库状态", permission=GROUP, priority=2, block=True)


@lib_stat.handle()
async def lib_stat_handle(bot: Bot, event: Event):
    if str(event.get_message()) == "图库状态":
        content=await get_lib_status()
        storage = float(content['diskUsage']/(1024*1024*1024))
        stat = '中珂院の图库\n图片计数: '+str(content['postCount'])+'\n总计大小: '+str(round(storage,3))+' GB\nhttps://img.sukasuka.cn'
        await lib_stat.finish(stat)

img_view = on_startswith("查看图片", permission=GROUP, priority=2, block=True)


@img_view.handle()
async def img_view_handle(bot: Bot, event: Event):
    arg = str(event.get_message()).strip()
    arg = arg[4:].strip().lower()
    if not arg:
        await img_view.finish('请输入图片id并重试＞﹏＜')
    content=await get_pic_by_id(arg)
    if content == "-1":
        await img_view.finish('发生了错误＞﹏＜，此id不存在或图库离线')
    cont = MessageSegment.image(file='https://img.sukasuka.cn/'+content['thumbnailUrl'])+'\n'+'图片id: '+str(content['id'])
    await img_view.send(cont)
    if content['tags'] == []:
        await img_view.send('这张图还没有标签呢＞﹏＜')
    else:
        tag_cont = '标签:'
        for tag in content['tags']:
            for subname in tag['names']:
                if not str(subname).find('(kantai_collection)') == -1:
                    break
                tag_cont += str(subname) + ','
                break
        await img_view.send(tag_cont[:-1])

