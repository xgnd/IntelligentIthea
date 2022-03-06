import json
import os
import random
import re
import time

import requests  # 导入网页请求库
from bs4 import BeautifulSoup  # 导入网页解析库
from nonebot.adapters.onebot.v11 import MessageSegment
from PIL import Image, ImageDraw, ImageFont

project_path = os.path.dirname(os.path.abspath(__file__))


session = requests.Session()
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


async def get_lib_status() -> str:
    url = 'https://img.sukasuka.cn/api/info'
    content = session.get(url, headers=headers)
    return json.loads(content.content)


async def get_random_pic() -> str:
    stat = await get_lib_status()
    counts = stat['postCount']
    url = 'https://img.sukasuka.cn/api/post/'+str(random.randint(0, counts))
    response = session.get(url, headers=headers)
    if str(response) == '<Response [200]>':
        return json.loads(response.content)
    else:
        url = 'https://img.sukasuka.cn/api/post/' + \
            str(random.randint(0, counts))
        response = session.get(url, headers=headers)
        if str(response) == '<Response [200]>':
            return json.loads(response.content)
        else:
            url = 'https://img.sukasuka.cn/api/post/' + \
                str(random.randint(0, counts))
            response = session.get(url, headers=headers, verify=False)
            if str(response) == '<Response [200]>':
                return json.loads(response.content)
            else:
                return "error"


async def get_pic_by_id(post_id: str) -> str:
    url = 'http://img.sukasuka.cn/api/post/'+post_id
    response = session.get(url, headers=headers)
    if str(response) == '<Response [200]>':
        return json.loads(response.content)
    else:
        return "-1"


async def get_dialogue():
    data_path = os.path.join(project_path, 'dialogue.json')
    with open(data_path, 'r', encoding='utf-8-sig') as f:
        dialogue_list = json.load(f)["word"]
        dialogue = random.choice(dialogue_list)
        return dialogue


def pic_compose(text):
    if text == "birthday_table.png" or text == "Ithea_card.jpg":
        save_route = "file:///"+project_path+"/"+text
        image = MessageSegment.image(file=save_route)
        return image
    print(text)

    output_str = text
    output_str = line_break(output_str)
    d_font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', CHAR_SIZE)
    lines = output_str.count('\n')  # 计算行数

    image = Image.new("L", (LINE_CHAR_COUNT*(CHAR_SIZE+1) //
                            2, (CHAR_SIZE+8)*lines), "white")
    draw_table = ImageDraw.Draw(im=image)
    draw_table.text(xy=(0, 0), text=output_str,
                    fill='#000000', font=d_font, spacing=4)

    save_route = project_path+"/kepu.png"
    image.save(save_route, 'PNG')  # 保存在当前路径下，格式为PNG
    image.close()
    save_route = "file:///"+save_route
    image = MessageSegment.image(file=save_route)
    return image


async def get_kepu():

    data_path = os.path.join(project_path, 'data.json')
    with open(data_path, 'r', encoding='utf-8-sig') as f:
        data_list = json.load(f)["word"]
        data = random.choice(data_list)
        pic = pic_compose(data)
        return pic


LINE_CHAR_COUNT = 60  # 每行字符数：30个中文字符(=60英文字符)
CHAR_SIZE = 30
TABLE_WIDTH = 4


def line_break(line):
    ret = ''
    width = 0
    for c in line:
        if len(c.encode('utf8')) == 3:  # 中文
            if LINE_CHAR_COUNT == width + 1:  # 剩余位置不够一个汉字
                width = 2
                ret += '\n' + c
            else:  # 中文宽度加2，注意换行边界
                width += 2
                ret += c
        else:
            if c == '\t':
                space_c = TABLE_WIDTH - width % TABLE_WIDTH  # 已有长度对TABLE_WIDTH取余
                ret += ' ' * space_c
                width += space_c
            elif c == '\n':
                width = 0
                ret += c
            else:
                width += 1
                ret += c
        if width >= LINE_CHAR_COUNT:
            ret += '\n'
            width = 0
    if ret.endswith('\n'):
        return ret
    return ret + '\n'
