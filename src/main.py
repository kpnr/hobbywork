import argparse
import json
import re
from gettext import gettext as _
from dataclasses import dataclass
from os import path, scandir, makedirs
from typing import NewType, Optional, Set, List
from sql_zope_cvt import SqlZopeDef


DirPath = NewType('DirPath', str)


@dataclass(frozen=True)
class Settings(object):
  source_dir: DirPath
  destination_dir: DirPath
  interface_name: str = None


def settings_get() -> Settings:
  def dir_must_exists(s: str) -> DirPath:
    s = path.abspath(s)
    if not path.isdir(s):
      raise argparse.ArgumentTypeError(_('%s должен быть каталогом') % s)
    if not path.isdir(path.join(s, '__meta')):
      raise argparse.ArgumentTypeError(_('%s должен быть создан <zopeutil.py>') % s)
    return DirPath(s)

  def dir_may_exists(s: str) -> DirPath:
    s = path.abspath(s)
    if path.exists(s) and not path.isdir(s):
      raise argparse.ArgumentTypeError(_('%s должен быть каталогом') % s)
    return DirPath(s)

  arg_parser = argparse.ArgumentParser(
    description=_('''Автоматический конвертор для интерфейсов ZOPE.
  На вход требуется экспортированный с помощью zopeutil.py каталог интерфейса.
  На выходе получаем каталог yggdrasil интерфейса.'''),
    epilog='Made by pervushin_dg@magnit.ru 2020',
    fromfile_prefix_chars='@'
    )
  arg_parser.add_argument(
    'source_dir', type=dir_must_exists, help=_('Каталог экспортированного интерфейса zope'),
    metavar='zope_dir'
    )
  arg_parser.add_argument(
    'destination_dir', type=dir_may_exists, help=_('Каталог для создания yggdrasil интерфейса'),
    metavar='yggdrasil_dir'
    )
  try:
    args = arg_parser.parse_args()
  except (argparse.ArgumentError, argparse.ArgumentTypeError, SystemExit):
    arg_parser.print_help()
    raise
  rv = Settings(
    **{arg_name: getattr(args, arg_name) for arg_name in ('source_dir', 'destination_dir')}
    )
  return rv


def interface_copy(zope_path: DirPath, ygg_path: DirPath) -> Set[str]:
  """:returns set of suggested interface names. May be empty."""
  sql_list: List[SqlZopeDef] = []

  def ygg_file_save() -> Optional[str]:
    """returns interface name if detected else None"""
    def ygg_sql_save():
      rv = SqlZopeDef(z_json=z_json)
      sql_list.append(rv)
      return

    def ygg_html_save():
      html_name = z_json['id']
      html_name = path.join(ygg_path, 'frontend', html_name+'.html')
      with open(html_name, 'wt', encoding='utf8') as yf:
        print(z_json['_text'], file=yf)
      return

    def ygg_py_save() -> str:
      """returns suggested interface name"""
      py_name = z_json['id']
      py_name = path.join(ygg_path, 'backend', py_name+'.py')
      with open(py_name, 'wt', encoding='utf8') as yf:
        print(z_json['_body'], file=yf)
      rv = z_json['_filepath'].split('/')[-2]
      return rv

    def ygg_module_save():
      py_name = z_json['id']
      py_name = path.join(ygg_path, 'backend', py_name+'.py')
      with open(py_name, 'at', encoding='utf8') as yf:
        print('# Модуль-заглушка. Реализацию придется искать самому', file=yf)
        print(f"# Назначение: {z_json['title']}", file=yf)
        print(f"def {z_json['_function']}():", file=yf)
        print("  raise NotImplementedError('Реализуй меня!')", file=yf)
        print("", file=yf)
      return

    interface_name = None
    if z_json.get('connection_id') == 'Interbase_database_connection':
      ygg_sql_save()
    elif z_json.get('content_type') == 'text/html':
      ygg_html_save()
    elif 'Python_magic' in z_json:
      interface_name = ygg_py_save()
    elif '_module' in z_json:
      ygg_module_save()
    else:
      raise LookupError(_('Неизветный объект zope <%s>' % z_json[:1000]))
    return interface_name

  zope_meta_dir = path.join(zope_path, '__meta')
  makedirs(path.join(ygg_path, 'frontend'), exist_ok=True)
  makedirs(path.join(ygg_path, 'backend'), exist_ok=True)
  interface_names = set()
  for file in scandir(zope_meta_dir):
    if not file.is_file():
      continue
    with open(file, 'rt', encoding='cp1251', errors='surrogateescape') as zf:
      z_json = json.load(zf)
    interface_name = ygg_file_save()
    if interface_name:
      interface_names.add(interface_name)
  db_api_name = path.join(ygg_path, 'backend', 'db_api.py')
  with open(db_api_name, 'wt', encoding='utf8') as yf:
    for s in (
      '# -*- coding: utf8 -*-\n'
      '# Этот файл сгенерирован автоматически.',
      '# Для доступа к БД реализуйте функцию fetch_all\n'
      'from typing import List',
      'from box import Box\n\n',
      'def fetch_all(sql: str, *args) -> List[Box]:',
      '  raise NotImplementedError("Реализуй меня")\n',
      ):
      print(s, file=yf)
    for sql in sql_list:
      print(sql.to_ygg(), file=yf)
  return interface_names


def interface_name_choose(names: Set[str]) -> str:
  # noinspection PyPep8Naming
  NAME_RE = re.compile(r'^[A-Z_][A-Z_0-9]*$')
  rv = ''
  while not rv:
    if len(names) == 0:
      rv = input(_('Название интерфейса:'))
      if not NAME_RE.match(rv):
        rv = ''
    elif 1 < len(names):
      name_list = list(names)
      print(_('Выбери название интерфейса:'))
      for i, n in enumerate((x for x in name_list if NAME_RE.match(x)), 1):
        print(_('({i: >3}) {n}').format(i=i, n=n))
      i = input(_(':'))
      # noinspection PyBroadException
      try:
        i = int(i)
        rv = name_list[i-1]
      except Exception:
        rv = ''
    else:
      rv = names.pop()
  return rv


def main() -> None:
  settings = settings_get()
  interface_names = interface_copy(settings.source_dir, settings.destination_dir)
  interface_name = interface_name_choose(interface_names)
  print(_('Интерфейс %s готов, шеф!') % interface_name)
  return


if __name__ == '__main__':
  main()
