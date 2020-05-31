# -*- coding: utf-8 -*-
import re
from typing import Mapping, Generator, Optional, Any
from ast import parse as py_parse, NodeTransformer, AST, Str, Call, Load, Name, copy_location
import astor


class ZAstTransformer(NodeTransformer):
  def visit_Str(self, node: Str) -> Any:
    rv = Call(
      args=[node],
      keywords=[],
      func=Name(
        ctx=Load(),
        id='str'
        )
      )
    rv = copy_location(rv, node)
    return rv

  def visit_Call(self, node: Call) -> Any:
    def is_str_init_call(node):
      rv = isinstance(node, Call) and len(getattr(node, 'args', [])) == 1
      rv = rv and isinstance(node.func, Name) and node.func.id == 'str'
      return rv

    rv = self.generic_visit(node)
    if is_str_init_call(node) and is_str_init_call(node.args[0]):
      # `str(str(xxx)) -> str(xxx)
      rv = node.args[0]
    return rv

  def generic_visit(self, node: AST) -> Optional[AST]:
    rv = super().generic_visit(node)
    return rv

def py_zope_patch(src):
  def fix_not_eq_op(lines, line_no, col):
    line_str = lines[line_no]
    test_str = line_str[col - 2 :col]
    if test_str == '<>':
      line_str = line_str[:col-2] + '!=' + line_str[col:]
      lines[line_no] = line_str
      rv = 1
    else:
      rv = 0
    return rv

  def fix_print_stmt(lines, line_no, col):
    PRINT_RE = re.compile(r'(?x) (?P<indent>\s*) print \s* (?P<arg>[^(\s].*)? $')
    line_str = lines[line_no]
    m = PRINT_RE.match(line_str)
    if m:
      line_str = m['indent'] + 'print(' + m['arg'] + ')'
      lines[line_no] = line_str
      rv = 1
    else:
      rv = 0
    return rv

  def fix_indent_tabs(lines, line_no, col):
    rv = 0
    for line_no, line in enumerate(lines, 0):
      line_new = ''
      col_no_new = -1
      for col_no, char in enumerate(line, 0):
        col_no_new += 1
        if ord(' ') < ord(char):
          line_new += line[col_no:]
          break
        elif ord(char) == 9: # TAB char
          space_cnt = 8 - col_no_new % 8
          col_no_new += space_cnt - 1
          line_new += ' ' * space_cnt
        elif ord(char) == ord(' '):
          line_new += ' '
        else:
          breakpoint()
          raise TabError('Invalid indent char %s (code=%s)' % (char, ord(char)))
      if line != line_new:
        lines[line_no] = line_new
        rv = 1
    return rv

  def fix_state_prepare(exception, source):
    src_lined = source.split('\n')
    line = exception.lineno - 1
    col = exception.offset
    return src_lined, line, col

  # src = test_src
  parse_flag = 1
  while parse_flag:
    try:
      parse_flag = 0
      ast = py_parse(src, '', 'exec')
    except TabError as e:
      src_lined, line, col = fix_state_prepare(e, src)
      if fix_indent_tabs(src_lined, line, col):
        parse_flag = 1
        src = '\n'.join(src_lined)
      else:
        breakpoint()
    except SyntaxError as e:
      src_lined, line, col = fix_state_prepare(e, src)
      if fix_not_eq_op(src_lined, line, col):
        parse_flag = 1
        src = '\n'.join(src_lined)
      elif fix_print_stmt(src_lined, line, col):
        parse_flag = 1
        src = '\n'.join(src_lined)
      else:
        breakpoint()
        raise
  z_ast_transformer = ZAstTransformer()
  ast = z_ast_transformer.visit(ast)
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

test_src="""request = container.REQUEST
RESPONSE =  request.RESPONSE

barcode = request.get('barcode','')

if barcode == '':
   return container.task()
   
a=container.PPRINT_INFO_BARCODE(barcode=barcode)
if len(a)==0:
   return container.task(err = 'Товар не найден')
a=a[0]
if a.MODE <>    'ART':
   return container.task(err = 'Товар не найден')
   
b = container.PPRINT_INFO_ART(id_art=a.ID, weight=a.weight)[0]

return container.task(price = b.PRICESTR, pricew = b.PRICESTRW, artname=b.NAME, isweight=b.isweight)
"""
