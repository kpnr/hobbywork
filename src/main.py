import argparse
import json
import re
from gettext import gettext as _
from dataclasses import dataclass
from os import path, scandir, makedirs
from typing import NewType, Optional, Set, List, Any, MutableMapping
from sql_zope_cvt import SqlZopeDef
from py_zope_cvt import py_zope_cvt
from html_zope_cvt import html_zope_cvt

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
      raise argparse.ArgumentTypeError(_('%s должен быть создан <zexpextract.py>') % s)
    return DirPath(s)

  def dir_may_exists(s: str) -> DirPath:
    s = path.abspath(s)
    if path.exists(s) and not path.isdir(s):
      raise argparse.ArgumentTypeError(_('%s должен быть каталогом') % s)
    return DirPath(s)

  arg_parser = argparse.ArgumentParser(
    description=_('''Автоматический конвертор для интерфейсов ZOPE.
  На вход требуется экспортированный с помощью zexpextract.py каталог интерфейса.
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


def interface_copy(zope_path: DirPath, ygg_path: DirPath) -> str:
  """:returns interface name"""
  sql_list: List[SqlZopeDef] = []
  module_list: MutableMapping[str, dict] = dict()
  files_desc: MutableMapping[str, Any] = dict()

  def file_describe(file_name_full: str, description: Any):
    files_desc[file_name_full] = description
    return

  def files_desc_save():
    desc_map = dict()
    for name_full, desc in files_desc.items():
      file_path = path.dirname(name_full)
      file_name = path.basename(name_full)
      dir_descs = desc_map.setdefault(file_path, dict())
      dir_descs.update({file_name: desc})
    for dir_name, files in desc_map.items():
      desc_file_name = path.join(dir_name, 'descript.ion')
      with open(desc_file_name, 'wt', encoding='utf8') as df:
        for fn, fd in files.items():
          df.write(f'{fn} {json.dumps(fd)}\n')
    return

  def ygg_file_save() -> None:
    def ygg_sql_save():
      rv = SqlZopeDef(z_json=z_json)
      sql_list.append(rv)
      return

    def ygg_html_save() -> None:
      html_name = z_json['id']
      html_name = path.join(frontend_dir, html_name+'.html')
      file_describe(html_name, dict(type='template'))
      with open(html_name, 'wt', encoding='utf8') as yf:
        for s in html_zope_cvt(z_json):
          yf.write(s + '\n')
      return

    def ygg_py_save() -> None:
      py_name = z_json['id']
      py_name = path.join(backend_dir, py_name+'.py')
      file_describe(py_name, dict(type='python'))
      with open(py_name, 'wt', encoding='utf8') as yf:
        for s in py_zope_cvt(z_json):
          yf.write(s + '\n')
      return

    def ygg_module_save():
      py_name = z_json['id']
      module_content= module_list.setdefault(py_name, dict())
      func_name = z_json['_function']
      module_content[func_name] = z_json
      return

    if z_json.get('connection_id') == 'Interbase_database_connection':
      ygg_sql_save()
    elif z_json.get('content_type') == 'text/html':
      ygg_html_save()
    elif 'Python_magic' in z_json:
      ygg_py_save()
    elif '_module' in z_json:
      ygg_module_save()
    else:
      raise LookupError(_('Неизветный объект zope <%s>' % z_json[:1000]))
    return

  zope_meta_dir = path.abspath(path.join(zope_path, '__meta'))
  interface_name = path.basename(zope_path).upper()
  frontend_dir = path.join(ygg_path, interface_name, 'frontend', interface_name)
  backend_dir = path.join(ygg_path, interface_name, 'backend')
  makedirs(frontend_dir, exist_ok=True)
  makedirs(backend_dir, exist_ok=True)
  for file in scandir(zope_meta_dir):
    if not file.is_file():
      continue
    with open(file, 'rt', encoding='cp1251', errors='surrogateescape') as zf:
      z_json = json.load(zf)
    ygg_file_save()
  # finalization
  # save all sql blocks into single py module
  db_api_name = path.join(backend_dir, 'db_api.py')
  file_describe(db_api_name, dict(type='db_api'))
  with open(db_api_name, 'wt', encoding='utf8') as yf:
    yf.write(
      '# -*- coding: utf8 -*-\n'
      '# Этот файл сгенерирован автоматически.\n'
      '# Для доступа к БД реализуйте функцию fetch_all\n\n'
      'from typing import List\n'
      'from box import Box\n\n\n'
      'def fetch_all(sql: str, *args) -> List[Box]:\n'
      '  raise NotImplementedError("Реализуй меня")\n\n\n'
      )
    for sql in sql_list:
      yf.write(sql.to_ygg() + '\n')
  # save module blocks
  for name, content in module_list.items():
    py_name = path.join(backend_dir, name + '.py')
    file_describe(py_name, dict(type='external'))
    with open(py_name, 'wt', encoding='utf8') as yf :
      yf.write('# Модуль-заглушка. Реализацию придется искать самому\n\n')
      for func_name, func_def in content.items():
        yf.write(
          f"\ndef {func_def['_function']}():\n"
          f'  """Назначение: {func_def["title"]}"""\n'
          f"  raise NotImplementedError('Реализуй меня!')\n"
          )
      yf.write("\n")
  # save file descriptions
  files_desc_save()
  return interface_name


def main() -> int:
  settings = settings_get()
  interface_name = interface_copy(settings.source_dir, settings.destination_dir)
  print(_('Интерфейс %s готов, шеф!') % interface_name)
  return 0


if __name__ == '__main__':
  exit_code = main()
  exit(exit_code)
