# -*- coding: utf-8 -*-

from collections import defaultdict
from functools import wraps
from itertools import chain
from typing import Iterable, List, Sequence, Callable, Dict, Tuple, Any, NewType
import abc
from os import listdir, path, scandir
from importlib import import_module
from .corpse import (Box, ChainBox2, dict2, z_builtins, PyModule, z_request_get, render_template,
  current_app, IBox, j_is_none, package_dir_get)
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


INTERFACE_NAME = __name__.split('.', 1)[0]

Z_SCRIPT_PKG = INTERFACE_NAME + '.backend'

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
    self.containers = Z_Containers()
    self.backend_walk()
    self.z_objects = Box(chain(z_scripts, z_templates), box_duplicates='error')
    backend.db_api.fetch_all = self.fetch_all
    self.config.EXPLAIN_TEMPLATE_LOADING = True
    current_app.jinja_env.tests['None'] = j_is_none
    return

  def backend_walk(self, dir):
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
    container = self.containers.get(py_path)
    module = import_module('.'.join(py_path))
    module.fetch_all = self.fetch_all
    container.register(module, skip='fetch_all')
    # for name, obj in module.__dict__:
    #   if callable(obj):
    #     container.add([name, obj])

  def endpoints_register(self, py_path):
    container = self.containers.get(py_path)
    module = import_module('.'.join(py_path))
    endpoints: Iterable[str] = getattr(module, '_endpoints', set())
    container.callables_register(module, skip=endpoints)
    for endpoint in endpoints:
      self.endpoint_register(getattr(module, endpoint), py_path)
    return

  def endpoint_register(self, z_func, py_path) -> Callable:
    return
    view_func = self.z_func_to_view(z_func)
    self.add_url_rule(
      rule=endpoint_name,
      endpoint=endpoint_name,
      view_func=view_func,
      methods=['GET', 'POST']
      )
    return view_func


  def templates_find(self) -> List[Tuple[str, TemplateFunc]]:
    rv = []
    dirs = (path.join( path.dirname(p), 'frontend', self.name) for p in backend.__path__)
    for t_dir in dirs:
      template_names = (
        n[:-5] for n in listdir(t_dir)
        if n.endswith('.html') and path.isfile(path.join(t_dir, n))
        )
      for template_name in template_names:
        template = self.import_template(template_name)
        rv.append((template_name,template))
    return rv

  def import_template(self, template_name: str) -> TemplateFunc:
    z_here = dict2(
      getUserName=lambda uid: self.user.shortname,
      title='Title not implemented yet',
      )
    template_name = self.name+'/'+template_name+'.html'

    def render_func(**kwargs) -> str:
      rv = render_template(
        template_name,
        request=kwargs.pop('request', z_request_get(self)),
        container=kwargs.pop('container', self.z_container_get()),
        here=kwargs.pop('here', z_here),
        len=kwargs.pop('len', z_builtins['len']),
        options=defaultdict(lambda : '', kwargs),
        )
      return rv
    return render_func

  @staticmethod
  def scripts_public_find(scripts: Sequence[PyModule]) -> Iterable[Tuple[str, Any]]:
    def script_public_find(s: PyModule) -> Iterable[Tuple[str, Any]]:
      SKIP_LIST=('__name__ __doc__ __package__ __loader__ __spec__ __file__ __cached__ '
        '__builtins__ _endpoints'.split(' '))
      for p_name, p_obj in s.__dict__.items():
        if p_name in SKIP_LIST:
          continue
        yield (p_name, p_obj)
      return

    for s in scripts:
      yield from script_public_find(s)
    return


  def z_func_to_view(self, z_func: Callable) -> Callable:
    @wraps(z_func)
    def _z_wrapper():
      g = self.z_globals_get()
      l = self.z_locals_get(code_obj)
      g.update(l)
      # noinspection PyTypeChecker
      rv = eval(code_obj, g)
      return rv

    # noinspection PyUnresolvedReferences
    code_obj: CodeObject = z_func.__code__
    return _z_wrapper

  def z_container_get(self):
    def z_isInteger(v):
      rv = isinstance(v, int)
      return rv

    z_req = z_request_get(self)
    container = ChainBox2(self.z_objects, Box(REQUEST=z_req, isInteger=z_isInteger))
    return container

  def z_globals_get(self) -> Dict[str, Any]:
    container = self.z_container_get()
    rv = dict(
      __builtins__=z_builtins,
      container=container,
      context=container,
      )
    return rv

  def z_locals_get(self, code_obj: CodeObject) -> Dict[str, Any]:
    rv = dict(
      )
    return rv

  def fetch_all(self, sql, *args):
    with self.database.acquire(True) as tr:
      rows = tr.execute(sql, args, tr.ALL)
    rv = []
    for row in rows:
      rv.append(IBox(row))
    return rv
