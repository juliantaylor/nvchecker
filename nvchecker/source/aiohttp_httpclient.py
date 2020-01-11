# MIT licensed
# Copyright (c) 2013-2017 lilydjwg <lilydjwg@gmail.com>, et al.

import atexit
import asyncio
import aiohttp
from .httpclient import DEFAULT_USER_AGENT, ProxyObject

__all__ = ['session',
           'setup_session',
           'HTTPError',
           'NetworkErrors']

class HTTPError(Exception):
    def __init__(self, code, message, response):
        self.code = code
        self.message = message
        self.response = response

class BetterClientSession(aiohttp.ClientSession):
    def __init__(self, *args, **kwargs):
        self.proxy = kwargs.pop('proxy', None)
        super().__init__(*args, **kwargs)

    async def _request(self, *args, **kwargs):
        kwargs.setdefault("proxy", self.proxy)
        kwargs.setdefault("headers", {}).setdefault('User-Agent', DEFAULT_USER_AGENT)

        res = await super(BetterClientSession, self)._request(
            *args, **kwargs)
        if res.status >= 400:
            raise HTTPError(res.status, res.reason, res)
        return res

session = ProxyObject()

def setup_session(proxy, concurrency):
    connector = aiohttp.TCPConnector(limit=concurrency)
    session.set(BetterClientSession(
        proxy = proxy,
        trust_env = True,
        connector = connector,
        timeout = aiohttp.ClientTimeout(total=20),
    ))

@atexit.register
def cleanup():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(session.close())

NetworkErrors = (
    asyncio.TimeoutError,
    aiohttp.ClientConnectorError,
)
