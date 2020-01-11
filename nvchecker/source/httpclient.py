# MIT licensed
# Copyright (c) 2019 lilydjwg <lilydjwg@gmail.com>, et al.

from .. import __version__

DEFAULT_USER_AGENT = 'lilydjwg/nvchecker %s' % __version__

class ProxyObject:
  obj = None

  def __getattr__(self, name):
    return getattr(self.obj, name)

  def __setattr__(self, name, value):
    return setattr(self.obj, name, value)

  def set(self, obj):
    super().__setattr__('obj', obj)
