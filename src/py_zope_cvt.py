from typing import Mapping, Generator


def py_zope_cvt(z_json: Mapping) -> Generator[str, None, None]:
  func_name = z_json['id']
  py_args = [x for x in ((z_json.get('_params', '')).split('\n')) if x]
  yield 'import datetime'
  yield ''
  if not py_args:
    s = f'["{func_name}"]'
  else:
    s = ''
  yield f'_endpoints = set({s})'
  for s in (
    '', ''
    f'def {func_name}({", ".join(py_args)}):',
    # f'  context = container  # Auto generated string',
    # f'  same_type = lambda o, t: isinstance(o, type(t))  # Auto generated string',
    # f'  DateTime = datetime.datetime.now  # Auto generated string',
    ) :
    yield s
  for s in z_json['_body'].split('\n'):
    if s :
      s = '  ' + s
    yield s
  yield ''
  # if not py_args:
  #   for s in (
  #     '',
  #     f'__rv = {func_name}()',
  #     '',
  #     ):
  #     yield s
  return
