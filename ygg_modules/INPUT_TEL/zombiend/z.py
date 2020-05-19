from collections import defaultdict
from functools import wraps
from itertools import chain
from typing import Iterable, List, Sequence, Callable, Dict, Tuple, Any, NewType
import abc
from os import listdir, path
from importlib import import_module
from .corpse import (Box, ChainBox2, dict2, z_builtins, PyModule, z_request_get, render_template,\
                     IBox)
from appserver.yggdrasil_branch import YggdrasilBranch
from .. import backend


TemplateFunc = NewType('TemplateFunc', Callable)


class CodeObject(abc.ABC):
  co_name: str
  co_argcount: int
  co_nlocals: int
  co_varnames: Tuple[str]
  co_cellvars:Tuple[str]
  co_freevars:Tuple[str]
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
  def __init__(self, *, import_name, **kwargs):
    name = import_name.split('.', 1)[0]
    template_folder = '../frontend'
    static_folder = "../static"
    super().__init__(
      name=name,
      import_name=import_name,
      template_folder=template_folder,
      static_folder=static_folder,
      **kwargs
      )
    z_scripts = self.scripts_load()
    z_points = self.endpoints_register(z_scripts)
    z_scripts = self.scripts_public_find(z_scripts)
    z_templates = self.templates_find()
    self.z_objects = Box(chain(z_scripts, z_templates), box_duplicates='error')
    backend.db_api.fetch_all = self.fetch_all
    return

  @staticmethod
  def scripts_load() -> List[PyModule]:
    rv = []
    dirs = backend.__path__
    for z_dir in dirs:
      script_names = (
        n[:-3] for n in listdir(z_dir)
        if n.endswith('.py') and path.isfile(path.join(z_dir, n))
        )
      for script_name in script_names:
        script_name = backend.__name__ + '.' + script_name
        z_module = import_module(script_name)
        setattr(z_module,'__builtins__', z_builtins)
        rv.append(z_module)
    return rv

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
        options=defaultdict(lambda : '', kwargs)
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

  def endpoints_register(self, z_scripts: Iterable[PyModule]) -> List[str]:
    rv = []
    for script in z_scripts:
      if not hasattr(script, '_endpoints'):
        continue
      endpoints: Iterable[str] = script._endpoints
      for endpoint in endpoints:
        self.endpoint_register(script, endpoint)
        rv.append(endpoint)
    return rv

  def endpoint_register(self, script: PyModule, endpoint_name: str) -> Callable:
    z_func = getattr(script, endpoint_name)
    view_func = self.z_func_to_view(z_func)
    self.add_url_rule(
      rule=endpoint_name,
      endpoint=endpoint_name,
      view_func=view_func,
      methods=['GET', 'POST']
      )
    return view_func

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
    with self.database.acquire(True) as tr :
      rows = tr.execute(sql, args, tr.ALL)
    rv = []
    for row in rows:
      rv.append(IBox(row))
    return rv


z: Module = Module(import_name=__name__)
