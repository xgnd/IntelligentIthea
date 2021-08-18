import asyncio
import base64
from io import BytesIO

from nonebot import get_driver, on_command, on_regex, on_startswith
from nonebot.adapters import Bot, Event, Message
from nonebot.adapters.cqhttp import (GroupMessageEvent, GroupRequestEvent,
                                     MessageSegment)
from nonebot.adapters.cqhttp.permission import GROUP
from nonebot.rule import to_me
from nonebot.typing import T_State
from PIL import Image, ImageDraw, ImageFont

from .config import Config
from .data_source import *

global_config = get_driver().config
config = Config(**global_config.dict())


# ROAD = '='
# ROADLENGTH = 16
# TOTAL_NUMBER = 10
# NUMBER = 5
# ONE_TURN_TIME = 3
# SUPPORT_TIME = 30
# RUN_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
# FILE_PATH = os.path.dirname(__file__)
# # 如果此项为True，则技能由图片形式发送，减少风控。
# SKILL_IMAGE = False


running_judger = RunningJudger()

numrecord = NumRecord()


# 指定赛道的角色释放技能，输入分配好的赛道和赛道编号
def skill_unit(Race_list, rid, position, silence, pause, ub, gid):
    # 检查是否被沉默
    cid = Race_list[rid-1]
    sid = skill_select(cid)
    if ub[rid-1] != 0:
        sid = 3
        ub[rid-1] -= 1

    skill = skill_load(cid, sid)
    skillmsg = skill[0]
    skillmsg += ":"
    if silence[rid-1] == 1:
        skillmsg += "本回合被沉默"
        silence[rid-1] -= 1
        return skillmsg
    skillmsg += skill[1]
    list = Race_list
    id = rid
    position = position
    silence = silence
    pause = pause
    ub = ub
    kan_num = numrecord.get_kan_num(gid)
    kokoro_num = numrecord.get_kokoro_num(gid)
    if skill[2] == "null":
        return skillmsg
    loc = locals()
    addtion_text = ''
    exec(skill[2])
    if 'text' in loc.keys():
        addtion_text = loc['text']
    if 'kan_num1' in loc.keys():
        numrecord.add_kan_num(gid, loc['kan_num1'])
    skillmsg += addtion_text

    return skillmsg

# 每个赛道的角色轮流释放技能
def skill_race(Race_list, position, silence, pause, ub, gid):
    skillmsg = ""
    for rid in range(1, 6):
        skillmsg += skill_unit(Race_list, rid, position,
                               silence, pause, ub, gid)
        if rid != 5:
            skillmsg += "\n"
    return skillmsg

start = on_startswith("赛跑开始",permission=GROUP,priority=2, block=True)


