from pydantic import BaseSettings
import os

class Config(BaseSettings):
    class Config:
        extra = "ignore"