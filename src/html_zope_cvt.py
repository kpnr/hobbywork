from typing import Mapping, Sequence, Tuple
from lxml.html import HTMLParser, Element, document_fromstring

def html_zope_cvt(z_json: Mapping) -> Sequence[str]:
  ATTRS_IGNORED = frozenset(
    'action align bgcolor border cellspacing class href id language length maxlength name onclick '
    'style type '
    'value width'.split(' '))
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

  def z_parse(el: Element, level: int) -> Sequence[str]:
    def z_import_add(i_name:str) -> None:
      z_imports.add(i_name)
      return

    def tag_open_close_get(el: Element) -> Tuple[str, str]:
      def attrs_to_str(attrs: Mapping):
        rv = ''
        for k, v in attrs.items():
          rv += f' {k}="{v}"'
        return rv
      o = '<'+el.tag + attrs_to_str(el.attrib)
      if len(el) or el.text:
        o += '>'
        c = f'</{el.tag}>'
      else:
        o +=' />'
        c = ''
      return o, c

    rv = []
    indent = '  ' * level
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
      rv += [indent + '{%- block '+slot_name+' -%}']
      rv += z_parse(el, level)
      rv += [indent + '{%- endblock -%}']
      return rv
    condition = el.attrib.pop('tal:condition', '')
    if condition:
      rv += [indent + '{%- if ' + condition + ' -%}']
      rv += z_parse(el, level)
      rv += [indent + '{%- endif -%}']
      return rv
    repeat = el.attrib.pop('tal:repeat', '')
    if repeat:
      repeat_var, repeat_expr = repeat.split(' ',1)
      rv += [indent + '{%- for ' + repeat_var + ' in ' + repeat_expr + ' -%}']
      rv += z_parse(el, level)
      rv += [indent + '{%- end for -%}']
      return rv
    content = el.attrib.pop('tal:content', '')
    if content:
      el.text = content
    attrs = el.attrib.pop('tal:attributes', '')
    if attrs:
      attrs = [a.strip(' ').split(' ', 1) for a in attrs.split(';')]
      attrs = {a.strip(' '): v.strip(' ') for (a, v) in attrs}
      el.attrib.update(attrs)
    if frozenset(el.attrib.keys()) - ATTRS_IGNORED:
      breakpoint()
    tag_open, tag_close = tag_open_close_get(el)
    rv += [indent + tag_open]
    if el.text:
      rv += [indent + '  ' + el.text]
    for child in el:
      rv += z_parse(child, level)
    if tag_close:
      rv += [indent + tag_close]
    if el.tail:
      rv += [indent + el.tail]
    return rv

  parser = HTMLParser()
  doc = document_fromstring(z_json['_text'], parser, ensure_head_body=True)
  rv = z_parse(doc, 0)
  for imp in z_imports:
    yield '{%- extends "' + imp + '" -%}'
  for s in rv:
    yield s
  return
