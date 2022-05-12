from typing import Dict
from collections import defaultdict
from nonebot.typing import T_State
from nonebot.rule import to_me
from nonebot.matcher import Matcher
from nonebot.adapters import Bot, Event, Message
from nonebot.permission import SUPERUSER
from nonebot import get_driver, on_command, on_notice, on_startswith, on_request, on_message
from nonebot.adapters.cqhttp import PokeNotifyEvent, MessageEvent, GroupMessageEvent, GroupIncreaseNoticeEvent, MessageSegment, GroupRequestEvent, GroupIncreaseNoticeEvent
from nonebot.adapters.cqhttp.permission import GROUP
from nonebot import require, get_bots
import random
import json
import asyncio

from .config import Config
from .data_source import *

global_config = get_driver().config
config = Config(**global_config.dict())

menu = on_startswith("菜单", permission=GROUP, priority=2, block=True)


@menu.handle()
async def menu_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "菜单":
            msg = f"""{MessageSegment.face(144)}◇━━菜单━━◇{MessageSegment.face(144)}
{MessageSegment.face(54)}抽卡（或戳一戳）
{MessageSegment.face(54)}排行榜
{MessageSegment.face(54)}合成 [角色] [角色]
{MessageSegment.face(54)}一键合成 [等级]
{MessageSegment.face(54)}超级一键合成
{MessageSegment.face(54)}查看 [角色]
{MessageSegment.face(54)}查看仓库
{MessageSegment.face(54)}卡牌列表
{MessageSegment.face(54)}编号图
{MessageSegment.face(54)}兑换 [商品]
{MessageSegment.face(54)}1A2B
{MessageSegment.face(54)}五子棋
{MessageSegment.face(54)}一言
{MessageSegment.face(54)}点歌 [歌曲名]
{MessageSegment.face(54)}走进珂学"""
            await menu.finish(msg)


draw = on_startswith("抽卡", permission=GROUP, priority=2, block=True)


@draw.handle()
async def draw_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if_poke = isinstance(event, PokeNotifyEvent)
        if not if_poke:
            if not str(event.get_message()) == "抽卡":
                return
        draw_h = DrawCardRule(event.group_id, event.user_id)
        card, hint, image = await draw_h.drawcard()
        if hint == "没到时间":
            msg = "还有{time}分钟才能抽奖哟哦".format(time=card)
            await draw.finish(msg)
        if card == 0:
            if if_poke:
                if random.choices([True, False], [0.3, 0.8])[0]:
                    msg = "今日已经戳得够多了，请明天再来吧~"
                    await draw.finish(msg)
                else:
                    msg = await get_sticker(1)
                    await draw.finish(msg)
            else:
                msg = hint
                await draw.finish(msg)
        build_msg = ""
        for i in card.keys():
            grade = config.grade_to_grade_name[get_grade(i)]
            build_msg += grade + \
                "「{name}」".format(name=number2name(i)) + \
                "×" + str(card[i]) + "\n"

        if if_poke:
            msg = MessageSegment.at(event.user_id) + random.choice(config.poke_draw_hint) + "\n" + image + "\n" + "------------------------------" + \
                "\n" + "获得了：" + "\n" + build_msg.rstrip()
        else:
            msg = MessageSegment.at(event.user_id) + "这些卡送你了~" + "\n" + image + "\n" + "------------------------------" + \
                "\n" + "获得了：" + "\n" + build_msg.rstrip()

        # 可能会跟一张图
        if random.choices([True, False], [0.7, 0.3])[0]:
            await draw.finish(msg)
        else:
            await draw.send(msg)
            await asyncio.sleep(random.randint(1, 8))
            msg = await get_sticker(2)
            await draw.finish(msg)


# 用戳一戳触发抽卡
async def _group_poke(bot: Bot, event: Event, state: T_State) -> bool:
    if not config.while_season_end:
        return isinstance(event, PokeNotifyEvent) and event.is_tome()

group_poke = on_notice(_group_poke, priority=2, block=True)
group_poke.handle()(draw_handler)


ranking = on_startswith("排行榜", permission=GROUP, priority=2, block=True)


