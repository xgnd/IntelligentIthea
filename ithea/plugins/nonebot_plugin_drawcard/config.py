from typing import Dict
from collections import OrderedDict
from pydantic import BaseSettings
import os,json

d_route = os.path.join(os.getcwd(), "data", "plugin")   # 取数据路径
i_route = os.path.join(os.getcwd(), "data", "image")   # 取图片路径

with open(os.path.join(d_route, "config.json"), 'r', encoding='utf-8-sig') as f:   # 读入角色数据
    d = json.load(f)
    f.close()
with open(i_route + "/warehouse.json", 'r', encoding='utf-8-sig') as f:
    wd = json.load(f)
    f.close()

class Config(BaseSettings):
    while_season_end = False

    data_route = d_route
    image_route = i_route
    data = d
    warehouse_data = wd

    season = data["rules"]["settings"]["season"]
    season_name = data["rules"]["settings"]["season_name"]

    drawcard_times = data["rules"]["settings"]["drawcard_times"]   # 一天抽卡次数
    drawcard_cd = data["rules"]["settings"]["drawcard_cd"]   # 每次抽卡时间间隔，分钟

    sign_in_EXP = data["rules"]["settings"]["sign_in_EXP"]
    sign_in_coin = data["rules"]["settings"]["sign_in_coin"]

    one_grade = data["rules"]["settings"]["one_grade"]
    two_grade = data["rules"]["settings"]["two_grade"]
    three_grade = data["rules"]["settings"]["three_grade"]
    four_grade = data["rules"]["settings"]["four_grade"]
    five_grade = data["rules"]["settings"]["five_grade"]

    one_grade_EXP = data["rules"]["settings"]["one_grade_EXP"]
    two_grade_EXP = data["rules"]["settings"]["two_grade_EXP"]
    three_grade_EXP = data["rules"]["settings"]["three_grade_EXP"]
    four_grade_EXP = data["rules"]["settings"]["four_grade_EXP"]
    five_grade_EXP = data["rules"]["settings"]["five_grade_EXP"]
    
    poke_draw_hint = ["呀嘞呀嘞~来卡咯","别戳了别戳了，再戳就了戳晕啦","这些卡送你了~","啊啊啊啊别戳啦！","妈咪妈咪哄，看我变出了一堆卡~","哟豁~竟然出来了这么多卡"]

    grade_to_grade_name: Dict[int, str] = OrderedDict(sorted({1: "超稀有", 2: "稀有", 3: "普通"}.items(), key=lambda t: t[0]))
    grade_name_to_grade: Dict[str, int] = OrderedDict([(v, k) for k, v in grade_to_grade_name.items()])

    class Config:
        extra = "ignore"