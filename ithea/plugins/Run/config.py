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
    RUN_DB_PATH = os.path.join(os.getcwd(), "data", "plugin","global_data.json")
    FILE_PATH = os.path.dirname(__file__)
    #如果此项为True，则技能由图片形式发送，减少风控。
    SKILL_IMAGE = False
    class Config:
        extra = "ignore"