# MIT licensed
# Copyright (c) 2017 Felix Yan <felixonmars@archlinux.org>, et al.

import sys

import pytest
pytestmark = [
  pytest.mark.asyncio,
  pytest.mark.skipif('nvchecker.source.aiohttp_httpclient' not in sys.modules,
                     reason='aiohttp not chosen'),
]

async def test_proxy(get_version, monkeypatch):
  from nvchecker.source import session
  import aiohttp

  async def fake_request(*args, **kwargs):
    proxy = kwargs.pop('proxy')

    class fake_response():
      status = 200

      async def read():
        return proxy.encode("ascii")

      def release():
        pass

    return fake_response

  monkeypatch.setattr(session, "proxy", "255.255.255.255:65535", raising=False)
  monkeypatch.setattr(aiohttp.ClientSession, "_request", fake_request)

  assert await get_version("example", {"regex": "(.+)", "url": "deadbeef"}) == "255.255.255.255:65535"
  assert await get_version("example", {"regex": "(.+)", "url": "deadbeef", "proxy": "0.0.0.0:0"}) == "0.0.0.0:0"
