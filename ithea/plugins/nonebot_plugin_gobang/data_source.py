import json
import os
import random
import re

from nonebot import get_driver
from nonebot.adapters.cqhttp import MessageSegment
from PIL import Image, ImageDraw

from .config import Config

global_config = get_driver().config
config = Config(**global_config.dict())

project_path = os.path.dirname(os.path.abspath(__file__))
record_path = os.path.join(project_path, 'record.json')
cache_path = os.path.join(project_path, 'cache')

# 棋局默认配置
default = [
    "",    # 玩家1
    "",    # 玩家2
    1,     # 当前落子方，1或2
    [[]],  # 棋局
    [0, 0],  # 上次玩家1落子位置，用于悔棋
    [0, 0],  # 上次玩家2落子位置，用于悔棋
    0,     # 玩家1是否使用过悔棋
    0      # 玩家2是否使用过悔棋
]

# 定义三个常量函数，用来表示白棋，黑棋，以及 空
EMPTY = 0
BLACK = 1
WHITE = 2

# 定义黑色（黑棋用，画棋盘）
black_color = [0, 0, 0]
# 定义白色（白棋用）
white_color = [255, 255, 255]

# 加载图片
BLACK_pic = Image.open(os.path.join(project_path, 'black.png'))
WHITE_pic = Image.open(os.path.join(project_path, 'white.png'))
background = Image.open(os.path.join(project_path, 'background.png'))


def match(group, qq):
    """
        对局匹配，返回：
        0：不在棋局中
        i：棋局信息
    """
    group = str(group)
    qq = str(qq)
    with open(record_path, "r", encoding="utf-8-sig") as f:
        record = json.load(f)

    if group in record.keys():
        if record[group]:
            # 判断自己是否在棋局中
            for i in record[group].values():
                if qq in i:
                    return i
            return 0
        else:
            return 0
    else:
        return 0


