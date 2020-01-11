# MIT licensed
# Copyright (c) 2020 lilydjwg <lilydjwg@gmail.com>, et al.

import atexit
from typing import Optional
import json

import httpx

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

NetworkErrors = (
  httpx.exceptions.NetworkError,
  httpx.exceptions.ConnectTimeout,
)

class Response:
  def __init__(self, r: httpx.Response) -> None:
    self.r = r

  async def json(self, content_type=None):
    data = await self.r.aread()
    return json.loads(data)

  async def read(self):
    return await self.r.aread()

  def __getattr__(self, name):
    return getattr(self.r, name)

class ResponseManager:
  def __init__(self, client, args, kwargs) -> None:
    self.client = client
    self.args = args
    self.kwargs = kwargs

  async def __aenter__(self) -> Response:
    try:
      r = await self.client.get(
        *self.args, **self.kwargs)
      if r.status_code >= 400:
        raise HTTPError(
          r.status_code,
          r.reason_phrase,
          r,
        )
      return Response(r)

    except NetworkErrors:
      raise
    except httpx.HTTPError as e:
      raise HTTPError(
        e.response.status_code,
        e.response.reason_phrase,
        e.response,
      )

  async def __aexit__(self, exc_type, exc, tb):
    pass

class Session:
  def __init__(self, client: httpx.AsyncClient, concurrency: int) -> None:
    self.clients = {None: client}
    self.concurrency = concurrency

  def get(self, *args, **kwargs) -> ResponseManager:
    proxy = kwargs.pop('proxy', None)
    client = self.clients.get(proxy)
    if not client:
      client = httpx.AsyncClient(
        pool_limits = httpx.PoolLimits(
          soft_limit = self.concurrency * 2,
          hard_limit = self.concurrency,
        ),
        timeout = httpx.Timeout(20, pool_timeout=None),
        headers = {'User-Agent': DEFAULT_USER_AGENT},
        http2 = True,
        proxies = proxy,
      )
      self.clients[proxy] = client
    return ResponseManager(client, args, kwargs)

  async def aclose(self):
    for client in self.clients.values():
      await client.aclose()
    del self.clients

session = ProxyObject()

def setup_session(proxy: Optional[str], concurrency: int):
  s = httpx.AsyncClient(
    pool_limits = httpx.PoolLimits(
      soft_limit = concurrency * 2,
      hard_limit = concurrency,
    ),
    timeout = httpx.Timeout(20, pool_timeout=None),
    headers = {'User-Agent': DEFAULT_USER_AGENT},
    http2 = True,
    proxies = proxy,
  )
  session.set(Session(s, concurrency))

@atexit.register
def cleanup():
  import asyncio
  loop = asyncio.get_event_loop()
  loop.run_until_complete(session.aclose())
