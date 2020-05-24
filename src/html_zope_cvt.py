from typing import Mapping, Sequence, Tuple
import re
from lxml.html import Element, soupparser, HtmlComment
from tales_cvt import tales_expression_to_jinja as tal_expression_cvt

ATTRS_ALLOWED = frozenset(
  'action align bgcolor border cellpadding cellspacing class colspan '
  'disabled href id language length maxlength name onblur onclick '
  'onkeydown onkeyup size style type '
  'valign value width '
  'metal:fill-slot metal:use-macro '
  'tal:define tal:attributes tal:condition tal:content tal:omit-tag tal:repeat'.split(' ')
  )

def node_visit(el: Element) -> None:
  REPLACE_NAMES = {
    'aling': 'align'
    }
  for a_name in frozenset(el.attrib.keys()) - ATTRS_ALLOWED:
    a_name_new = REPLACE_NAMES.get(a_name)
    if a_name_new is not None:
      a_value = el.attrib.pop(a_name)
      if a_name_new:
        el.attrib.update({a_name_new: a_value})
    else:
      breakpoint()
  return

def html_zope_cvt(z_json: Mapping) -> Sequence[str]:
  z_imports = set()
  output_enabled = 0
  z_parse_out = []

  def z_parse(el: Element, level: int) -> None:
    def z_import_add(i_name: str) -> None:
      IMPORT_REPLACE = {
        'here/main_template/macros/page': 'zope/main_template.html'
        }
      i_name = IMPORT_REPLACE.get(i_name, i_name)
      z_imports.add(i_name)
      return

    def tag_open_close_get(el: Element) -> Tuple[str, str]:
      def attrs_to_str(attrs: Mapping):
        rv = ''
        for k, v in attrs.items():
          # it seems Jinja handle expressions in double quoted strings
          # if not (v.startswith('{{') and v.endswith('}}')):
          v = f'"{v}"'
          rv += f' {k}={v}'
        return rv
      if isinstance(el, HtmlComment):
        o = '<!--'
        c = '-->'
      else:
        o = '<'+el.tag + attrs_to_str(el.attrib)
        if len(el) or el.text:
          o += '>'
          c = f'</{el.tag}>'
        else:
          o +=' />'
          c = ''
      return o, c

    def emit(s: str) -> None:
      if output_enabled:
        indent = '  ' * level
        z_parse_out.append(indent + s)
      return

    def tal_define_cvt(s: str):
      def tal_to_def_list(s: str) -> Sequence[str]:
        var_defs_dirty = s.split(';')
        var_defs_clear = []
        var_current = var_defs_dirty.pop(0)
        for d in var_defs_dirty:
          if d:
            var_defs_clear.append(var_current)
            var_current = d
          else:
            var_current += ';'
        var_defs_clear.append(var_current)
        return var_defs_clear
      def tal_var_def_parse(s: str) -> Tuple[str, str]:
        VAR_DEF_RE = re.compile(r"(?mxu) ^ \s* (?P<scope>(local|global) \s+)? (?P<name>\w+)"
                                r"\s+ (?P<expr>.+) $")
        m = VAR_DEF_RE.match(s)
        scope, name, expr = m.group('scope', 'name', 'expr')
        if scope == 'global':
          raise NotImplementedError('tal:define <global> scope not implemented')
        expr = tal_expression_cvt(expr)
        return (name, expr)
      var_defs = tal_to_def_list(s)
      var_def_parsed = []
      for var_def in var_defs:
        var_parsed = tal_var_def_parse(var_def)
        var_def_parsed.append(var_parsed)
      var_names, var_values = zip(*var_def_parsed)
      lval = ', '.join(var_names)
      rval = ', '.join(var_values)
      rv = lval + ' = ' + rval
      return rv

    def tal_content_cvt(s: str) -> str:
      s = s.strip(' \r\n\t')
      if s.startswith('python:'):
        s = s[len('python:'):].strip(' \r\n\t')
      elif s.startswith('structure '):
        s = s[len('structure '):]
        s = '('+tal_expression_cvt(s)+')|safe'
      elif s.startswith('text '):
        s = s[len('text '):]
        s = tal_expression_cvt(s)
      else:
        s = tal_expression_cvt(s)
      s = '{{ '+s+' }}'
      return s

    nonlocal output_enabled
    node_visit(el)
    if output_enabled:
      level += 1
    if el.text is not None:
      el.text = el.text.strip(' \n\t\r')
    if el.tail is not None:
      el.tail = el.tail.strip(' \n\t\r')
    import_name = el.attrib.pop('metal:use-macro', '')
    if import_name:
      z_import_add(import_name)
    slot_name = el.attrib.pop('metal:fill-slot', '')
    if slot_name:
      output_enabled += 1
      emit('{%- block '+slot_name+' -%}')
      z_parse(el, level)
      emit('{%- endblock -%}')
      emit('')
      output_enabled -= 1
      return
    define = el.attrib.pop('tal:define', '')
    if define:
      define = tal_define_cvt(define)
      emit('{{ set ' + define + ' }}')
    condition = el.attrib.pop('tal:condition', '')
    if condition:
      condition = tal_expression_cvt(condition)
      emit('{%- if ' + condition + ' -%}')
      z_parse(el, level)
      emit('{%- endif -%}')
      return
    repeat = el.attrib.pop('tal:repeat', '')
    if repeat:
      repeat_var, repeat_expr = (x.strip() for x in repeat.split(' ',1))
      repeat_expr = tal_expression_cvt(repeat_expr)
      emit('{%- for ' + repeat_var + ' in ' + repeat_expr + ' -%}')
      z_parse(el, level)
      emit('{%- endfor -%}')
      return
    content = el.attrib.pop('tal:content', '')
    if content:
      el.text = tal_content_cvt(content)
    attrs = el.attrib.pop('tal:attributes', '')
    if attrs:
      attrs = [a.strip(' ').split(' ', 1) for a in attrs.split(';')]
      attrs = {a.strip(' '): tal_content_cvt(v.strip(' ')) for (a, v) in attrs}
      el.attrib.update(attrs)
    omit = el.attrib.pop('tal:omit-tag', None)
    tag_open, tag_close = tag_open_close_get(el)
    is_dummy_tag = isinstance(el.tag, str) and el.tag.casefold() == 'span' and not (el.text or el.tail)
    if omit is not None:
      if omit:
        raise NotImplementedError('Non-empty <tal:omit-tag> attribute')
      else:
        is_dummy_tag = True
    if not is_dummy_tag:
      emit(tag_open)
    if el.text:
      emit('  ' + el.text)
    for child in el:
      z_parse(child, level-1 if is_dummy_tag else level)
    if tag_close and not is_dummy_tag:
      emit(tag_close)
    if el.tail:
      emit(el.tail)
    return

  # doc = soupparser.fromstring(html_test)
  doc = soupparser.fromstring(z_json['_text'])
  z_parse(doc, 0)
  for imp in z_imports:
    yield '{%- extends "' + imp + '" -%}'
  for s in z_parse_out:
    yield s
  return