def is_ready(group, qq):
    """
        等待房间满60s后检查，不够人则关闭房间，够人不变，返回：
        0：不够人
        1：够人
    """
    group = str(group)
    qq = str(qq)
    with open(record_path, "r", encoding="utf-8-sig") as f:
        record = json.load(f)

    i = record[group][qq]
    if i[1] == "":
        record[group].pop(qq)
        with open(record_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()
        return 0
    else:
        return 1


def gobang_start(group, qq):
    """
        五子棋开始，返回：
        0：开始失败，已在棋局中
        1：开始成功
    """
    group = str(group)
    qq = str(qq)
    with open(record_path, "r", encoding="utf-8-sig") as f:
        record = json.load(f)

    if match(group, qq) == 0:
        _default = default
        _default[0] = qq
        if group in record.keys():
            record[group][qq] = default
        else:
            record[group] = {}
            record[group][qq] = default

        with open(record_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()
        return 1
    else:
        return 0


def gobang_join(group, qq):
    """
        五子棋加入，返回：
        0：无棋局可加入
        1：正在棋局中，无法加入其它棋局
        棋局发起人qq：加入成功并返回棋局发起人qq
    """
    group = str(group)
    qq = str(qq)
    with open(record_path, "r", encoding="utf-8-sig") as f:
        record = json.load(f)

    if group in record.keys():
        if record[group]:
            # 判断自己是否在棋局中
            for i in record[group].values():
                if qq in i:
                    return 1
            keys_list = list(record[group].keys())
            # 逆序遍历，优先加入最新的棋局
            for i in range(len(record[group])-1, -1, -1):
                if record[group][keys_list[i]][1] == "":
                    record[group][keys_list[i]][1] = qq
                    record[group][keys_list[i]] = gobang_init(
                        record[group][keys_list[i]])   # 初始化棋盘
                    with open(record_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(record, ensure_ascii=False))
                        f.close()
                    return keys_list[i]
            return 0
        else:
            return 0
    else:
        return 0


def gobang_init(info):
    """ 初始化棋盘 """
    board = [[]] * 15
    for col in range(len(board)):
        board[col] = [EMPTY] * 15
    info[3] = board
    return info


def gobang_canmove(info, col, row):
    """ 判断当前点位是否可以下棋 """
    if info[3][col][row] == EMPTY:
        return info
    return False


def gobang_move(info, col, row):
    """ 定义盘上的下棋函数，col表示列，row表示行，is_black表示判断当前点位该下黑棋，还是白棋 """
    is_white = info[2]-1
    info[3][col][row] = WHITE if is_white else BLACK
    info[2] = 1 if is_white else 2
    n = 5 if is_white else 4
    info[n] = [col, row]
    return info


def gobang_draw(info, col, row, group, qq):
    """ 绘制棋盘 """
    is_white = info[2]-1
    if info[4] == [0, 0] and info[5] == [0, 0]:   # 第一次落子
        base_img = background
    else:
        n = 4 if is_white else 5
        filename = str(group)+str(info[0])+str(info[n][0])+str(info[n][1])
        base_img = Image.open(cache_path+'/{file}.png'.format(file=filename))

    # 底图上需要P掉的区域
    # 以左边界为准（left, upper, right, lower）
    box = (38+62*col-25, 40+62*row-25, 38+62*col+25, 40+62*row+25)
    img = WHITE_pic if is_white else BLACK_pic
    base_img.paste(img, box, img)

    save_route = cache_path + \
        '/{file}.png'.format(file=str(group)+str(info[0])+str(col)+str(row))
    base_img.save(save_route)   # 未标红点棋盘图，用于悔棋和下次合成

    draw = ImageDraw.Draw(base_img)
    draw.ellipse([(38+62*col-5, 40+62*row-5), (38+62*col+5, 40 +
                                               62*row+5)], outline="red", fill="red")   # 落的子标上红点

    save_route = cache_path + \
        '/{file}.png'.format(file=str(group) +
                             str(info[0])+str(col)+str(row)+"-")
    base_img.save(save_route)   # 已标红点棋盘图，将发送此图

    save_route = "file:///"+save_route
    image = MessageSegment.image(file=save_route)
    return image


def gobang_save(info, group, qq):
    """
        保存棋盘，返回：
        True：成功
        False：失败
    """
    group = str(group)
    qq = str(qq)
    with open(record_path, "r", encoding="utf-8-sig") as f:
        record = json.load(f)

    try:
        record[group][info[0]] = info

        with open(record_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False))
            f.close()
        return True
    except:
        return False


def gobang_end(info, group, qq):
    """
        结束对局
    """
    group = str(group)
    qq = str(qq)
    with open(record_path, "r", encoding="utf-8-sig") as f:
        record = json.load(f)

    record[group].pop(info[0])
    with open(record_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.close()
    # 清理图片
    filelist = os.listdir(cache_path)
    for i in filelist:
        flag = str(group)+str(info[0])
        if i.startswith(flag):
            os.remove(cache_path+'/'+i)


# 判断输赢，传入当前棋盘上的棋子列表，输出结果，黑棋胜返回0，白棋胜返回1，未出结果则为3
def is_win(board):
    for n in range(15):
        # 判断水平方向胜利
        flag = 0
        # flag是一个标签，表示是否有连续以上五个相同颜色的棋子
        for b in board:
            if b[n] == 1:
                flag += 1
                if flag == 5:
                    print('黑棋胜')
                    return 0
            else:
                # else表示此时没有连续相同的棋子，标签flag重置为0
                flag = 0

        flag = 0
        for b in board:
            if b[n] == 2:
                flag += 1
                if flag == 5:
                    print('白棋胜')
                    return 1
            else:
                flag = 0

        # 判断竖直方向胜利
        flag = 0
        for b in board[n]:
            if b == 1:
                flag += 1
                if flag == 5:
                    print('黑棋胜')
                    return 0
            else:
                flag = 0

        flag = 0
        for b in board[n]:
            if b == 2:
                flag += 1
                if flag == 5:
                    print('白棋胜')
                    return 1
            else:
                flag = 0

        # 判断正斜方向胜利

        for x in range(4, 25):
            flag = 0
            for i, b in enumerate(board):
                if 14 >= x - i >= 0 and b[x - i] == 1:
                    flag += 1
                    if flag == 5:
                        print('黑棋胜')
                        return 0
                else:
                    flag = 0

        for x in range(4, 25):
            flag = 0
            for i, b in enumerate(board):
                if 14 >= x - i >= 0 and b[x - i] == 2:
                    flag += 1
                    if flag == 5:
                        print('白棋胜')
                        return 1
                else:
                    flag = 0

        # 判断反斜方向胜利
        for x in range(11, -11, -1):
            flag = 0
            for i, b in enumerate(board):
                if 0 <= x + i <= 14 and b[x + i] == 1:
                    flag += 1
                    if flag == 5:
                        print('黑棋胜')
                        return 0
                else:
                    flag = 0

        for x in range(11, -11, -1):
            flag = 0
            for i, b in enumerate(board):
                if 0 <= x + i <= 14 and b[x + i] == 2:
                    flag += 1
                    if flag == 5:
                        print('白棋胜')
                        return 1
                else:
                    flag = 0

    return 3


# 取正则匹配的字符串
def parse_cmd(pattern, msg: str) -> list:
    return re.findall(pattern, msg, re.S)
