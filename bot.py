#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import nonebot
from nonebot.adapters.onebot.v11 import Adapter
# Custom your logger
from nonebot.log import logger, default_format

logger.add("error.log",
           rotation="00:00",
           diagnose=False,
           level="ERROR",
           format=default_format)

# You can pass some keyword args config to init function
nonebot.init()
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

nonebot.load_plugins("ithea/plugins")
# nonebot.load_plugin("chtholly.plugins.nonebot_plugin_simdraw")
# Modify some config / config depends on loaded configs

# config = driver.config
# do something...

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
