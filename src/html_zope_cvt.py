from typing import Mapping, Sequence, Tuple
from lxml.html import HTMLParser, Element, document_fromstring

ATTRS_ALLOWED = frozenset(
  'action align bgcolor border cellspacing class href id language length maxlength name onclick '
  'style type '
  'value width '
  'metal:fill-slot metal:use-macro '
  'tal:attributes tal:condition tal:content tal:repeat'.split(' ')
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
  html_test = '''<HTML metal:use-macro="here/main_template/macros/page">
    <script  metal:fill-slot="script" tal:content="python:'function init(){OnBodyLoad(\'\',\'barcode\',\'\');}'"/>
    <div align="justify" metal:fill-slot="error" class="error" tal:condition="request/err|options/err|nothing" tal:content="structure request/err|options/err"/>
    
    <div metal:fill-slot="data" align="center">
        <b tal:content="options/mes"/><br>
        <div style="width: 240px; word-break: break-all;">
        <span tal:repeat="item options/data">
            <a tal:attributes="href python:'gettelegaAction?uid=%s&id=%s&id_shtask=%s&outurl=%s&tcode=%s&tovarid=%s' % (request.uid, item.ID_ART, options.get('id_shtask'), request.outurl, options.get('tcode'), options.get('tovarid'))">
                <span class="smalltext" tal:content="item/NAME"/>
            </a> 
            <br>
        </span> 
        </div>
        <br>
        <a id='back' tal:attributes="href python: 'gettelegaAction?uid=%s&id_shtask=%s&outurl=%s&tcode=%s'%(request.uid, options.get('id_shtask'), request.outurl, options.get('tcode'))">Назад</a>
    </div>
</HTML>
'''
  z_imports = set()
  output_enabled = False
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

    def tal_content_cvt(s: str) -> str:
      s = s.strip(' \r\n\t')
      if s.startswith('python:'):
        s = s[len('python:'):].strip(' \r\n\t')
      elif s.startswith('structure '):
        s = s[len('structure '):]
        s = tal_expression_cvt(s)
      elif s.startswith('text '):
        s = s[len('text '):]
        s = tal_expression_cvt(s)
      else:
        s = tal_expression_cvt(s)
      s = '{{ '+s+' }}'
      return s

    def tal_expression_cvt(s: str) -> str:
      if s.startswith('python:'):
        s = s[len('python:'):]
        s = s.strip()
      else:
        # it seems "path:" expression
        s = s.replace('/', '.')
        s = s.replace('|', ' or ')
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
      assert not output_enabled
      output_enabled = True
      emit('{%- block '+slot_name+' -%}')
      z_parse(el, level)
      emit('{%- endblock -%}')
      emit('')
      output_enabled = False
      return
    condition = el.attrib.pop('tal:condition', '')
    if condition:
      condition = tal_expression_cvt(condition)
      emit('{%- if ' + condition + ' -%}')
      z_parse(el, level)
      emit('{%- endif -%}')
      return
    repeat = el.attrib.pop('tal:repeat', '')
    if repeat:
      repeat_var, repeat_expr = repeat.split(' ',1)
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
    tag_open, tag_close = tag_open_close_get(el)
    emit(tag_open)
    if el.text:
      emit('  ' + el.text)
    for child in el:
      z_parse(child, level)
    if tag_close:
      emit(tag_close)
    if el.tail:
      emit(el.tail)
    return

  parser = HTMLParser()
  doc = document_fromstring(z_json['_text'], parser, ensure_head_body=True)
  z_parse(doc, 0)
  for imp in z_imports:
    yield '{%- extends "' + imp + '" -%}'
  for s in z_parse_out:
    yield s
  return
