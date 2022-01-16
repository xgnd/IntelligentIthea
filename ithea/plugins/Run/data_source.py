import sqlite3
import os
import random
import copy
import heapq
import re
import json
from datetime import datetime, date
from nonebot import get_driver

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

def check_record(group):
    group = str(group)
    project_path = config.data_path
    file_path = os.path.join(project_path,'record.json')

    with open(file_path,"r", encoding='UTF-8') as f:
        record = json.loads(f.read())

    today = str(date.today())
    time = datetime.now().replace(microsecond=0)

    if group in list(record.keys()):
        last_time = record[group][-1]
        last_time = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
        mincount = (time - last_time).seconds
        mincount = mincount/60
        mincount = round(mincount, 1)
        if mincount >= config.CD:
            record[group].append(str(time))
        else:
            mincount = config.CD - mincount
            mincount = round(mincount, 1)   # 这个函数有时不管用，多放一个保险
            return mincount, "没到时间"
    else:
        record[group] = [str(time)]

    with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()
    return 200, "时间记录成功"

class Run_chara:
    # 通过传入文件名 读入对应的角色Json文档进行初始化
    def __init__(self, id:str):
        project_path = config.data_path
        file_path = os.path.join(project_path,'config.json')
        
        # 读文件
        with open(file_path,"r", encoding='UTF-8') as f:
            self.config = json.loads(f.read())
            

        # 搬运数据
        self.id = id
        self.name = self.config[id]['name']
        self.icon = self.config[id]["icon"]
        self.speed = self.config[id]['speed']
        self.skill = self.config[id]['skill']
        del self.config
        
   
        
    def getskill(self,sid):
        skill = self.skill[str(sid)]
        return skill
    def geticon(self):
        icon = self.icon
        return str(icon)
    def getname(self):
        name = self.name
        return str(name)
    def getspeed(self):
        return self.speed
    def getskill_prob_list(self):
        prob_list = [0 for x in range(0,5)]
        sum = 1
        for i in range(1,5):
            prob_list[i]=self.skill[str(i)]["skill_porb"]
            sum -= prob_list[i]
        prob_list[0] = sum
        return  prob_list

class RunningJudger:
    def __init__(self):
        self.on = {}
        self.support = {}
        self.support_on = {}

    def set_support(self, gid):
        self.support[gid] = {}

    def get_support(self, gid):
        return self.support[gid] if self.support.get(gid) is not None else 0

    def add_support(self, gid, uid, id, score):
        self.support[gid][uid] = [id, score]

    def get_support_id(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][0]
        else:
            return 0

    def get_support_score(self, gid, uid):
        if self.support[gid].get(uid) is not None:
            return self.support[gid][uid][1]
        else:
            return 0

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def turn_on(self, gid):
        self.on[gid] = True

    def turn_off(self, gid):
        self.on[gid] = False
# 下注开关

    def get_on_off_support_status(self, gid):
        return self.support_on[gid] if self.support_on.get(gid) is not None else False

    def turn_on_support(self, gid):
        self.support_on[gid] = True

    def turn_off_support(self, gid):
        self.support_on[gid] = False



class ScoreCounter:
    def __init__(self):
        with open(config.RUN_DB_PATH,"r",encoding="utf-8-sig") as f:
            self.data = json.load(f)

    def _add_score(self, gid, uid, score):
        group = str(gid)
        qq = str(uid)
        current_score = self._get_score(gid, uid)
        self.data[group][qq]["coin"] = current_score+score
        with open(config.RUN_DB_PATH, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.data, ensure_ascii=False))
            f.close()

    def _reduce_score(self, gid, uid, score):
        group = str(gid)
        qq = str(uid)
        current_score = self._get_score(gid, uid)
        if current_score >= score:
            self.data[group][qq]["coin"] = current_score-score
        else:
            self.data[group][qq]["coin"] = 0
        with open(config.RUN_DB_PATH, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.data, ensure_ascii=False))
            f.close()

    def _get_score(self, gid, uid):
        group = str(gid)
        qq = str(uid)
        if group in self.data.keys():
            if qq in self.data[group].keys():
                if self.data[group][qq]["coin"] == 0:
                    return 0
                return self.data[group][qq]["coin"]
            else:
                self.data[group][qq] = {"grade": 1, "EXP": 0, "coin": 0}
                with open(config.RUN_DB_PATH, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(self.data, ensure_ascii=False))
                    f.close()
                return 0
        else:
            self.data[group] = {
                qq: {"grade": 1, "EXP": 0, "coin": 0}}
            with open(config.RUN_DB_PATH, 'w', encoding='utf-8') as f:
                f.write(json.dumps(self.data, ensure_ascii=False))
                f.close()
            return 0
            

