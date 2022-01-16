import os
from PIL import Image


route = os.path.join(os.getcwd(), "七星")   # 需要制作哪个头像就换成相应文件夹

img = os.listdir(route)


def avatar():
    """ 在image中的“头像”文件夹中运行，同时将image文件夹中的白.png复制到运行目录 """
    white = Image.open("白.png")
    white.resize((19, 19))

    for image in img:
        new_img = Image.open(os.path.join(route, image))

        new_img = new_img.resize((79, 79))

        new_img.paste(white, (60, 60))

        new_img.save(os.path.join(route, image))


def grey_avatar():
    """ 在image中的“灰头像”文件夹中运行 """
    for image in img:
        new_img = Image.open(os.path.join(route, image)).convert('L')

        new_img = new_img.resize((79, 79))

        new_img.save(os.path.join(route, image))
avatar()
# grey_avatar()