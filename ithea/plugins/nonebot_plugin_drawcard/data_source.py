import asyncio
import aiohttp
import json
import os
import random
import shutil
from collections import OrderedDict
from datetime import date, datetime
from PIL import Image, ImageDraw, ImageFont

from nonebot import get_driver
from nonebot.adapters import Bot
from nonebot.adapters.cqhttp import MessageSegment

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

data_route = config.data_route
image_route = config.image_route

role_data = config.data
warehouse_data = config.warehouse_data

# 加载图片
background_small = Image.open(os.path.join(
    image_route, "background_small.png"))
background_middle = Image.open(os.path.join(
    image_route, "background_middle.png"))
background_big = Image.open(os.path.join(image_route, "background_big.png"))

all_role_data = role_data["role"]["role_data"]
all_card_dict = {}
all_avatar_dict = {}
all_grey_avatar_dict = {}
for i in all_role_data.keys():
    role_image_url = all_role_data[i]["url"].replace("file:///", "")
    new_img = Image.open(role_image_url)
    all_card_dict[i] = new_img
    role_image_url = all_role_data[i]["url"].replace(
        "file:///", "").replace("image", "image/头像")
    new_img = Image.open(role_image_url)
    all_avatar_dict[i] = new_img
    role_image_url = all_role_data[i]["url"].replace(
        "file:///", "").replace("image", "image/灰头像")
    new_img = Image.open(role_image_url)
    all_grey_avatar_dict[i] = new_img


ttf = ImageFont.truetype("C:/windows/fonts/arial.ttf", 15)