# 判断金币是否足够下注
    def _judge_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                return 1
            else:
                return 0
        except Exception as e:
            raise Exception(str(e))


# 这个类用于记录一些与技能有关的变量，如栞的ub计数，可可萝的主人
class NumRecord:
    def __init__(self):
        self.kan_num = {}
        self.kokoro_num = {}

    def init_num(self, gid):
        self.kan_num[gid] = 1
        self.kokoro_num[gid] = 0

    def get_kan_num(self, gid):
        return self.kan_num[gid]

    def add_kan_num(self, gid, num):
        self.kan_num[gid] += num

    def set_kokoro_num(self, gid, kokoro_id):
        l1 = list(range(1, config.NUMBER+1))
        l1.remove(kokoro_id)
        self.kokoro_num[gid] = random.choice(l1)
        return self.kokoro_num[gid]

    def get_kokoro_num(self, gid):
        return self.kokoro_num[gid]

# 将角色以角色编号的形式分配到赛道上，返回一个赛道的列表。
def chara_select():
    l = range(1, config.TOTAL_NUMBER+1)
    select_list = random.sample(l, 5)
    return select_list
# 取得指定角色编号的赛道号,输入分配好的赛道和指定角色编号
def get_chara_id(list, id):
    raceid = list.index(id)+1
    return raceid

# 输入赛道列表和自己的赛道，选出自己外最快的赛道
def select_fast(position, id):
    list1 = copy.deepcopy(position)
    list1[id-1] = 999
    fast = list1.index(min(list1))
    return fast+1

# 输入赛道列表和自己的赛道，选出自己外最慢的赛道。
def select_last(position, id):
    list1 = copy.deepcopy(position)
    list1[id-1] = 0
    last = list1.index(max(list1))
    return last+1
# 输入赛道列表，自己的赛道和数字n，选出自己外第n快的赛道。
def select_number(position, id, n):
    lis = copy.deepcopy(position)
    lis[id-1] = 999
    max_NUMBER = heapq.nsmallest(n, lis)
    max_index = []
    for t in max_NUMBER:
        index = lis.index(t)
        max_index.append(index)
        lis[index] = 0
    nfast = max_index[n-1]
    return nfast+1

# 输入自己的赛道号，选出自己外的随机1个赛道，返回一个赛道编号
def select_random(id):
    l1 = list(range(1, config.NUMBER+1))
    l1.remove(id)
    select_id = random.choice(l1)
    return select_id

# 输入自己的赛道号和数字n，选出自己外的随机n个赛道，返回一个赛道号的列表
def nselect_random(id, n):
    l1 = list(range(1, config.NUMBER+1))
    l1.remove(id)
    select_list = random.sample(l1, n)
    return select_list

# 选择除自己外的全部对象，返回赛道号的列表
def select_all(id):
    l1 = list(range(1, config.NUMBER+1))
    l1.remove(id)
    return l1

def search_kokoro(charalist):
    if 10 in charalist:
        return charalist.index(10)+1

    else:
        return None


# 对单一对象的基本技能：前进，后退，沉默，暂停，必放ub
def forward(id, step, position):
    fid = int(id)
    position[fid-1] = position[fid-1] - step
    position[fid-1] = max(1, position[fid-1])
    return


def backward(id, step, position):

    position[id-1] = position[id-1] + step
    position[id-1] = min(config.ROADLENGTH, position[id-1])
    return


def give_silence(id, num, silence):
    silence[id-1] += num
    return


def give_pause(id, num, pause):
    pause[id-1] += num
    return


def give_ub(id, num, ub):
    ub[id-1] += num
    return


def change_position(id, rid, position):
    position[id-1], position[rid-1] = position[rid-1], position[id-1]
    return

# 用于技能参数增加
def add(a, b):
    return a+b


# 对列表多对象的基本技能
def n_forward(list, step, position):
    for id in list:
        position[id-1] = position[id-1] - step
        position[id-1] = max(1, position[id-1])
    return


def n_backward(list, step, position):
    for id in list:
        position[id-1] = position[id-1] + step
        position[id-1] = min(config.ROADLENGTH, position[id-1])
    return


def n_give_silence(list, num, silence):
    for id in list:
        silence[id-1] += num
    return