html_test = '''<html metal:use-macro="here/main_template/macros/page">
   <script  metal:fill-slot="script" tal:content="python:'function init(){OnBodyLoad(\'\',\'\');}'"/>
    <div align="justify" metal:fill-slot="error" class="error" tal:condition="request/err|options/err|nothing" tal:content="structure request/err|options/err"/>

    <div metal:fill-slot="data" align="center" >    

Текущие привязки товара:
            <table class='table1px'>
            <tr>
       <td>МП</td>
       <td>Паллет</td>
       <td>Кол-во</td>
            </tr>
            <tr tal:repeat="item  python: container.GM_GETARTAMOUNTMERCH(id_art=request.id_art)">
             <span tal:define="style python: '{background:#666666}'*(item.STATUS=='0')"> 
              <td tal:attributes="style style">
              <a href='#'>
               <span class="smalltext" tal:content="python: item.SITENAME" />
              </a>     </td>

   
            <span tal:condition="python: container.GET_TYPE_PALLET(barcode=item.BIGNUMBER)[0]['IS_OPT']==1">
              <td style="background-color: gray;" tal:content="python: item.BIGNUMBER"></td>
            </span>  
            <span tal:condition="python: container.GET_TYPE_PALLET(barcode=item.BIGNUMBER)[0]['IS_OPT']==0">
              <td tal:attributes="style style" tal:content="python: item.BIGNUMBER"></td>
            </span> 

              <td tal:attributes="style style" tal:content="python: item.AMOUNT"></td>
             </span>
            </tr>
          </table>

   <br><a id='back' tal:attributes="href python: 'artAction?uid=%s&sbarcode=%s&name=%s&num=%s' % (request.uid,request.sbarcode,request.name,request['num'])">Назад</a>
    </div>    
</html>

'''
