# -*- coding: utf-8 -*-

from typing import Sequence, Mapping, Any
import sys
import os
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


class ZContainers(object):
  class Manager(object):
    def __init__(self, container):
      super().__init__()
      self._container = container
      return

    def register_module(self, py_module, *, skip=frozenset()):
      SKIP_LIST=frozenset('__name__ __doc__ __package__ __loader__ __spec__ __file__ __cached__ '
        '__builtins__ _endpoints'.split(' '))
      SKIP_LIST = SKIP_LIST | skip
      for name, obj in py_module.__dict__.items():
        if name in SKIP_LIST:
          continue
        if callable(obj):
          self._container[name] = obj
      return

    def register_symbol(self, name, value):
      self._container[name] = value
      return

  @staticmethod
  def py_path_to_z(py_path):
    if not py_path:
      rv = []
    if py_path[1] == 'backend':
      rv = py_path[0:1] + py_path[2:]
    elif py_path[1] == 'frontend':
      rv = py_path[2:]
    else:
      breakpoint()
      raise ValueError('Invalid py_path %s' % py_path)
    return rv

  def __init__(self):
    super().__init__()
    self._root = dict2(__container=dict2())
    return

  def manager_get(self, py_path):
    c = self.py_path_to_sub_container(py_path)
    m = self.Manager(c)
    return m

  def py_path_to_sub_container(self, py_path):
    z_path = self.py_path_to_z(py_path)
    r = self._root
    for sub_name in z_path:
      r = r.setdefault(sub_name, dict2(__container=dict2()))
    rv = r['__container']
    return rv

  def py_path_to_container(self, py_path):
    z_path = self.py_path_to_z(py_path)
    def g_sub_container():
      r = self._root
      for sub_name in z_path:
        yield r['__container']
        r = r.setdefault(sub_name, dict2(__container=dict2()))
      yield r['__container']
      return
    rv = ChainBox2(*g_sub_container())
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


def package_dir_get(package_name: str) -> str:
  backend_dir = sys.modules[package_name].__file__
  backend_dir = os.path.abspath(os.path.dirname(backend_dir))
  return backend_dir


def z_request_get(y_module) -> ChainBox2:
  rv = ChainBox2(
    Box(),
    Box(
      RESPONSE=None,
      SESSION=y_module.heap,
      ),
    {k: str2(v) if isinstance(v, str) and not isinstance(v, str2) else v for k, v in f_request.values.items()},
    dict2(
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