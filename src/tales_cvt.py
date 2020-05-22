import sly


# noinspection PyPep8Naming
class Lexer_python(sly.Lexer):
  # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
  tokens = {T_BODY}
  T_BODY = r'.+'


# noinspection PyUnresolvedReferences
class Parser_python(sly.Parser):
  tokens = Lexer_python.tokens

  @_("T_BODY")
  def p_all(self, p):
    rv = p.T_BODY
    return rv


# noinspection PyPep8Naming
class Lexer_path(sly.Lexer):
  # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
  tokens = {T_TAIL, T_ID, T_PATH_SPEC_CHAR}
  literals = {'|', '/', '?'}

  T_ID = r'(?iu)[a-z][a-z0-9_]+'
  T_PATH_SPEC_CHAR = r'[ _.,~-]'
  T_TAIL = r'\|.+'


# noinspection PyPep8Naming,PyUnresolvedReferences
class Parser_path(sly.Parser):
  tokens = Lexer_path.tokens

  @_('p_path', 'p_path T_TAIL')
  def p_path_expr(self, p):
    rv = p.p_path
    if 1 < len(p):
      rv += ' or ' + tales_expression_to_jinja(p.T_TAIL[1:])
    return rv

  @_('p_var', 'p_path "/" p_segment')
  def p_path(self, p):
    if 1 < len(p):
      rv = p.p_path + '[' + p.p_segment + ']'
    else:
      rv = p.p_var
    return rv

  @_('T_ID')
  def p_var(self, p):
    rv = p.T_ID
    return rv

  @_(' "?" p_var ', 'p_path_chars')
  def p_segment(self, p):
    if 1 < len(p):
      rv = p.p_var
    else:
      rv = '"'+p.p_path_chars+'"'
    return rv

  @_('T_ID', 'T_PATH_SPEC_CHAR', 'p_path_chars T_ID', 'p_path_chars T_PATH_SPEC_CHAR')
  def p_path_chars(self, p):
    rv = p[0]
    if 1 < len(p):
       rv += p[1]
    return rv


def tales_expression_to_jinja(src: str) -> str:
  def parser_name_and_src_get(src: str) -> (str, str):
    PREFIXIES = frozenset('path exists nocall not string python'.split(' '))
    PREFIX_DEFAULT = 'path'
    parser = PREFIX_DEFAULT
    for pf in PREFIXIES:
      if src.startswith(pf + ':'):
        parser = pf
        src = src[len(pf)+1:]
        break
    return parser, src

  parser_name, src = parser_name_and_src_get(src)
  lexer = globals()['Lexer_'+parser_name]()
  parser = globals()['Parser_'+parser_name]()
  rv = parser.parse(lexer.tokenize(src))
  return rv


def main():
  s = 'request/err'
  r = tales_expression_to_jinja(s)

  s = 'request/err|options'
  r = tales_expression_to_jinja(s)

  s = 'request/err|options/err|nothing'
  r = tales_expression_to_jinja(s)
  return


if __name__=='__main__':
  main()