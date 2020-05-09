import argparse
from gettext import gettext as _
from dataclasses import dataclass
from os import path

@dataclass(frozen=True)
class Settings(object):
  source_dir:str
  destination_dir:str

def settings_get() -> Settings:
  def dir_must_exists(s: str) -> str:
    s = path.abspath(s)
    if not path.isdir(s):
      raise argparse.ArgumentTypeError(_('%s должен быть каталогом') % s)
    if not path.isdir(path.join(s,'__meta')):
      raise argparse.ArgumentTypeError(_('%s должен быть создан <zopeutil.py>') % s)
    return s

  def dir_may_exists(s):
    s = path.abspath(s)
    if path.exists(s) and not path.isdir(s):
      raise argparse.ArgumentTypeError(_('%s должен быть каталогом') %s)
    return s

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
  rv = Settings(**{arg_name:getattr(args, arg_name) for arg_name in ('source_dir', 'destination_dir')})
  return rv

def main():
  setting = settings_get()
  print(_('Усё готово, шеф!'))
  return


if __name__ == '__main__':
  main()
