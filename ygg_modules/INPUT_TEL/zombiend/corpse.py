from typing import Sequence, Mapping, Any
import abc
import codecs
from collections import ChainMap, defaultdict
from flask import request as f_request, render_template, current_app
from box import Box

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

  def iterkeys(self):
    rv = self.keys()
    return rv

  def itervalues(self):
    rv = self.values()
    return rv


# noinspection PyPep8Naming
class str2(str):
  def encode(self, encoding='', errors='strict'):
    if encoding.casefold() in {'base64_codec', 'base64', 'base-64'}:
      rv = super().encode('cp1251', errors)
      rv = codecs.encode(rv, 'base64', errors)
      rv = rv.decode('cp1251', errors)
      rv = str2(rv)
    else:
      rv = super().encode(encoding or None, errors)
    return rv

  def decode(self, encoding='', errors='strict'):
    rv = self.encode('cp1251', errors)
    if encoding.casefold() in {'base64_codec', 'base64', 'base-64'}:
      rv = codecs.decode(rv, 'base64', errors)
      rv = rv.decode('cp1251', errors)
    else:
      rv = rv.decode(encoding or None, errors)
    rv = str2(rv)
    return rv

  def __mod__(self, other):
    rv = super().__mod__(other)
    rv = str2(rv)
    return rv

  def __add__(self, other):
    rv = super().__add__(other)
    rv = str2(rv)
    return rv

  def __getitem__(self, item):
    rv = super().__getitem__(item)
    rv = str2(rv)
    return rv


def z_request_get(y_module) -> ChainBox2:
  rv = ChainBox2(
    Box(),
    Box(
      RESPONSE=None,
      SESSION=y_module.heap,
      ),
    {k: str2(v) if isinstance(v, str) and not isinstance(v, str2) else v for k, v in f_request.values.items()},
    dict(
      uid=y_module.user.uid,
      headers=f_request.headers,  # TODO: restructure or remove base_layout
      ),
    defaultdict(lambda: '')
    )
  return rv


def j_is_none(x: Any) -> bool:
  rv = x is None
  return rv

z_builtins = dict(
  globals=globals,
  locals=locals,
  dict=dict2,
  len=len,
  str=str2,
  )