@ranking.handle()
async def ranking_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "排行榜":
            ranking_h = DrawCardRule(event.group_id, event.user_id)
            score = ranking_h.get_group_ranking()
            score_member = list(score.keys())
            msg_1 = ''
            n = 0
            for i in score_member:
                n += 1
                try:
                    name = await bot.call_api("get_group_member_info", group_id=event.group_id, user_id=i)
                    name = dict(name)['nickname'].strip()
                except:
                    name = i
                msg_1 += "\n" + str(n) + "、" + name + "\n" + \
                    "图鉴完成度：" + str(score[i])
                if n == 10:
                    break
            msg = MessageSegment.face(99) + f"◇━━{get_season_name()}排行榜━━◇" + \
                MessageSegment.face(99) + msg_1
            await ranking.finish(msg)


compose = on_startswith("合成", permission=GROUP, priority=2, block=True)


@compose.handle()
async def handle_first_receive(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        card = str(event.get_message()).strip()
        card = card[2:].strip()
        card = card.split(" ")
        if len(card) < 2:
            msg = "合成失败！" + "\n" + "可能是角色名间没加空格或缺少角色卡片"
            await compose.finish(msg)
        elif len(card) > 2:
            msg = "合成失败！" + "\n" + "需合成的角色卡片过多"
            await compose.finish(msg)
        elif len(card) == 2:
            # 判断合成卡片是否为编号
            card_list = card
            if_card_1 = card[0][:1].isnumeric()
            if_card_2 = card[1][:1].isnumeric()
            if not if_card_1 and not if_card_2:
                card_list = name2number(card)
            elif not if_card_1:
                card_list[0] = name2number(card[0])
            elif not if_card_2:
                card_list[1] = name2number(card[1])

            # 若有不存编号，返回0
            lose_number = []
            for i in range(len(card_list)):
                if card_list[i] == 0:   # 对应上面的名字转编号，利用编号转名字判断该名字是否存在
                    lose_number.append(card[i])
                elif number2name(card_list[i]) == 0:   # 利用编号转名字判断该编号是否存在
                    lose_number.append(card[i])

            # 发送提示编号不存在的消息
            lose_number_len = len(lose_number)
            if lose_number_len != 0:
                if lose_number_len == 1:
                    await compose.finish(lose_number + "不存在")
                if lose_number_len == 2:
                    await compose.finish(lose_number[0] + "和" + lose_number[1] + "不存在")
            card = card_list
            # 合成
            print("需合成的图片：", card)

            compose_card = DrawCardRule(event.group_id, event.user_id)
            card, image = await compose_card.compose(card[0], card[1], False)
            if image == 0:
                msg = card
                await compose.finish(msg)

            grade = config.grade_to_grade_name[get_grade(card)]
            msg = grade + \
                "「{name}」".format(name=number2name(card)) + "×1"
            msg = MessageSegment.at(event.user_id) + "芜湖~你合成了一张{name}卡".format(name=grade) + "\n" + image + "\n" + "------------------------------" + \
                "\n" + "获得了：" + "\n" + msg

            # 可能会跟一张图
            if random.choices([True, False], [0.7, 0.3])[0]:
                await compose.finish(msg)
            else:
                await compose.send(msg)
                await asyncio.sleep(random.randint(1, 5))
                msg = await get_sticker(2)
                await compose.finish(msg)

compose_oneclick = on_startswith(
    "一键合成", permission=GROUP, priority=2, block=True)


@compose_oneclick.handle()
async def handle_first_receive(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        card = str(event.get_message()).strip()
        card = card[4:].strip().replace(" ", "")
        if card in config.grade_name_to_grade:
            card = config.grade_name_to_grade[card]
            compose_card = DrawCardRule(event.group_id, event.user_id)
            card, image = await compose_card.compose(card, card, True)
            if image == 0:  # 返回0说明没有多余的卡用于一键合成了
                msg = card
                await compose_oneclick.finish(msg)

            grade = config.grade_to_grade_name[get_grade(card)]
            msg = grade + \
                "「{name}」".format(name=number2name(card)) + "×1"
            msg = MessageSegment.at(event.user_id) + "芜湖~你合成了一张{name}卡".format(name=grade) + "\n" + image + "\n" + "------------------------------" + \
                "\n" + "获得了：" + "\n" + msg

            # 可能会跟一张图
            if random.choices([True, False], [0.7, 0.3])[0]:
                await compose_oneclick.finish(msg)
            else:
                await compose_oneclick.send(msg)
                await asyncio.sleep(random.randint(1, 5))
                msg = await get_sticker(2)
                await compose_oneclick.finish(msg)


super_compose_oneclick = on_startswith(
    "超级一键合成", permission=GROUP, priority=2, block=True)


@super_compose_oneclick.handle()
async def handle_super_compose(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        card_dict: Dict[int, int] = defaultdict(lambda: 0)  # card id to count
        compose_card = DrawCardRule(event.group_id, event.user_id)
        for card_grade in config.grade_to_grade_name.keys():
            while 1:
                card_id, image = await compose_card.compose_without_image(card_grade, card_grade, True)
                if type(card_id) is not int or image == 0:  # 返回0说明没有多余的卡用于一键合成了
                    break
                card_dict[card_id] += 1
        if not card_dict:
            await super_compose_oneclick.finish("没有多余的卡用于一键合成了")
            return
        card_dict = OrderedDict(sorted(card_dict.items(), key=lambda card_id_and_count: get_grade(card_id_and_count[0])))
        msg = f"{MessageSegment.at(event.user_id)} 超级一键合成！\n" \
              f"{pic_composition(card_dict.keys())}\n" \
              f"------------------------------\n" \
              f"获得了"
        for card_id in card_dict:
            msg += f"\n{config.grade_to_grade_name[get_grade(card_id)]}「{number2name(card_id)}」×{card_dict[card_id]}"
        # 可能会跟一张图
        if random.choices([True, False], [0.7, 0.3])[0]:
            await super_compose_oneclick.finish(msg)
        else:
            await super_compose_oneclick.send(msg)
            # await asyncio.sleep(random.randint(1, 5))
            msg = await get_sticker(2)
            await super_compose_oneclick.finish(msg)

show = on_startswith("查看", permission=GROUP, priority=3, block=True)


@show.handle()
async def handle_first_receive(bot: Bot, event: GroupMessageEvent, state: T_State):
    if not config.while_season_end:
        args = str(event.get_message()).strip().replace(
            " ", "")
        args = args[2:]
        print("查看的角色", args)
        if args:
            state["name"] = args  # 如果用户发送了参数则直接赋值


@show.got("name", prompt="你想查看哪个角色呢？")
async def handle_name(bot: Bot, event: GroupMessageEvent, state: T_State):
    if not config.while_season_end:
        name = state["name"]
        # 判断卡片是否为编号
        if_card = name[:1].isnumeric()
        if if_card:
            name = number2name(name)
            if name == 0:   # 判断该编号是否存在
                await show.finish("该编号不存在")

        number = name2number(name)
        if number == 0:   # 判断该名字是否存在
            await show.finish("你想查看的角色不存在，请重新输入！")

        show_card = DrawCardRule(event.group_id, event.user_id)
        if_role = show_card.if_user_role(number)
        if not if_role:
            await show.finish("你尚未拥有该角色哟")
        role_url = get_image(number)
        role_grade = get_grade(number)
        role_introduction = get_introduction(number)
        if role_grade == 1:
            role_grade = "超稀有"
        elif role_grade == 2:
            role_grade = "稀有"
        elif role_grade == 3:
            role_grade = "普通"
        image = MessageSegment.image(file=role_url)
        if not role_introduction:
            msg = MessageSegment.at(event.user_id) + "嘿咻~{name}给您呈上".format(
                name=name) + "\n" + image + "\n" + "名字：" + name + "\n" + "等级：" + role_grade
        else:
            msg = MessageSegment.at(event.user_id) + "嘿咻~{name}给您呈上".format(
                name=name) + "\n" + image + "\n" + role_introduction + "\n" + "------------------------------" + "\n" + "名字：" + name + "\n" + "等级：" + role_grade

        # 可能会跟一张图
        if random.choices([True, False], [0.2, 0.7])[0]:
            await draw.finish(msg)
        else:
            await draw.send(msg)
            await asyncio.sleep(random.randint(1, 5))
            msg = await get_sticker(3)
            await draw.finish(msg)

view = on_startswith("查看仓库", permission=GROUP, priority=2, block=True)


@view.handle()
async def view_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "查看仓库":
            view_h = DrawCardRule(event.group_id, event.user_id)
            image, role_length, all_role_length, card_lenth, role, grade, member_ranking = await view_h.view_user_data()
            msg = MessageSegment.at(event.user_id) + \
                "的仓库" + image + "\n" + "持有卡片总数：" + str(card_lenth) + "\n" + "超稀有卡片数：" + \
                str(grade["grade_1"]) + "\n" + "稀有卡片数：" + str(grade["grade_2"])+"\n" + "普通卡片数：" + \
                str(grade["grade_3"]) + "\n" + "图鉴完成度：" + \
                str(role_length) + "/" + str(all_role_length) + \
                "\n" + "当前群排名：" + str(member_ranking)

            await view.send(msg)

role_list = on_startswith("卡牌列表", permission=GROUP, priority=2, block=True)


@role_list.handle()
async def role_list_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "卡牌列表":
            all_role_list = get_all_role_name()
            msg = ''
            n = 0
            for i in all_role_list:
                n += 1
                msg_1 = "\n"+str(n)+"、"+"「{name}」".format(name=i)
                msg += msg_1

            msg = MessageSegment.face(99) + "◇━卡牌列表━◇" + \
                MessageSegment.face(99) + msg
            await role_list.finish(msg)

role_number = on_startswith("编号图", permission=GROUP, priority=2, block=True)


@role_number.handle()
async def role_number_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "编号图":
            image = get_number_pic()
            msg = MessageSegment.face(99) + "◇━编号图━◇" + \
                MessageSegment.face(99) + image + "角色图上为对应编号，编号可代替角色名字使用哟~"
            await role_number.finish(msg)

personal_info = on_startswith("个人信息", permission=GROUP, priority=2, block=True)

@personal_info.handle()
async def personal_info_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "个人信息":
            score_handle = GlobalHandle(event.group_id, event.user_id)
            score = score_handle.get_score()
            grade,EXP,coin = score["grade"],score["EXP"],score["coin"]
            if grade == 1:
                grade = config.one_grade
            elif grade == 2:
                grade = config.two_grade
            elif grade == 3:
                grade = config.three_grade
            elif grade == 4:
                grade = config.four_grade
            else:
                grade = config.five_grade
            image = MessageSegment.image(
                file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
            msg = MessageSegment.at(event.user_id) + "的个人信息" + "\n" + image + "\n" + \
                MessageSegment.face(random.choice([21, 24, 172, 175, 179, 183, 187, 202, 203, 212])) + "等级：{}".format(grade) + "\n" + \
                MessageSegment.face(190) + "经验值：{}".format(str(EXP)) + "\n" + \
                MessageSegment.face(158) + "墨鱼币：{}".format(str(coin))
            await personal_info.finish(msg)



oneword = on_startswith("一言", permission=GROUP, priority=2, block=True)


@oneword.handle()
async def oneword_hander(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "一言":
            word, source = await get_oneword()
            msg = '"{word}" -----《{source}》'.format(word=word, source=source)
            await oneword.finish(msg)


sign_in = on_startswith("签到", permission=GROUP, priority=2, block=True)


@sign_in.handle()
async def sign_in_handler(bot: Bot, event: GroupMessageEvent):
    if not config.while_season_end:
        if str(event.get_message()) == "签到":
            sign_in_h = DrawCardRule(event.group_id, event.user_id)
            msg, n, coin = await sign_in_h.sign_in()
            if msg == 0:
                msg = "今天签到过了哟！"
                await sign_in.finish(msg)
            else:
                image = MessageSegment.image(
                    file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
                msg = MessageSegment.at(event.user_id) + "签到成功！" + "\n" + image + "\n" + \
                    "你是今天第{}个签到的人！".format(n) + "\n" + "------------------------------" + "\n" + \
                    MessageSegment.face(random.choice([21, 24, 172, 175, 179, 183, 187, 202, 203, 212])) + "累积签到天数：" + str(msg) + "\n" + \
                    MessageSegment.face(190) + "获得了10点经验值" + "\n" + \
                    MessageSegment.face(158) + "获得了{}枚墨鱼币".format(coin)
                await sign_in.send(msg)

                if_upgrade, grade, EXP, coin = await upgrade_check(event.group_id, event.user_id)
                print(if_upgrade, grade, EXP, coin)
                if if_upgrade == 1:
                    if grade == 2:
                        grade = config.two_grade
                        image = MessageSegment.image(
                            file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
                        msg = MessageSegment.at(event.user_id) + "恭喜你正式入门了，晋升为{}！".format(grade) + "\n" + image + "\n" + \
                            "------------------------------" + "\n" + MessageSegment.face(69) + "升级奖励：" + "\n" + MessageSegment.face(54) + "墨鱼币50枚" + "\n" + MessageSegment.face(54) + "每日签到的墨鱼币增加至10枚" + "\n" +\
                            "------------------------------" + "\n" + MessageSegment.face(144) + "等级：" + grade + "\n" + MessageSegment.face(
                                190) + "经验值：" + str(EXP) + "\n" + MessageSegment.face(158) + "墨鱼币数：" + str(coin)
                        await sign_in.send(msg)
                        await asyncio.sleep(1)
                        msg = await get_sticker(4)
                        await sign_in.finish(msg)
                    elif grade == 3:
                        grade = config.three_grade
                        image = MessageSegment.image(
                            file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
                        msg = MessageSegment.at(event.user_id) + "哟！祝贺你成为了{}！".format(grade) + "\n" + image + "\n" + \
                            "------------------------------" + "\n" + MessageSegment.face(69) + "升级奖励：" + "\n" + MessageSegment.face(54) + "墨鱼币100枚" + "\n" + MessageSegment.face(54) + "每日签到的墨鱼币增加至15枚" + "\n" +\
                            "------------------------------" + "\n" + MessageSegment.face(
                                144) + "等级：" + grade + "\n" + MessageSegment.face(190) + "经验值：" + str(EXP) + "\n" + MessageSegment.face(158) + "墨鱼币数：" + str(coin)
                        await sign_in.send(msg)
                        await asyncio.sleep(1)
                        msg = await get_sticker(4)
                        await sign_in.finish(msg)
                    elif grade == 4:
                        grade = config.four_grade
                        image = MessageSegment.image(
                            file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
                        msg = MessageSegment.at(event.user_id) + "不错不错，我现在封你为{}，以后好好努力".format(grade) + "\n" + image + "\n" + \
                            "------------------------------" + "\n" + MessageSegment.face(69) + "升级奖励：" + "\n" + MessageSegment.face(54) + "墨鱼币150枚" + "\n" + MessageSegment.face(54) + "每日签到的墨鱼币增加至20枚" + "\n" +\
                            "------------------------------" + "\n" + MessageSegment.face(
                                144) + "等级：" + grade + "\n" + MessageSegment.face(190) + "经验值：" + str(EXP) + "\n" + MessageSegment.face(158) + "墨鱼币数：" + str(coin)
                        await sign_in.send(msg)
                        await asyncio.sleep(1)
                        msg = await get_sticker(4)
                        await sign_in.finish(msg)
                    elif grade == 5:
                        grade = config.five_grade
                        image = MessageSegment.image(
                            file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
                        msg = MessageSegment.at(event.user_id) + "你成功登峰造极，成为了{}！".format(grade) + "\n" + image + "\n" + \
                            "------------------------------" + "\n" + MessageSegment.face(69) + "升级奖励：" + "\n" + MessageSegment.face(54) + "墨鱼币200枚" + "\n" + MessageSegment.face(54) + "每日签到的墨鱼币增加至25枚" + "\n" +\
                            "------------------------------" + "\n" + MessageSegment.face(
                                144) + "等级：" + grade + "\n" + MessageSegment.face(190) + "经验值：" + str(EXP) + "\n" + MessageSegment.face(158) + "墨鱼币数：" + str(coin)
                        await sign_in.send(msg)
                        await asyncio.sleep(1)
                        msg = await get_sticker(4)
                        await sign_in.finish(msg)


scheduler = require("nonebot_plugin_apscheduler").scheduler


@scheduler.scheduled_job("date", run_date="2022-2-18 21:00:00", id="upgrade")
async def upgrade():
    config.while_season_end = True
    bot = list(get_bots().values())[0]

    _group_list = await bot.call_api("get_group_list")
    print(_group_list)
    group_list = []
    for i in _group_list:
        group_list.append(i["group_id"])

    msg = ["大家好哟！又要开始开始赛季结算咯！（正在全群广播）","我记得上次赛季结算还是在上次呢","好了，下面开始数据统计","统计赛季数据ing..."]
    for n in msg:
        for i in group_list:
            try:
                await bot.call_api("send_group_msg", group_id=i, message=n)
            except:
                pass
        await asyncio.sleep(2)

    for i in group_list:
        score_h = DrawCardRule(i, 0)
        score = score_h.get_group_ranking()
        score_member = list(score.keys())
        score_n = list(score.values())

        level_3 = 0
        level_2 = 0
        level_1 = 0
        n = get_role_length()
        for j in score_n:
            if j >= n*5/6:
                level_3 += 1
            elif j >= n/2:
                level_2 += 1
            else:
                level_1 += 1

        try:
            await bot.call_api("send_group_msg", group_id=i, message="下面公布本群数据")
        except:
            pass
        await asyncio.sleep(2)
        msg = f"◇━━赛季数据━━◇\n本赛季玩家数：{len(score_member)}\n肝帝级玩家数：{level_3}\n普通级玩家数：{level_2}\n萌新级玩家数：{level_1}"
        try:
            await bot.call_api("send_group_msg", group_id=i, message=msg)
        except:
            pass
    await asyncio.sleep(2)
    

    for i in group_list:
        score_h = DrawCardRule(i, 0)
        score = score_h.get_group_ranking()
        score_member = list(score.keys())
        score_n = list(score.values())
        msg_1 = ''
        n = 0
        for j in score_member:
            n += 1
            try:
                name = await bot.call_api("get_group_member_info", group_id=i, user_id=j)
                name = dict(name)['nickname'].strip()
            except:
                name = j
            msg_1 += "\n" + str(n) + "、" + name + "\n" + \
                "图鉴完成度：" + str(score[j])
            if n == 10:
                break
        try:
            await bot.call_api("send_group_msg", group_id=i, message="接下来是本群赛季排行前十名")
        except:
            pass
        await asyncio.sleep(2)
        msg = "◇━━赛季排行━━◇" + msg_1
        try:
            await bot.call_api("send_group_msg", group_id=i, message=msg)
        except:
            pass
    await asyncio.sleep(2)

    for i in group_list:
        msg = "◇━━赛季奖励━━◇\n每位玩家将会得到：\n" + \
            MessageSegment.face(158) + "图鉴数×5的墨鱼币\n" + \
            MessageSegment.face(190) + "图鉴数×10的经验"
        try:
            await bot.call_api("send_group_msg", group_id=i, message=msg)
        except:
            pass
    await asyncio.sleep(4)

    for i in group_list:
        try:
            await bot.call_api("send_group_msg", group_id=i, message="发放奖励ing...")
        except:
            pass
    await asyncio.sleep(4)

    for i in group_list:
        score_h = DrawCardRule(i, 0)
        score = score_h.get_group_ranking()
        score_member = list(score.keys())
        score_n = list(score.values())
        n = 0
        for j in score_member:
            score_handle = GlobalHandle(i, j)
            score_handle.add_score(0, score_n[n]*10, score_n[n]*5)
            n += 1
        try:
            await bot.call_api("send_group_msg", group_id=i, message="奖励完毕")
        except:
            pass

    for i in group_list:
        try:
            await bot.call_api("send_group_msg", group_id=i, message="正在清除赛季数据...")
        except:
            pass
    season_over()
    for i in group_list:
        try:
            await bot.call_api("send_group_msg", group_id=i, message="清除完毕！")
        except:
            pass

    await asyncio.sleep(2)
    for i in group_list:
        try:
            await bot.call_api("send_group_msg", group_id=i, message="开始更新...")
        except:
            pass


exchange = on_startswith("兑换", permission=GROUP, priority=2, block=True)


@exchange.handle()
async def exchange_handle(bot: Bot, event: GroupMessageEvent, state: T_State):
    commodity = str(event.get_message())[2:].strip()
    print("兑换的商品", commodity)
    if commodity:
        state["commodity"] = commodity  # 如果用户发送了参数则直接赋值


@exchange.got("commodity", prompt="◇━商品列表━◇\n" + "⭐️抽卡（90币）" + "\n" + "------------------------------" + "\n" + "请问要兑换什么呢~")
async def exchange_got(bot: Bot, event: GroupMessageEvent, state: T_State):
    commodity = state["commodity"]
    if commodity == "抽卡":
        score_handle = GlobalHandle(event.group_id, event.user_id)
        score = score_handle.get_score()
        if score["coin"] >= 90:
            score_handle.reduce_score(0, 0, 90)
            await exchange.send("兑换成功！")
            draw_h = DrawCardRule(event.group_id, event.user_id)
            card, hint, image = await draw_h.drawcard(True)
            build_msg = ""
            for i in card.keys():
                grade = config.grade_to_grade_name[get_grade(card)]
                build_msg += grade + \
                    "「{name}」".format(name=number2name(i)) + \
                    "×" + str(card[i]) + "\n"

            msg = MessageSegment.at(event.user_id) + "这些卡送你了~" + "\n" + image + "\n" + "------------------------------" + \
                "\n" + "获得了：" + "\n" + build_msg.rstrip()

            # 可能会跟一张图
            if random.choices([True, False], [0.7, 0.3])[0]:
                await draw.finish(msg)
            else:
                await draw.send(msg)
                await asyncio.sleep(random.randint(1, 8))
                msg = await get_sticker(2)
                await draw.finish(msg)
        else:
            await exchange.finish("墨鱼币不够用啦！")


async def _group_member_add(bot: Bot, event: Event, state: T_State) -> bool:
    if not config.while_season_end:
        return isinstance(event, GroupIncreaseNoticeEvent)
    else:
        return False

group_member_add = on_notice(_group_member_add, priority=2, block=True)


@group_member_add.handle()
async def group_member_add_handle(bot: Bot, event: GroupIncreaseNoticeEvent):
    if not config.while_season_end:
        # 获取qq头像
        image = MessageSegment.image(
            file="https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(event.user_id))
        # 获取用户昵称和性别
        data = await bot.call_api("get_group_member_info", group_id=event.group_id, user_id=event.user_id)
        data = dict(data)
        joiner_name = data['nickname'].strip()
        sex = data['sex']
        if sex == "male":
            sex = "帅哥"
        elif sex == "female":
            sex = "美女"
        elif sex == "unknown":
            sex = "不肯暴露呢"
        # 获取群总数和审核管理员
        data = await bot.call_api("get_group_info", group_id=event.group_id)
        joiner_count = str(dict(data)["member_count"] + 1)
        print(event.operator_id)
        if event.operator_id == 0:
            operator_name = "无"
        else:
            data = await bot.call_api("get_group_member_info", group_id=event.group_id, user_id=event.operator_id)
            operator_name = dict(data)['nickname'].strip()
        # 构建消息
        msg = MessageSegment.at(event.user_id) + "欢迎回家！" + MessageSegment.face(144) + "\n" + image + "\n" + "┏昵称：" + joiner_name + \
            "\n" + "┣号码：" + str(event.group_id) + "\n" + "┣性别：" + sex + "\n" + "┣审核管理员：" + operator_name + \
            "\n" + "┣注意：新人请注意啦，以后要乖哦！" + "\n" + f"┗您是第{joiner_count}位入群的！"
        # 会跟一张图
        await group_member_add.send(msg)
        await asyncio.sleep(random.randint(1, 5))
        msg = await get_sticker(2)
        await group_member_add.finish(msg)