def n_give_pause(list, num, pause):
    for id in list:
        pause[id-1] += num
    return


def n_give_ub(list, num, ub):
    for id in list:
        ub[id-1] += num
    return

# 概率触发的基本技能
def prob_forward(prob, id, step, position):
    r = random.random()
    if r < prob:
        forward(id, step, position)
        return 1
    else:
        return 0


def prob_backward(prob, id, step, position):
    r = random.random()
    if r < prob:
        backward(id, step, position)
        return 1
    else:
        return 0


def prob_give_pause(prob, id, num, pause):
    r = random.random()
    if r < prob:
        give_pause(id, num, pause)
        return 1
    else:
        return 0


def prob_give_silence(prob, id, num, silence):
    r = random.random()
    if r < prob:
        give_silence(id, num, silence)
        return 1
    else:
        return 0

# 根据概率触发技能的返回，判断是否增加文本，成功返回成功文本，失败返回失败文本
def prob_text(is_prob, text1, text2):
    if is_prob == 1:
        addtion_text = text1
    else:
        addtion_text = text2
    return addtion_text

# 按概率表选择一个技能编号
def skill_select(cid):
    c = Run_chara(str(cid))
    skillnum_ = ['0', '1', '2', '3', '4']
    # 概率列表,读json里的概率，被注释掉的为老版本固定概率
    r_ = c.getskill_prob_list()
   #r_ = [0.7, 0.1, 0.1, 0.08, 0.02]
    sum_ = 0
    ran = random.random()
    for num, r in zip(skillnum_, r_):
        sum_ += r
        if ran < sum_:
            break
    return int(num)

# 加载指定角色的指定技能，返回角色名，技能文本和技能效果
def skill_load(cid, sid):
    c = Run_chara(str(cid))
    name = c.getname()
    if sid == 0:
        return name, "none", "null"
    else:
        skill_text = c.getskill(sid)["skill_text"]
        skill_effect = c.getskill(sid)["skill_effect"]
        return name, skill_text, skill_effect


# 初始状态相关函数
def position_init(position):
    for i in range(0, config.NUMBER):
        position[i] = config.ROADLENGTH
    return


def silence_init(silence):
    for i in range(0, config.NUMBER):
        silence[i] = 0
    return


def pause_init(pause):
    for i in range(0, config.NUMBER):
        pause[i] = 0
    return


def ub_init(ub):
    for i in range(0, config.NUMBER):
        ub[i] = 0
    return

# 赛道初始化
def race_init(position, silence, pause, ub):
    position_init(position)
    silence_init(silence)
    pause_init(pause)
    ub_init(ub)
    return

# 一个角色跑步 检查是否暂停
def one_unit_run(id, pause, position, Race_list):
    if pause[id-1] == 0:
        cid = Race_list[id-1]
        c = Run_chara(str(cid))
        speedlist = c.getspeed()
        step = random.choice(speedlist)
        forward(id, step, position)
        return
    else:
        pause[id-1] -= 1
        return

# 一轮跑步，每个角色跑一次
def one_turn_run(pause, position, Race_list):
    for id in range(1, 6):
        one_unit_run(id, pause, position, Race_list)

# 打印当前跑步状态
def print_race(Race_list, position):
    racemsg = ""
    for id in range(1, 6):
        cid = Race_list[id-1]
        c = Run_chara(str(cid))
        icon = c.geticon()

        for n in range(1, config.ROADLENGTH+1):
            if n != position[id-1]:
                racemsg = racemsg + config.ROAD
            else:
                racemsg = racemsg + icon
        if id != 5:
            racemsg = racemsg + "\n"

    return racemsg
# 检查比赛结束用，要考虑到同时冲线
def check_game(position):
    winner = []
    is_win = 0
    for id in range(1, 6):
        if position[id-1] == 1:
            winner.append(id)
            is_win = 1
    return is_win, winner


def introduce_race(Race_list):
    msg = ''
    for id in range(1, 6):
        msg += f'{id}号：'
        cid = Race_list[id-1]
        c = Run_chara(str(cid))
        icon = c.geticon()
        name = c.getname()
        msg += f'{name}，图标为{icon}'
        msg += "\n"
    msg += f"所有人请在{config.SUPPORT_TIME}秒内选择支持的选手。格式如下：\n1/2/3/4/5号xx墨鱼币\n如果金币为0，可以发送“签到”领取墨鱼币"
    return msg

# 取正则匹配的字符串
def parse_cmd(pattern, msg: str) -> list:
    return re.findall(pattern, msg, re.S)