class DrawCardRule():
    def __init__(self, qq_group, qq):
        self.group = str(qq_group)
        self.qq = str(qq)
        self.user_data_url = os.path.join(
            data_route, self.group, self.qq+'.json')
        self.group_data_url = os.path.join(
            data_route, self.group, "all.json")

    def get_user_data(self):
        """ 取用户数据，无返回值 """
        with open(self.user_data_url, 'r', encoding='utf-8-sig') as f:
            self.user_data = json.load(f)
            self.role_length = self.user_data['role_length']
            self.card_length = self.user_data['card_length']
            self.user_role = self.user_data['role']
            self.user_role_grade = self.user_data['grade']
            f.close()

    def get_group_data(self):
        """ 取群数据，无返回值 """
        with open(self.group_data_url, 'r', encoding='utf-8-sig') as f:
            self.group_data = json.load(f)
            self.user = self.group_data['user']
            self.user_score = self.group_data['score']
            f.close()

    def if_user_role(self, role) -> bool:
        """ 检测用户是否有卡片，返回一个布尔值 """
        with open(self.user_data_url, 'r', encoding='utf-8-sig') as f:
            user_data = json.load(f)
            user_role = list(user_data['role'].keys())
            if role not in user_role:
                return False
            else:
                return True
            f.close()

    async def drawcard(self, exchange=False):
        """ 抽卡，返回角色名字列表或没到时间提示 """
        await DrawCardRule.userdata(self)  # 检测是否有群数据文件
        if not exchange:
            mincount, hint = await DrawCardRule.drawcard_record(self)
        else:
            mincount = 200
            hint = "时间记录成功"
        print("时间记录：", mincount, "提示：", hint)
        image = ''
        if hint == "没到时间":
            return mincount, hint, image
        if mincount == 0:
            return mincount, hint, image
        if mincount == 200:
            DrawCardRule.get_user_data(self)  # 取用户数据
            DrawCardRule.get_group_data(self)  # 取群数据

            draw_role_card = []
            draw_role_length = []
            grade_1 = 0
            grade_2 = 0
            grade_3 = 0

            draw_num = random.choices([2, 3, 4], [0.6, 0.4, 0.2])[
                0]  # 一次抽卡获得卡片数

            # 取抽卡概率
            draw_weights = role_data["rules"]['weights']['draw']

            draw_weights = dict_shuffle(draw_weights)  # 打乱卡牌概率的字典
            for i in range(draw_num):
                draw_card = random.choices(
                    list(draw_weights.keys()), list(draw_weights.values()))[0]  # 抽卡
                grade = get_grade(draw_card)
                if draw_card in draw_role_card:
                    n = draw_role_card.index(draw_card)
                    draw_role_length[n] += 1
                    continue
                if grade == 1:
                    n = grade_1
                    grade_1 += 1
                if grade == 2:
                    n = grade_1 + grade_2
                    grade_2 += 1
                if grade == 3:
                    n = grade_1 + grade_2 + grade_3
                    grade_3 += 1
                draw_role_card.insert(n, draw_card)
                draw_role_length.insert(n, 1)
            self.draw_card_dict = dict(zip(draw_role_card, draw_role_length))
            await DrawCardRule.savedata(self, self.draw_card_dict)  # 保存数据
            image = DrawCardRule.pic_composition(
                self, list(self.draw_card_dict.keys()))
            return self.draw_card_dict, "抽卡成功", image

    async def drawcard_record(self):
        """ 检测抽卡间隔，返回时间间隔提示 """
        record_url = os.path.join(
            data_route, self.group, 'record.json')

        if_record_url = os.path.exists(record_url)

        today = str(date.today())
        time = datetime.now().replace(microsecond=0)

        if not if_record_url:
            with open(record_url, 'w', encoding='utf-8') as f:
                record = {today: {self.qq: [str(time)]}}
                f.write(json.dumps(record, ensure_ascii=False))
                f.close()
                return 200, "时间记录成功"

        with open(record_url, 'r', encoding='utf-8-sig') as f:
            record = json.load(f)
            f.close()

        if today in list(record.keys()):
            if self.qq in list(record[today].keys()):
                if len(record[today][self.qq]) >= config.drawcard_times:
                    return 0, "今日抽卡次数已用完咯，请明天再来吧~"
                last_time = record[today][self.qq][-1]
                last_time = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
                mincount = (time - last_time).seconds
                mincount = mincount/60
                # print(mincount)
                mincount = round(mincount, 1)
                if mincount >= config.drawcard_cd:
                    record[today][self.qq].append(str(time))
                else:
                    mincount = config.drawcard_cd - mincount
                    mincount = round(mincount, 1)   # 这个round函数有时不管用，多放一个保险
                    return mincount, "没到时间"
            elif self.qq not in list(record[today].keys()):
                record[today][self.qq] = [str(time)]
        else:
            record[today] = {self.qq: [str(time)]}

        with open(record_url, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()
        return 200, "时间记录成功"

    async def compose(self, card_1, card_2, oneclick):
        """ 合成，返回角色名字列表 """
        await DrawCardRule.userdata(self)  # 检测是否有群数据文件
        DrawCardRule.get_user_data(self)  # 取用户数据
        DrawCardRule.get_group_data(self)  # 取群数据

        # 一键合成时判断是否是同级卡，抽取多余卡，从该等级抽取卡牌
        if oneclick:
            grade = card_1
            card_1, card_2 = await DrawCardRule.compose_get_card(self, card_1)
            if card_1 == 0 and card_2 == 0:
                return "没有多余的卡用于一键合成了", 0

        # 判断是否是同级卡，一键合成则此跳过
        if not oneclick:
            card_1_grade = get_grade(card_1)
            card_2_grade = get_grade(card_2)
            if card_1_grade != card_2_grade:
                return "这两张卡不是同级卡片哟，请使用同等级卡合成~", 0
            grade = card_1_grade

            # 判断用户是否有这张卡，因为一键合成时是从用户已有卡片里抽的，所以这里一键合成的可以跳过
            if_card_1 = DrawCardRule.if_user_role(self, card_1)
            if_card_2 = DrawCardRule.if_user_role(self, card_2)

            if not if_card_1 and not if_card_2:
                return "这两张卡您都没有" + MessageSegment.face(174), 0
            elif not if_card_1:
                return "您没有这张{name}卡哟".format(name=card_1), 0
            elif not if_card_2:
                return "您没有这张{name}卡哟".format(name=card_2), 0

            if card_1 == card_2 and self.user_role[card_1] < 2:
                return "这张卡不够用啦！", 0

        print(self.user_role)
        # 如果是一样的卡且用户数据里此卡数量为2，直接删除此卡
        if card_1 == card_2 and self.user_role[card_1] == 2:
            self.user_role.pop(card_1)
        else:
            self.user_role[card_1] -= 1
            self.user_role[card_2] -= 1
            if self.user_role[card_1] == 0:
                self.user_role.pop(card_1)
            if self.user_role[card_2] == 0:
                self.user_role.pop(card_2)

        # 减少卡对应的等级拥有的卡牌数
        if grade == 1:
            self.user_data["grade"]["grade_1"] -= 2
        if grade == 2:
            self.user_data["grade"]["grade_2"] -= 2
        if grade == 3:
            self.user_data["grade"]["grade_3"] -= 2

        # 获取合成等级概率
        if grade == 3:
            grade = random.choices([2, 3], [0.1, 0.8])[0]
        elif grade == 2:
            grade = random.choices([1, 2], [0.2, 0.8])[0]
        elif grade == 1:
            pass   # 当等级为超稀有时，合成只会出超稀有，合成等级不变

        compose_weights = dict_shuffle(
            role_data["rules"]["weights"]["compose"]["grade_"+str(grade)])   # 对该等级的卡牌顺序进行打乱

        # 抽取一张卡牌
        role_list = []
        role = random.choices(list(compose_weights.keys()),
                              list(compose_weights.values()))[0]
        role_list.append(role)
        image = DrawCardRule.pic_composition(self, role_list)   # 图片合成

        await DrawCardRule.savedata(self, {role: 1})   # 保存数据

        return role, image

    async def compose_get_card(self, grade):
        """ 一键合成时从用户数据里抽取两个多余的卡 """
        redundant_card = []
        role_list = list(self.user_role.keys())

        for i in range(len(self.user_role)):
            card = random.choice(role_list)
            if self.user_role[card] > 1 and grade == get_grade(card):
                if self.user_role[card] >= 3:
                    redundant_card.append(card)
                    redundant_card.append(card)
                else:
                    redundant_card.append(card)
            if redundant_card == 2:
                break
            role_list.remove(card)

        if len(redundant_card) < 2:
            return 0, 0

        return redundant_card[0], redundant_card[1]

    def pic_composition(self, card_list):
        """ 抽卡和合成图片合成 """
        # 加载底图
        new_img_list = []
        for i in card_list:
            new_img = all_card_dict[i]
            new_img_list.append(new_img)

        # 底图上需要P掉的区域
        # 以左边界为准（left, upper, right, lower）
        box = []
        card_list_len = len(card_list)
        if card_list_len == 1:
            base_img = background_small
            box.append((150, 70, 546, 626))
        elif card_list_len == 2:
            base_img = background_middle
            box.append((70, 223, 466, 779))
            box.append((536, 223, 932, 779))
        elif card_list_len == 3:
            base_img = Image.open(os.path.join(
                image_route, "background_big.png"))
            box.append((177, 70, 573, 626))
            box.append((750, 70, 1146, 626))
            box.append((463, 696, 859, 1252))
        elif card_list_len == 4:
            base_img = Image.open(os.path.join(
                image_route, "background_big.png"))
            box.append((177, 70, 573, 626))
            box.append((750, 70, 1146, 626))
            box.append((177, 696, 573, 1252))
            box.append((750, 696, 1146, 1252))

        for i in range(card_list_len):
            base_img.paste(new_img_list[i], box[i])

        base_img = base_img.resize((500, 500))
        # 可以设置保存路径

        save_route = image_route + \
            '/cache/{filename}.png'.format(
                filename=str(int(datetime.now().timestamp())))
        base_img.save(save_route)
        save_route = "file:///"+save_route
        image = MessageSegment.image(file=save_route)
        return image

    async def savedata(self, draw_card_dict):
        """ 保存数据 """
        for i in list(draw_card_dict.keys()):
            if i in list(self.user_role.keys()):
                self.user_data["role"][i] += draw_card_dict[i]
            else:
                self.user_data["role"][i] = draw_card_dict[i]
            grade = get_grade(i)
            if grade == 1:
                self.user_data["grade"]["grade_1"] += 1
                continue
            if grade == 2:
                self.user_data["grade"]["grade_2"] += 1
                continue
            if grade == 3:
                self.user_data["grade"]["grade_3"] += 1
        role_length = len(self.user_data["role"])   # 取用户图鉴数
        card_length = sum([self.user_data["grade"]["grade_1"], self.user_data["grade"]
                           ["grade_2"], self.user_data["grade"]["grade_3"]])   # 取用户卡片数量
        self.group_data['score'][self.qq] = role_length
        self.group_data['score'] = dict(
            sorted(self.group_data['score'].items(), key=lambda x: x[1], reverse=True))   # 用户按图鉴从多到少排序
        self.user_data['role_length'] = role_length
        self.user_data['card_length'] = card_length

        with open(self.user_data_url, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.user_data, ensure_ascii=False))
            f.close()
        with open(self.group_data_url, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.group_data, ensure_ascii=False))
            f.close()

    async def userdata(self):
        """ 检测是否有群数据文件 """
        # 欲检测路径
        group_url = os.path.join(data_route, self.group)
        if_group_url = os.path.exists(group_url)
        user_url = os.path.join(data_route, self.group, self.qq+'.json')
        if_user_url = os.path.exists(user_url)
        # 进行判断并写入
        print("是否有群数据", if_group_url, if_user_url)
        if not if_group_url:
            os.makedirs(group_url)
            with open(self.group_data_url, 'w', encoding='utf-8') as f:
                group_data = {"user": [int(self.qq)], "score": {}}
                f.write(json.dumps(group_data, ensure_ascii=False))
                f.close()
        if not if_user_url:
            with open(self.user_data_url, 'w', encoding='utf-8') as f:
                user_data = {"role_length": 0, "card_length": 0, "role": {
                }, "grade": {"grade_1": 0, "grade_2": 0, "grade_3": 0}}
                f.write(json.dumps(user_data, ensure_ascii=False))
                f.close()

    async def view_user_data(self):
        """ 查看仓库 """
        await DrawCardRule.userdata(self)

        with open(self.group_data_url, 'r', encoding='utf-8-sig') as f:
            group_data = list(json.load(f)["score"].keys())
            if self.qq in group_data:
                member_ranking = await DrawCardRule.get_group_member_ranking(self)
            else:
                member_ranking = len(group_data) + 1
            f.close()

        with open(self.user_data_url, 'r', encoding='utf-8-sig') as f:
            user_data = json.load(f)
            role_length, card_lenth, role, grade = user_data["role_length"], user_data[
                "card_length"], user_data["role"], user_data["grade"]
            all_role_length = get_role_length()   # 取角色总数
            f.close()

        if "warehouse" not in list(user_data.keys()):
            if len(role.keys()) == 0:
                image = os.path.join(image_route, "all.png")
                image = MessageSegment.image(file="file:///"+image)
                return image, role_length, all_role_length, card_lenth, role, grade, member_ranking

            image = DrawCardRule.warehouse_pic_composition(self, role)

            user_data["warehouse"] = role
            with open(self.user_data_url, 'w', encoding='utf-8') as f:
                f.write(json.dumps(user_data, ensure_ascii=False))
                f.close()
            return image, role_length, all_role_length, card_lenth, role, grade, member_ranking
        else:
            add_pic = {}
            user_warehouse = user_data["warehouse"]

            # 查看角色图片是否在仓库，是否能够对应得上
            variance = dict_reduce(role, user_warehouse)

            if len(variance) == 0:
                image = os.path.join(
                    data_route, self.group, self.qq+".png")
                save_route = "file:///"+image
                image = MessageSegment.image(file=save_route)
                return image, role_length, all_role_length, card_lenth, role, grade, member_ranking

            image = DrawCardRule.warehouse_pic_composition(
                self, variance, True)
            user_data["warehouse"] = user_data["role"]
            with open(self.user_data_url, 'w', encoding='utf-8') as f:
                f.write(json.dumps(user_data, ensure_ascii=False))
                f.close()

            return image, role_length, all_role_length, card_lenth, role, grade, member_ranking

    def warehouse_pic_composition(self, role_list, if_warehouse=False):
        """ 仓库图片合成 """
        print("更改角色列表：", role_list, "是否复用用户仓库图片：", if_warehouse)
        if if_warehouse:
            warehouse_pic = os.path.join(
                data_route, self.group, self.qq+".png")
        if not if_warehouse:
            warehouse_pic = os.path.join(image_route, "all.png")
        base_img = Image.open(warehouse_pic)

        all_role_list = role_data["role"]["role_data"]

        role_list_keys = list(role_list.keys())

        new_img_list = []
        for i in role_list_keys:
            if role_list[i] != 404:
                new_img = all_avatar_dict[i]
                new_img_list.append(new_img)
            else:
                new_img = all_grey_avatar_dict[i]
                new_img_list.append(new_img)

        box = []

        for i in role_list_keys:
            box.append(tuple(warehouse_data[i]))

        n = 0
        for i in role_list_keys:
            # for j in box:
            if role_list[i] != 404:
                draw = ImageDraw.Draw(new_img_list[n])
                draw.text((61, 61), '×' +
                          str(role_list[i]), font=ttf, fill=(0, 0, 0))
                base_img.paste(
                    new_img_list[n], box[n])
            else:
                base_img.paste(
                    new_img_list[n], box[n])
            n += 1

        base_img.resize((500, 500))

        save_route = os.path.join(data_route, self.group, self.qq+".png")
        base_img.save(save_route)
        save_route = "file:///"+save_route
        image = MessageSegment.image(file=save_route)
        return image

    def get_group_ranking(self) -> dict:
        """ 取群排名及图鉴完成度 """
        DrawCardRule.get_group_data(self)
        return self.user_score

    def get_old_group_ranking(self, n) -> dict:
        """ 取群历史排名及图鉴完成度，传入一个代表赛季的整数 """
        self.group_data_url = os.path.join(
            data_route, "history", "s"+str(n), self.group, "all.json")
        with open(self.group_data_url, 'r', encoding='utf-8-sig') as f:
            self.group_data = json.load(f)
            self.user = self.group_data['user']
            self.user_score = self.group_data['score']
            f.close()
        return self.user_score

    async def get_group_member_ranking(self) -> int:
        """ 取个人在群里的排名 """
        grou_user_score = list(DrawCardRule.get_group_ranking(self).keys())
        member_ranking = grou_user_score.index(self.qq) + 1
        return member_ranking

    async def sign_in(self):
        """ 签到，使用这个函数时应阿巴阿巴阿巴，再阿巴阿巴（懒得写注释了） """

        record_url = os.path.join(data_route, 'global_record.json')

        today = str(date.today())

        with open(record_url, 'r', encoding='utf-8-sig') as f:
            record = json.load(f)
            f.close()

        # 签到记录
        if self.group in record.keys():   # 判断该群是否已有过记录
            if today in record[self.group].keys():   # 判断数据中的日期是不是今天
                if self.qq in record[self.group][today]:   # 判断该用户是否有过签到
                    return 0, 0, 0
                else:
                    record[self.group][today].append(self.qq)
                    # 累积签到天数，如果之前有签到过就加1，没有则报错转为等于1
                    try:
                        record[self.group]["user"][self.qq] += 1
                    except:
                        record[self.group]["user"][self.qq] = 1
            else:   # 不是今天则删除上次记录的日期，记录今天
                del record[self.group][list(record[self.group])[1]]
                record[self.group][today] = [self.qq]
                # 累积签到天数，如果之前有签到过就加1，没有则报错转为等于1
                try:
                    record[self.group]["user"][self.qq] += 1
                except:
                    record[self.group]["user"][self.qq] = 1
        else:
            record[self.group] = {"user": {self.qq: 1}, today: [self.qq]}

        with open(record_url, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()

        # 签到奖励记录
        try:
            global_data_path = os.path.join(data_route, "global_data.json")
            with open(global_data_path, "r", encoding="utf-8-sig") as f:
                grade = json.load(f)[self.group][self.qq]["grade"]
        except:
            grade = 1
        coin = config.sign_in_coin + (grade-1)*5
        score_handle = GlobalHandle(self.group, self.qq)
        score_handle.add_score(0, config.sign_in_EXP, coin)

        n = record[self.group]["user"][self.qq]
        print("累积签到天数：" + str(n))
        sign_in_count = str(record[self.group][today].index(self.qq) + 1)
        print(n, sign_in_count, coin)
        return n, sign_in_count, coin


def get_number_pic() -> MessageSegment:
    """ 取编号图 """
    route = "file:///" + image_route + "/number_pic.png"
    image = MessageSegment.image(file=route)
    return image


def get_all_role_name() -> list:
    """ 取所有角色名字，返回角色名字字符串列表 """
    all_role_name = list(role_data["number"].values())
    return all_role_name


def get_role_length() -> int:
    """ 取角色总数 """
    all_role_length = role_data["rules"]["settings"]["length"]
    return all_role_length


def get_image(number) -> str:
    """ 取角色图片，返回一个图片url """
    image_url = role_data["role"]["role_data"][number]["url"]
    return image_url


def get_grade(number) -> int:
    """ 取角色等级，返回一个整数 """
    role_grade = role_data["role"]["role_data"][number]["grade"]
    return role_grade


def get_introduction(number) -> int:
    """ 取角色等级，返回一个整数 """
    role_introduction = role_data["role"]["role_data"][number]["introduction"]
    return role_introduction


async def get_sticker(number) -> MessageSegment:
    """ 
    表情包选择，适用于不同场景下的表情包选择，不同的序号代表不同的场景
    1、抽卡次数到时
    2、获得卡时
    3、查看角色时
    4、升级时
    """
    path = os.path.join(image_route, "sticker")
    path = os.path.join(path, str(number))
    files = os.listdir(path)
    files = random.choice(files)
    path = "file:///" + path+"/"+files
    image = MessageSegment.image(file=path)
    return image


def numbername(number):
    """ 编号转名字，传入一个代表编号的字符串或字符串列表 """
    role_data_number = role_data["number"]
    try:
        if type(number) == str:
            name = role_data_number[number]
            return name
        elif type(number) == list:
            return [role_data_number[i] for i in number]
    except:
        return 0

def namenumber(name):
    """ 名字转编号，传入一个代表名字的字符串或字符串列表 """
    role_data_number = role_data["number"]
    role_data_name = dict(
        zip(role_data_number.values(), role_data_number.keys()))
    try:
        if type(name) == str:
            number = role_data_name[name]
            return number
        elif type(name) == list:
            return [role_data_name[i] for i in name]
    except:
        return 0


def season_over():
    files = os.listdir(data_route)
    files.remove("history")
    files.remove("终末台词.json")
    files.remove("config.json")
    files.remove("global_data.json")
    files.remove("global_record.json")

    file_path = data_route+"/history/s"+str(config.season)
    os.makedirs(file_path)
    for i in files:
        shutil.move(data_route+"/"+i, file_path+"/"+i)


class GlobalHandle():
    """ 全局数据操作 """

    def __init__(self, gid, uid):
        self.group = str(gid)
        self.qq = str(uid)

        self.global_data_path = os.path.join(data_route, "global_data.json")
        with open(self.global_data_path, "r", encoding="utf-8-sig") as f:
            self.data = json.load(f)

    def add_score(self, grade, EXP, coin):
        """ 增加等级/经验值/墨鱼币，皆传入整数，无返回值 """
        user_score = self.get_score()
        self.data[self.group][self.qq]["grade"] += grade
        self.data[self.group][self.qq]["EXP"] += EXP
        self.data[self.group][self.qq]["coin"] += coin
        with open(self.global_data_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.data, ensure_ascii=False))
            f.close()

    def reduce_score(self, grade, EXP, coin):
        """ 减少等级/经验值/墨鱼币，皆传入整数，无返回值 """
        user_score = self.get_score()
        self.data[self.group][self.qq]["grade"] -= grade
        self.data[self.group][self.qq]["EXP"] -= EXP
        self.data[self.group][self.qq]["coin"] -= coin

        # if self.data[self.group][self.qq]["grade"] <= 0:
        #     self.data[self.group][self.qq]["grade"] = 1
        if self.data[self.group][self.qq]["EXP"] < 0:
            self.data[self.group][self.qq]["EXP"] = 0
        if self.data[self.group][self.qq]["coin"] < 0:
            self.data[self.group][self.qq]["coin"] = 0

        with open(self.global_data_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.data, ensure_ascii=False))
            f.close()

    def get_score(self) -> dict:
        """ 获取用户全局数据，返回一个字典 """
        if self.group in self.data.keys():
            if self.qq in self.data[self.group].keys():
                return self.data[self.group][self.qq]
            else:
                self.data[self.group][self.qq] = {
                    "grade": 1, "EXP": 0, "coin": 0}
                with open(self.global_data_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(self.data, ensure_ascii=False))
                    f.close()
                return self.data[self.group][self.qq]
        else:
            self.data[self.group] = {
                self.qq: {"grade": 1, "EXP": 0, "coin": 0}}
            with open(self.global_data_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.data, ensure_ascii=False))
                f.close()
            return self.data[self.group][self.qq]


