import random
import os
import json
from nonebot import get_driver
from nonebot.adapters.cqhttp import MessageSegment

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

project_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(project_path,'record.json')

def start(group,qq):
    with open(file_path,"r", encoding="utf-8-sig") as f:
        record = json.load(f)

    random.shuffle(config.items)
    answer=''
    for i in range(4):
        answer+=str(config.items[i])

    if group in record.keys():
        if qq in record[group].keys():
            return False
        else:
            record[group][qq] = [0,answer] 
    else:
        record[group] = {qq:[0,answer]}
    # print(record)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.close()
    return True

def end(group,qq):
    with open(file_path,"r", encoding="utf-8-sig") as f:
        record = json.load(f)

    if group in record.keys():
        if qq in record[group].keys():
            record[group].pop(qq)
        else:
            return False
    else:
        return False
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.close()
    return True

def guess(group,qq,number):
    with open(file_path,"r", encoding="utf-8-sig") as f:
        record = json.load(f)
    try:
        a_count=0 # initial A count
        b_count=0 # initial B count
        answer = record[group][qq][1]
        record[group][qq][0] += 1
        if number==answer:
            round_times = record[group][qq][0]
            record[group].pop(qq)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False))
                f.close()
            return "4A0B",round_times
        for i in range(4):
            for j in range(4):
                if i==j and number[i]==answer[j]:
                    a_count+=1
                elif number[i]==answer[j]:
                    b_count+=1  
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()
        return '{0}A{1}B'.format(a_count,b_count),record[group][qq][0]
    except:
        return 0,0


async def get_sticker(number) -> MessageSegment:
    """ 
    表情包选择，适用于不同场景下的表情包选择，不同的序号代表不同的场景
    1、抽卡次数到时
    2、获得卡时
    3、查看角色时
    4、升级时
    """
    image_route = os.path.join(os.getcwd(), "data", "image")
    path = os.path.join(image_route, "sticker")
    path = os.path.join(path, str(number))
    files = os.listdir(path)
    files = random.choice(files)
    path = "file:///" + path+"/"+files
    image = MessageSegment.image(file=path)
    return image

class GlobalHandle():
    """ 全局数据操作 """

    def __init__(self, gid, uid):
        self.group = str(gid)
        self.qq = str(uid)
        
        data_route = os.path.join(os.getcwd(), "data", "plugin")   # 取数据路径
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
