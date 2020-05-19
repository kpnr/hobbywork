# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Type, TypeVar, Sequence, Mapping
import SQLParser

SqlArgType = TypeVar('SqlArgType', str, int, float, datetime)


@dataclass
class SqlArgDef(object):
  id: str
  type: Type[SqlArgType]
  optional: bool


@dataclass
class SqlZopeDef(object):
  RE_INPUT_VAR = re.compile(
    r'(?ax)(?P<dtml><dtml-sqlvar \s+ (?P<id>[A-Za-z][\w$]*) \s+ type=\"(?P<type>string|int|float)\"'
    r'(?:\s+(?P<optional>optional))?\s*>)'
    )
  STR_TO_TYPE = dict(
    int=int,
    n=int,
    string=str,
    s=str,
    d=datetime,
    )
  id: str
  title: str
  inputs: Sequence[SqlArgDef]
  outputs: Sequence[SqlArgDef]
  source: str

  def __init__(self, *, z_json: Mapping):
    super().__init__()

    def source_to_sql(src: str) -> str:
      """Remove dtml-sqlvar"""
      def replacer(m: re.Match) -> str:
        rv = ':'+m.group('id').casefold()
        return rv

      rv = self.RE_INPUT_VAR.sub(replacer, src)
      return rv
    self.id = z_json['id']
    self.title = z_json['title']
    self.inputs = self.sql_input_get(z_json['src'])
    self.outputs = self.sql_output_get(z_json.get('_col', []))
    self.source = source_to_sql(z_json['src'])

  @classmethod
  def sql_input_get(cls, z_def: str) -> Sequence[SqlArgDef]:
    rv = []
    for var_match in cls.RE_INPUT_VAR.finditer(z_def):
      rv.append(
        SqlArgDef(
          id=var_match.group('id'),
          type=cls.STR_TO_TYPE[var_match.group('type')],
          optional=bool(var_match.group('optional'))
          )
        )
    assert len(rv) == z_def.count('dtml-sqlvar')
    return rv

  @classmethod
  def sql_output_get(cls, z_def: Sequence[Mapping]) -> Sequence[SqlArgDef]:
    rv = []
    for z_arg in z_def:
      rv.append(
        SqlArgDef(
          id=z_arg['name'],
          type=cls.STR_TO_TYPE[z_arg['type']],
          optional=False
          )
        )
    return rv

  def to_ygg(self):
    def arg_defs_to_list(arg_defs: Sequence[SqlArgDef]) -> Sequence[str]:
      rv = []
      for i in arg_defs:
        if i.optional:
          continue
        rv.append(f'{i.id}: {i.type.__name__}')
      for i in arg_defs:
        if not i.optional:
          continue
        rv.append(f'{i.id}: {i.type.__name__}=None')
      return rv

    rv = f'def {self.id}({", ".join(arg_defs_to_list(self.inputs))}):\n'
    rv += f'  """\n{self.title}\n'
    rv += '  Output fields:\n    '
    rv += '\n    '.join(arg_defs_to_list(self.outputs))
    rv += '\n  """\n'
    sql, param_list = SQLParser.named_to_pos_parse(self.source)
    sql = sql.replace('"', r'\"')
    param_list = (p for p in param_list)
    rv += f'  rv = fetch_all("{sql}", {", ".join(param_list)})\n'
    rv += '  return rv\n\n'
    return rv
