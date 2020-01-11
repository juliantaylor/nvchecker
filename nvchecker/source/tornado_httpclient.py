# MIT licensed
# Copyright (c) 2013-2020 lilydjwg <lilydjwg@gmail.com>, et al.

import json
from urllib.parse import urlencode

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPResponse
from tornado.httpclient import HTTPError

try:
  import pycurl
except ImportError:
  pycurl = None

from .httpclient import DEFAULT_USER_AGENT, ProxyObject

__all__ = ['session',
           'setup_session',
           'HTTPError',
           'NetworkErrors']

HTTP2_AVAILABLE = None if pycurl else False

def setup_session(proxy, concurrency):
  if pycurl:
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=concurrency)
  else:
    AsyncHTTPClient.configure("tornado.simple_httpclient.SimpleAsyncHTTPClient", max_clients=concurrency)

  session.set(Session(proxy))

def try_use_http2(curl):
  global HTTP2_AVAILABLE
  if HTTP2_AVAILABLE is None:
    try:
      curl.setopt(pycurl.HTTP_VERSION, 4)
      HTTP2_AVAILABLE = True
    except pycurl.error:
      HTTP2_AVAILABLE = False
  elif HTTP2_AVAILABLE:
    curl.setopt(pycurl.HTTP_VERSION, 4)

class Session:
  def __init__(self, proxy):
    self.client = AsyncHTTPClient()
    self.proxy = proxy

  def post(self, url, **kwargs):
    j = kwargs.pop('json', None)
    if j:
      kwargs['body'] = json.dumps(j)
    return self.get(url, method='POST', **kwargs)

  def get(self, url, **kwargs):
    kwargs['prepare_curl_callback'] = try_use_http2

    proxy = kwargs.pop('proxy', self.proxy)
    if proxy:
      host, port = proxy.rsplit(':', 1)
      kwargs['proxy_host'] = host
      kwargs['proxy_port'] = int(port)

    params = kwargs.get('params')
    if params:
      del kwargs['params']
      q = urlencode(params)
      url += '?' + q

    kwargs.setdefault("headers", {}).setdefault('User-Agent', DEFAULT_USER_AGENT)
    r = HTTPRequest(url, **kwargs)
    return ResponseManager(r, self.client)

class ResponseManager:
  def __init__(self, req, client):
    self.req = req
    self.client = client

  async def __aenter__(self):
    return await self.client.fetch(self.req)

  async def __aexit__(self, exc_type, exc, tb):
    pass

async def json_response(self, **kwargs):
  return json.loads(self.body.decode('utf-8'))

async def read(self):
  return self.body

HTTPResponse.json = json_response
HTTPResponse.read = read
session = ProxyObject()

NetworkErrors = ()
