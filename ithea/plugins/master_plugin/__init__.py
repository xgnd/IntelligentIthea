from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters import Bot, Event
from nonebot.permission import SUPERUSER
from nonebot import get_driver, get_bots, on_startswith, require
import os
import json

from .config import Config
from .data_source import *
driver = get_driver()
global_config = get_driver().config
status_config = Config(**global_config.dict())


menu = on_startswith("操作菜单", permission=SUPERUSER, priority=2, block=True)


@menu.handle()
async def menu_handler(bot: Bot, event: Event):
    if str(event.get_message()) == "操作菜单" and event.group_id == 368227266:
        msg = "◇━━操作菜单（超管专用）━━◇" + "\n" + "状态" + "\n" + "重启" + "\n" + "修改"
        await menu.finish(msg)


status = on_startswith("状态", permission=SUPERUSER, priority=2, block=True)


@status.handle()
async def server_status(bot: Bot, event: Event):
    if str(event.get_message()) == "状态" and event.group_id == 368227266:
        data = []

        if status_config.server_status_cpu:
            if status_config.server_status_per_cpu:
                data.append("CPU:")
                for index, per_cpu in enumerate(per_cpu_status()):
                    data.append(f"  core{index + 1}: {int(per_cpu):02d}%")
            else:
                data.append(f"CPU: {int(cpu_status()):02d}%")

        if status_config.server_status_memory:
            data.append(f"内存: {int(memory_status()):02d}%")

        if status_config.server_status_disk:
            data.append("磁盘:")
            for k, v in disk_usage().items():
                data.append(f"  {k}: {int(v.percent):02d}%")

        await status.send(message="\n".join(data))


restart = on_startswith("重启", permission=SUPERUSER, priority=2, block=True)


@restart.handle()
async def restart(bot: Bot, event: Event):
    if str(event.get_message()) == "重启" and event.group_id == 368227266:
        with open(os.path.join(os.getcwd(), "ithea", "plugins", "master_plugin", "data.json"), 'w', encoding='utf-8') as f:
            f.write(json.dumps({"restart": True}, ensure_ascii=False))
            f.close()
        await bot.call_api("send_group_msg", group_id=368227266, message="正在重启...")
        os.system(os.path.join(os.getcwd(), "restart.bat"))
        os._exit(0)


@driver.on_bot_connect
async def res(bot: Bot):
    with open(os.path.join(os.getcwd(), "ithea", "plugins", "master_plugin", "data.json"), 'r', encoding='utf-8-sig') as f:
        restart = json.load(f)["restart"]
        f.close()
    if restart == True:
        # bot = list(get_bots().values())[0]
        with open(os.path.join(os.getcwd(), "ithea", "plugins", "master_plugin", "data.json"), 'w', encoding='utf-8') as f:
            f.write(json.dumps({"restart": False}, ensure_ascii=False))
            f.close()
        await bot.call_api("send_group_msg", group_id=368227266, message="重启成功！")


with open(os.path.join(os.path.join(os.getcwd(), "data", "plugin"), "config.json"), 'r', encoding='utf-8-sig') as f:   # 读入角色数据
    data = json.load(f)
    f.close()

modify_dict = data["rules"]["settings"]
modify_dict["名字"] = data["number"]
modify_dict["概率"] = {"抽卡概率":data["rules"]["weights"]["draw"],"合成概率":{"普通":data["rules"]["weights"]["compose"]["grade_3"],"稀有":data["rules"]["weights"]["compose"]["grade_2"],"超稀有":data["rules"]["weights"]["compose"]["grade_1"]}}


modify = on_startswith("修改", permission=SUPERUSER, priority=2, block=True)

@modify.handle()
async def server_status(bot: Bot, event: Event):
    if str(event.get_message()) == "修改" and event.group_id == 368227266:
        msg = "◇━━修改（超管专用）━━◇" + "\n"
        for i in modify_dict.keys():
            if type(modify_dict[i]) != dict:
                msg+=i+"："+str(modify_dict[i])+"\n"
            else:
                msg+=i+"\n"
        msg += "------------------------------\n" + "若选项后有参数，则输入“修改”+[以上选项]+[欲修改为的内容]可以直接修改" + "\n" + "若选项后没有参数，则输入“修改”+以上选项可以进入下一层再修改，此时应输入“修改”+[该层名称]+[以上选项]+[欲修改为的内容]" + "\n" + "依此类推..." + "注：输入时各项间需加空格，仅在该群修改有。请慎重修改，修改后参数将无法找回！！！修改后务必重启，否则修改将不会生效！！！"
        await modify.finish(msg)
    args = str(event.get_message()).strip()[2:].strip().split(" ")
    print(args)
    if args:
        d = modify_dict
        for i in args:
            print(i)
            if i in d.keys():
                if type(d[i]) == dict and args.index(i) == len(args) - 1:
                    msg = "◇━━修改（超管专用）━━◇" + "\n"
                    for j in d[i].keys():
                        if type(d[i][j]) != dict:
                            msg+=j+"："+str(d[i][j])+"\n"
                        else:
                            msg+=j+"\n"
                    await modify.send(msg)
                elif args.index(i) == len(args) - 2:
                    # 转换一下类型，与原值的类型统一
                    if type(d[i]) == float:
                        args[-1] = float(args[-1])
                    if type(d[i]) == int:
                        args[-1] = int(args[-1])
                    if type(d[i]) == str:
                        args[-1] = str(args[-1])
                    # print(modify_dict)
                    print(d[i],args[-1])
                    replace_value(modify_dict,d[i],args[-1])
                    # print(modify_dict)
                    d = modify_dict
                    with open(os.path.join(os.path.join(os.getcwd(), "data", "plugin"), "config.json"), 'w', encoding='utf-8') as f:
                        name = d.pop("名字")
                        data["number"] = name
                        weights = d.pop("概率")
                        draw = weights.pop("抽卡概率")
                        data["rules"]["weights"]["draw"] = draw
                        compose=weights.pop("合成概率")
                        data["rules"]["weights"]["compose"]["grade_3"] = compose.pop("普通")
                        data["rules"]["weights"]["compose"]["grade_2"] = compose.pop("稀有")
                        data["rules"]["weights"]["compose"]["grade_1"] = compose.pop("超稀有")

                        data["rules"]["settings"] = modify_dict
                        
                        f.write(json.dumps(data, ensure_ascii=False))
                        f.close()
                    await modify.finish("修改成功！请立即重启")
                elif args.index(i) == len(args) - 1:
                    await modify.finish("“"+i+"”"+"请加上欲修改为的内容")
                d = d[i]
            else:
                await modify.finish("“"+i+"”"+"该选项不存在")
            

scheduler_clean = require("nonebot_plugin_apscheduler").scheduler


@scheduler_clean.scheduled_job('cron', day='*/1', id="clean")
async def clean():
    clean_cache()
    print("已定时清除缓存图片")
