from typing import Sequence, Mapping, Any
from box import Box
import abc
from collections import ChainMap, defaultdict
from flask import request as f_request, render_template

class PyModule(abc.ABC):
  _endpoints: Sequence[str]


class IBox(Box):
  """case insensitive dict"""

  def __getitem__(self, item, *args, **kwargs):
    if isinstance(item, str):
      item = item.casefold()
    rv = super().__getitem__(item, *args, **kwargs)
    return rv

  def __setitem__(self, key, value):
    if isinstance(key, str):
      key = key.casefold()
    rv = super().__setitem__(key, value)
    return rv

  def __delitem__(self, key):
    if isinstance(key, str):
      key = key.casefold()
    rv = super().__delitem__(key)
    return rv

  def __contains__(self, item):
    if isinstance(item, str):
      item = item.casefold()
    rv = super().__contains__(item)
    return rv


class ChainBox(ChainMap):
  def __getattr__(self, item):
    if item == 'maps':
      rv = self.__dict__[item]
    else:
      rv = self[item]
    return rv

  def __setattr__(self, key, value):
    if key == 'maps':
      self.__dict__[key] = value
    else:
      self[key] = value
    return

  def __delattr__(self, item):
    del self[item]


class ChainBox2(ChainBox):
  def has_key(self, key):
    rv = key in self
    return rv

  def iteritems(self):
    rv = self.items()
    return rv


class dict2(dict):
  def has_key(self, key):
    rv = key in self
    return rv

  def iteritems(self):
    rv = self.items()
    return rv


def z_request_get(y_module) -> Box:
  rv = ChainBox2(
    Box(),
    Box(
      RESPONSE=None,
      SESSION=y_module.heap,
      ),
    f_request.values,
    dict(
      uid=y_module.user.uid,
      headers=f_request.headers,  # TODO: restructure or remove base_layout
      ),
    defaultdict(lambda : '')
    )
  return rv


z_builtins = dict(
  globals=globals,
  locals=locals,
  dict=dict2,
  len=len,
  )