from typing import Sequence, Mapping


def py_zope_cvt(z_json: Mapping) -> Sequence[str]:
  func_name = z_json['id']
  py_args = (x for x in ((z_json.get('_params', '') + '\ncontainer').split('\n')) if x)
  for s in (
    f'import datetime',
    f'def {func_name}({", ".join(py_args)}):',
    f'  context = container  # Auto generated string',
    f'  same_type = lambda o, t: isinstance(o, type(t))  # Auto generated string',
    f'  DateTime = datetime.datetime.now  # Auto generated string',
    ) :
    yield s
  for s in z_json['_body'].split('\n') :
    if s :
      s = '  ' + s
    yield s
  return