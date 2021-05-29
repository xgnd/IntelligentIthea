from pydantic import BaseSettings


class Config(BaseSettings):
    server_status_cpu: bool = True
    server_status_per_cpu: bool = False
    server_status_memory: bool = True
    server_status_disk: bool = True

    class Config:
        extra = "ignore"