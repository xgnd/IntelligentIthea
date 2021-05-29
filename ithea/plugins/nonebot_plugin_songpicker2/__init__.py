# import nonebot
from .data_source import dataGet, dataProcess
from nonebot.permission import Permission
from nonebot.adapters import Bot, Event
from nonebot.typing import T_State
from nonebot import on_startswith
from nonebot.adapters.cqhttp import MessageSegment
dataget = dataGet()

songpicker = on_startswith(
    "点歌", permission=Permission(), priority=5)


@songpicker.handle()
async def handle_first_receive(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message())[2:].strip()
    if args.isdigit():
        if "songName" in state:
            state["songNum"] = int(args)
    elif args:
        state["songName"] = args


@songpicker.got("songName", prompt="歌名是？")
async def handle_songName(bot: Bot, event: Event, state: T_State):
    songName = state["songName"]
    songIdList = await dataget.songIds(songName=songName)
    if not songIdList:
        await songpicker.reject("没有找到这首歌，请发送其它歌名！")

    print(songIdList)
    songInfoList = await dataget.songInfo(songIdList, songName)

    songInfoMessage = await dataProcess.mergeSongInfo(songInfoList)
    await songpicker.send(songInfoMessage)
    state["songIdList"] = songIdList


@songpicker.got("songNum")
async def handle_songNum(bot: Bot, event: Event, state: T_State):
    songIdList = state["songIdList"]
    songNum = state["songNum"]
    print(songNum)
    # 处理重选
    if not songNum.isdigit():
        await songpicker.finish()
    else:
        songNum = int(songNum) - 1

    if songNum >= len(songIdList) or songNum <= -1:
        await songpicker.reject("数字序号错误，请重选")
    print(songNum)
    selectedSongId = songIdList[int(songNum)]

    songContent = [
        {
            "type": "music",
            "data": {
                "type": "163",
                "id": selectedSongId
            }
        }
    ]

    # songContent = MessageSegment.music(163,int(selectedSongId))
    print(songContent)
    await songpicker.send(songContent)

    songCommentsDict = await dataget.songComments(songId=selectedSongId)
    songCommentsMessage = await dataProcess.mergeSongComments(songCommentsDict)
    commentContent = [
        {
            "type": "text",
            "data": {
                "text": "下面为您播送热评：\n"
            }
        },
        {
            "type": "text",
            "data": {
                "text": songCommentsMessage
            }
        },
        {
            "type": "text",
            "data": {
                "text": "\n【回复序号可重选】"
            }
        }
    ]

    await songpicker.send(commentContent)

    # 重选功能
    await songpicker.reject()
