# -*- coding: utf-8 -*-
from typing import Mapping, Generator
from ast import parse as py_parse
import astor

def py_zope_patch(src):
  ast = py_parse(src, 'zope_script_file.py', 'exec')
  dst = astor.to_source(ast)
  return dst

def py_zope_cvt(z_json: Mapping) -> Generator[str, None, None]:
  func_name = z_json['id']
  py_args = [x for x in ((z_json.get('_params', '')).split('\n')) if x]
  yield '# -*- coding: utf-8 -*-'
  if not py_args:
    s = f'["{func_name}"]'
  else:
    s = ''
  yield f'_endpoints = set({s})'
  for s in (
    '', ''
    f'def {func_name}({", ".join(py_args)}):',
    ) :
    yield s
  body = py_zope_patch(z_json['_body'])
  for s in body.split('\n'):
    if s :
      s = ' '*4 + s
    yield s
  if s:
    yield ''
  return