@start.handle()
async def Racetest(bot: Bot, event: Event):
    if event.group_id != 764533822 and event.sender.role != "admin" and event.sender.role != "owner":
        await start.finish('只有群管理才能开启赛跑')
    if running_judger.get_on_off_status(event.group_id):
        await start.finish("此轮赛跑还没结束，请勿重复使用指令。")
    res,hint = check_record(event.group_id)
    if res != 200:
        await start.finish(f"距离下次比赛还有{res}分钟")
    running_judger.turn_on(event.group_id)
    running_judger.set_support(event.group_id)
    gid = event.group_id
    # 用于记录各赛道上角色位置，第i号角色记录在position[i-1]上
    position = [config.ROADLENGTH for x in range(0, config.NUMBER)]
    # 同理，记录沉默，暂停，以及必放ub标记情况
    silence = [0 for x in range(0, config.NUMBER)]
    pause = [0 for x in range(0, config.NUMBER)]
    ub = [0 for x in range(0, config.NUMBER)]
    numrecord.init_num(gid)
    Race_list = chara_select()
    msg = '墨鱼终极赛跑即将开始！\n下面为您介绍参赛选手：'
    await start.send(msg)
    await asyncio.sleep(config.ONE_TURN_TIME)
    running_judger.turn_on_support(gid)
    # 介绍选手，开始支持环节
    msg = introduce_race(Race_list)
    await start.send(msg)

    await asyncio.sleep(config.SUPPORT_TIME)
    running_judger.turn_off_support(gid)
    # 支持环节结束
    msg = '支持环节结束，下面赛跑正式开始。'
    await start.send(msg)
    await asyncio.sleep(config.ONE_TURN_TIME)
    kokoro_id = search_kokoro(Race_list)
    if kokoro_id is not None:
        kokoro_num = numrecord.set_kokoro_num(gid, kokoro_id)
        msg = f'本局存在艾陆可，艾陆可的憧憬者为{kokoro_num}号选手'
        await start.send(msg)
        await asyncio.sleep(config.ONE_TURN_TIME)

    race_init(position, silence, pause, ub)
    msg = '运动员们已经就绪！\n'
    msg += print_race(Race_list, position)
    await start.send(msg)

    gameend = 0
    i = 1
    while gameend == 0:
        await asyncio.sleep(config.ONE_TURN_TIME)
        msg = f'第{i}轮跑步:\n'
        one_turn_run(pause, position, Race_list)
        msg += print_race(Race_list, position)
        await start.send(msg)
        check = check_game(position)
        if check[0] != 0:
            break

        await asyncio.sleep(config.ONE_TURN_TIME)
        skillmsg = "技能发动阶段:\n"
        skillmsg += skill_race(Race_list, position, silence, pause, ub, gid)
        if config.SKILL_IMAGE == True:
            im = Image.new("RGB", (600, 150), (255, 255, 255))
            dr = ImageDraw.Draw(im)
            FONTS_PATH = os.path.join(config.FILE_PATH, 'fonts')
            FONTS = os.path.join(FONTS_PATH, 'msyh.ttf')
            font = ImageFont.truetype(FONTS, 14)
            dr.text((10, 5), skillmsg, font=font, fill="#000000")
            bio = BytesIO()
            im.save(bio, format='PNG')
            base64_str = 'base64://' + \
                base64.b64encode(bio.getvalue()).decode()
            mes = f"[CQ:image,file={base64_str}]"
            await start.send(mes)
        else:
            await start.send(skillmsg)

        await asyncio.sleep(config.ONE_TURN_TIME)
        msg = f'技能发动结果:\n'
        msg += print_race(Race_list, position)
        await start.send(msg)

        i += 1
        check = check_game(position)
        gameend = check[0]
    winner = check[1]
    winmsg = ""
    for id in winner:
        winmsg += str(id)
        winmsg += "\n"
    msg = f'胜利者为:\n{winmsg}'
    score_counter = ScoreCounter()
    await start.send(msg)
    gid = event.group_id
    support = running_judger.get_support(gid)
    winuid = []
    supportmsg = '比赛结算:\n'
    if support != 0:
        print(support)
        for uid in support:
            support_id = support[uid][0]
            support_score = support[uid][1]
            if support_id in winner:
                winuid.append(uid)
                winscore = support_score*2
                score_counter._add_score(gid, uid, winscore)
                supportmsg += MessageSegment.at(uid) + \
                    f'+{winscore}墨鱼币\n'
            else:
                score_counter._reduce_score(gid, uid, support_score)
                supportmsg += MessageSegment.at(uid) + \
                    f'-{support_score}墨鱼币\n'
    await start.send(supportmsg)
    running_judger.set_support(event.group_id)
    running_judger.turn_off(event.group_id)


judger = on_regex(r'^([1-5])号(\d+)(墨鱼币|分|币)$', permission=GROUP, priority=2, block=True)


@judger.handle()
async def on_input_score(bot: Bot, event: Event):
    # try:
    if running_judger.get_on_off_support_status(event.group_id):
        gid = event.group_id
        uid = event.user_id

        match = parse_cmd(r'^([1-5])号(\d+)(墨鱼币|分|币)$', event.raw_message)[0]

        select_id = int(match[0])
        input_score = int(match[1])
        print(select_id, input_score)
        score_counter = ScoreCounter()
        # 若下注该群下注字典不存在则创建
        if running_judger.get_support(gid) == 0:
            running_judger.set_support(gid)
        support = running_judger.get_support(gid)
        # 检查是否重复下注
        if uid in support:
            msg = MessageSegment.at(event.user_id) + '您已经支持过了'
            await judger.finish(msg)
        # 检查金币是否足够下注
        if score_counter._judge_score(gid, uid, input_score) == 0:
            msg = MessageSegment.at(event.user_id) + '您的墨鱼币不足'
            await judger.finish(msg)
        else:
            running_judger.add_support(gid, uid, select_id, input_score)
            msg = MessageSegment.at(event.user_id) + f'支持{select_id}号成功。'
            await judger.finish(msg)
    # except Exception as e:
        # await judger.send('错误:\n' + str(e))

async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card'] != '' else m['nickname']
    return d


reset = on_startswith("重置赛跑", permission=GROUP, priority=2, block=True)


@reset.handle()
async def init_runstatus(bot: Bot, event: Event):
    print(event.group_id,type(event.group_id))
    print(event.sender.role)
    if event.group_id != 764533822 and event.sender.role != "admin" and event.sender.role != "owner":
        await reset.finish('只有群管理才能使用重置赛跑哦')
    running_judger.turn_off(event.group_id)
    running_judger.set_support(event.group_id)
    msg = '已重置本群赛跑状态！'
    await reset.send(msg, at_sender=True)