async def upgrade_check(qq_group, qq):
    """ 用户等级检测，根据经验值检测升级或降级并写入数据，返回一个整数（0为啥都没发生,1为升级，2为降级）和等级、经验值、墨鱼币数 """
    group = str(qq_group)
    qq = str(qq)

    data_url = os.path.join(data_route, 'global_data.json')

    try:
        with open(data_url, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            user_data = data[group][qq]
            f.close()

        score_handle = GlobalHandle(group, qq)

        if user_data["grade"] == 1:
            if user_data["EXP"] >= config.two_grade_EXP:
                score_handle.add_score(1, 0, 50)
                return 1, user_data["grade"]+1, user_data["EXP"], user_data["coin"]+50
            else:
                return 0, user_data["grade"], user_data["EXP"], user_data["coin"]

        elif user_data["grade"] == 2:
            if user_data["EXP"] >= config.three_grade_EXP:
                score_handle.add_score(1, 0, 100)
                return 1, user_data["grade"]+1, user_data["EXP"], user_data["coin"]+100
            else:
                if user_data["EXP"] < config.two_grade_EXP:
                    score_handle.reduce_score(1, 0, 0)
                    return 2, user_data["grade"], user_data["EXP"], user_data["coin"]
                return 0, user_data["grade"], user_data["EXP"], user_data["coin"]

        elif user_data["grade"] == 3:
            if user_data["EXP"] >= config.four_grade_EXP:
                score_handle.add_score(1, 0, 150)
                return 1, user_data["grade"]+1, user_data["EXP"], user_data["coin"]+150
            else:
                if user_data["EXP"] < config.three_grade_EXP:
                    score_handle.reduce_score(1, 0, 0)
                    return 2, user_data["grade"], user_data["EXP"], user_data["coin"]
                return 0, user_data["grade"], user_data["EXP"], user_data["coin"]

        elif user_data["grade"] == 4:
            if user_data["EXP"] >= config.five_grade_EXP:
                score_handle.add_score(1, 0, 200)
                return 1, user_data["grade"]+1, user_data["EXP"], user_data["coin"]+200
            else:
                if user_data["EXP"] < config.four_grade_EXP:
                    score_handle.reduce_score(1, 0, 0)
                    return 2, user_data["grade"], user_data["EXP"], user_data["coin"]
                return 0, user_data["grade"], user_data["EXP"], user_data["coin"]

        else:   # 事实上这层判断并没有用，但看着对称舒服
            return 0, user_data["grade"], user_data["EXP"], user_data["coin"]

    except:
        return 0, 0, 0, 0


async def download_user_pic(qq) -> str:
    """ 下载用户头像 """
    url = "https://q1.qlogo.cn/g?b=qq&nk={}&s=640".format(qq)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            content = await res.read()
            route = image_route+'/cache/{}.png'.format(qq)
            with open(route, 'wb') as f:
                f.write(content)
    return route


async def get_oneword():
    """ 获取一言 """
    source_list = ["a", "b", "c", "d"]
    url = "https://v1.hitokoto.cn/?c={source}&encode=json&charset=utf-8".format(
        source=random.choice(source_list))
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            oneword = await res.text()
            oneword = json.loads(oneword)
            word = oneword["hitokoto"]
            source = oneword["from"]
            return word, source


def dict_shuffle(d) -> dict:
    """" 打乱字典元素顺序，参数为字典，返回一个打乱的字典 """
    keys = list(d.keys())  # 把键值存入列表中
    random.shuffle(keys)  # 随机打乱列表中的keys值
    order_d = OrderedDict()  # 创建一个有序字典对象
    for key in keys:
        order_d[key] = d[key]
    return dict(order_d)


def dict_reduce(dict_1, dict_2) -> dict:
    """ 字典找不同，传入的字典的值只能是整数 """
    re_dict = {}
    list_1_keys = list(dict_1.keys())
    list_2_keys = list(dict_2.keys())
    for i in list_1_keys:
        if i in list_2_keys:
            if dict_1[i] != dict_2[i]:
                re_dict[i] = dict_1[i]
                continue
        else:
            re_dict[i] = dict_1[i]

    for i in list_2_keys:
        if i not in list(dict_1.keys()):
            re_dict[i] = 404

    return re_dict
