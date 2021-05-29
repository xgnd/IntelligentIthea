from pydantic import BaseSettings
import os

class Config(BaseSettings):
    round_times = 10
    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
    class Config:
        extra = "ignore"