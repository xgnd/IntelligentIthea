import aiohttp
import asyncio
from json import loads
from random import choice


base_url = "http://i.itpk.cn/api.php"


def get_params(msg: str):
    return {
        "question": msg,
        "limit": 8,
        "api_key": "",
        "api_secret": ""
    }


async def get_message_reply(msg: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(url=base_url, params=get_params(msg)) as res:
            try:
                text = loads((await res.text()).encode("utf-8"))
                try:
                    return {"answer":text["content"]}
                except KeyError:
                    return 0
            except:
                ans = str(await res.text())
                return {"answer":ans}


if __name__ == '__main__':
    while(True):
        a = input()
        tasks = [
            asyncio.ensure_future(get_message_reply(a))
        ]
        loop = asyncio.get_event_loop()
        print(loop.run_until_complete(asyncio.wait(tasks)))