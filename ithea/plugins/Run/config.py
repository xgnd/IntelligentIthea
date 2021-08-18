from pydantic import BaseSettings
import os


class Config(BaseSettings):
    CD = 5
    ROAD = '='
    ROADLENGTH = 16
    TOTAL_NUMBER = 10
    NUMBER = 5
    ONE_TURN_TIME = 3
    SUPPORT_TIME = 30
    data_path:str = os.path.join(os.path.abspath(os.path.dirname(os.getcwd())),"global_data","Run")   # 取插件数据路径
    RUN_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(os.getcwd())),"global_data","data", "plugin", "global_data.json")

    # 如果此项为True，则技能由图片形式发送，减少风控。
    SKILL_IMAGE = False

    class Config:
        extra = "ignore"
