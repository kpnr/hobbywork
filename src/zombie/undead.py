# -*- coding: utf-8 -*-

from collections import defaultdict
from functools import wraps
from itertools import chain
from typing import Iterable, List, Sequence, Callable, Dict, Tuple, Any, NewType
import abc
from os import listdir, path, scandir
from importlib import import_module
from .corpse import (Box, ChainBox2, dict2, z_builtins, PyModule, z_request_get, render_template,
  current_app, IBox, j_is_none, package_dir_get, ZContainers)
from appserver.yggdrasil_branch import YggdrasilBranch


TemplateFunc = NewType('TemplateFunc', Callable)


class CodeObject(abc.ABC):
  co_name: str
  co_argcount: int
  co_nlocals: int
  co_varnames: Tuple[str]
  co_cellvars: Tuple[str]
  co_freevars: Tuple[str]
  co_code: bytes
  co_consts: Tuple
  co_names: Tuple[str]
  co_filename: str
  co_firstlineno: int
  co_lnotab: bytes
  co_stacksize: int
  co_flags: int


class Module(YggdrasilBranch):
  def __init__(self, *, package_name):
    template_folder = './frontend'
    static_folder = "./static"
    super().__init__(
      name=package_name,
      import_name=package_name,
      template_folder=template_folder,
      static_folder=static_folder,
      )
    self.containers = ZContainers()
    self.backend_walk()
    self.frontend_walk()
    self.config.EXPLAIN_TEMPLATE_LOADING = True
    current_app.jinja_env.tests['None'] = j_is_none
    return

  def backend_walk(self):
    def dir_walk(fs_dirs, py_dirs):
      for node in scandir(path.join(*fs_dirs)):
        if node.is_file():
          if node.name == 'db_api.py':
            self.db_api_register(py_dirs+['db_api'])
          elif node.name.endswith('.py'):
            self.endpoints_register(py_dirs+[node.name[:-3]])
          else:
            breakpoint()
            raise NotImplementedError('Unknown file type in backend dir')
        elif node.is_dir():
          dir_walk(fs_dirs+[node.name], py_dirs+[node.name])
        else:
          breakpoint()
          raise NotImplementedError('Unknown fs object in backend dir')
      return

    py_path = [self.name, 'backend']
    package_dir = package_dir_get(self.name)
    dir_walk([package_dir, 'backend'], py_path)
    return

  def db_api_register(self, py_path):
    manager = self.containers.manager_get(py_path)
    module = import_module('.'.join(py_path))
    module.fetch_all = self.fetch_all
    manager.register_module(module, skip='fetch_all')

  def endpoints_register(self, py_path):
    def endpoint_register(z_func, py_path) -> None :
      view_func = self.z_func_to_ygg_func(z_func, py_path)
      z_path = [''] + self.containers.py_path_to_z(py_path)[1:] + [z_func.__name__]
      self.add_url_rule(
        rule='/'.join(z_path),
        endpoint='_'.join(z_path),
        view_func=view_func,
        methods=['GET', 'POST']
        )
      manager.register_symbol(z_func.__name__, view_func)
      return

    manager = self.containers.manager_get(py_path[:-1])
    module = import_module('.'.join(py_path))
    endpoints: Sequence[str] = getattr(module, '_endpoints', set())
    if 1 < len(endpoints):
      raise NotImplementedError('Multi endpoint module')
    manager.register_module(module, skip=endpoints)
    for endpoint in endpoints:
      endpoint_register(getattr(module, endpoint), py_path[:-1])
    return

  def z_func_to_ygg_func(self, z_func: Callable, py_path) -> Callable:
    @wraps(z_func)
    def _z_wrapper():
      permanent = self.z_globals_get(py_path)
      transient = self.view_locals_get()
      g = ChainBox2(permanent, transient)
      # noinspection PyTypeChecker
      rv = eval(code_obj, g)
      return rv

    py_path = py_path.copy()
    # noinspection PyUnresolvedReferences
    code_obj: CodeObject = z_func.__code__
    return _z_wrapper

  def view_locals_get(self) -> Dict[str, Any]:
    rv = dict(
      )
    return rv

  def frontend_walk(self):
    def dir_walk(fs_dirs, py_dirs):
      for node in scandir(path.join(*fs_dirs)):
        if node.is_file():
          if node.name.endswith('.html'):
            self.template_register(py_dirs+[node.name[:-5]])
          else:
            breakpoint()
            raise NotImplementedError('Unknown file type in backend dir')
        elif node.is_dir():
          dir_walk(fs_dirs+[node.name], py_dirs+[node.name])
        else:
          breakpoint()
          raise NotImplementedError('Unknown fs object in frontend dir')
      return
    py_path = [self.name, 'frontend']
    package_dir = package_dir_get(self.name)
    dir_walk([package_dir, 'frontend'], py_path)
    return

  def template_register(self, py_path) -> TemplateFunc:
    py_path = py_path.copy()
    z_path = self.containers.py_path_to_z(py_path)
    template_name = '/'.join(z_path) + '.html'

    def render_func(**kwargs) -> str:
      arg_replacement = (
        ('request', lambda : z_request_get(self)),
        ('container', lambda : self.containers.py_path_to_container(py_path)),
        ('here', lambda : dict2(
            getUserName=lambda uid : self.user.shortname,
            title='Title not implemented yet',
            )
          ),
        ('len', lambda : z_builtins['len']),
        ('options', lambda : dict2(kwargs)),
        )
      template_args = dict2()
      for k, v in arg_replacement:
        a = kwargs.pop(k, None)
        if a is None:
          a = v()
        template_args.update((k, a))
      rv = render_template(
        template_name,
        **template_args,
        )
      return rv
    return render_func

  def z_container_get(self):
    def z_isInteger(v):
      rv = isinstance(v, int)
      return rv

    z_req = z_request_get(self)
    container = ChainBox2(self.z_objects, Box(REQUEST=z_req, isInteger=z_isInteger))
    return container

  def z_globals_get(self, py_path) -> Dict[str, Any]:
    container = self.containers.py_path_to_container(py_path)
    rv = dict(
      __builtins__=z_builtins,
      container=container,
      context=container,
      )
    return rv

  def fetch_all(self, sql, *args):
    with self.database.acquire(True) as tr:
      rows = tr.execute(sql, args, tr.ALL)
    rv = []
    for row in rows:
      rv.append(IBox(row))
    return rv
