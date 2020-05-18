# -*- coding: utf-8 -*-
_endpoints = set()

def videoRegistration(video_type):
  def unique(seq, idfun=None): 
     if idfun is None:
         def idfun(x): return x
     seen = {}
     result = []
     for item in seq:
         marker = idfun(item)
         if seen.has_key(marker): continue
         seen[marker] = 1
         result.append(item)
     return result

  class XMLBuilder:
      # По-хорошему здесь должен быть конструктор (__init__). Но так как Zope запрещает
      # создавать конструкторы класса в скриптах, придется вызывать init вручную.
      def init(self, indent=2):
          self.indent = indent

      def get_meta(self,data_dict,key):
         result = {}
         if data_dict.has_key(key):
            l = len(key)
            key_meta = filter(lambda x:x.find(key+'$')>-1,data_dict.keys())
            for i in key_meta:
               result[i[l+1:]] = data_dict[i]
         return result
        
      def translate_data(self,data,meta={},start_indent = 0):
         xml_data = ''
         #if isinstance(data,dict):
         if same_type(data,{}):
            xml_data += self.dict_to_xml(data,start_indent)
         #elif isinstance(data,list):
         elif same_type(data,[]):
            xml_data += self.list_to_xml(meta.get('item_tag','item'),data,start_indent)
         else:
            xml_data += str(data)
         return xml_data

      def list_to_xml(self, tag, items, start_indent = 0):
          xml_data = ''
          for item in items:
             if xml_data != '': xml_data += '\n'
             #nl = isinstance(item,(list,dict))
             nl = same_type(item,[]) or same_type(item, {})
             xml_data += ' '*(start_indent+self.indent)+ ('<%s>' + ['','\n'][nl] + '%s' + ['','\n'+' '*(start_indent+self.indent)][nl] + '</%s>') % (tag,self.translate_data(item,{},start_indent+self.indent),tag)
          return xml_data

      def dict_to_xml(self, data, start_indent = 0):
          xml_data = ''
          key_list = []
          if data.has_key('_order_'):
              key_list = filter(lambda x:x in data.keys(),data['_order_'])
              key_list.extend(filter(lambda x:(x not in key_list) and
                                              (x != '_order_') and
                                              (x.find('$') == -1),
                                     data.keys()))
          else:
              key_list = filter(lambda x:(x not in key_list) and
                                          (x != '_order_') and
                                          (x.find('$') == -1),
                                 data.keys())
          key_list = unique(key_list)
          for k in key_list:
              v = data[k]
              #nl = isinstance(v,(list,dict))
              nl = same_type(v,[]) or same_type(v, {})
              if xml_data != '': xml_data += '\n'
              xml_data += ' '*(start_indent+self.indent)+ ('<%s>' + ['','\n'][nl] + '%s' + ['','\n'+' '*(start_indent+self.indent)][nl] + '</%s>') % (k,self.translate_data(v,self.get_meta(data,k),start_indent+self.indent),k)
             
          return xml_data
                                                                          
      def get_xml(self, root_tag='root', **data):
          xml = '<?xml version="1.0" encoding="windows-1251"?>\n' + \
                '<%s>\n' % (root_tag,) + \
                '%s' + \
                '\n</%s>' % (root_tag,)
          
          xml_data = self.dict_to_xml(data)
          return xml % (xml_data,)

  class Trassir:
      def init(self):
          self.xb = XMLBuilder()
          self.xb.init()

      def get_time(self):
          return DateTime().strftime('%H:%M:%S')

      def get_date(self):
          return DateTime().strftime('%d/%m/%Y')

      def get_xml(self, **data):
          data['date'] = self.get_date()
          data['time'] = self.get_time()
          order = ['event_type','operation_id','date','time','session','operator']
          order.extend(data.setdefault('_order_',[]))
          data['_order_'] = order
          return self.xb.get_xml('transaction',**data)

      def cartincome_begin(self, operation_id, empl_name, id_session, expedition):
          return self.get_xml(**{'_order_':['expedition'],
                                 'event_type': 'cart_income_begin',
                                 'operation_id': operation_id,
                                 'expedition': expedition,
                                 'session': id_session,
                                 'operator': empl_name})
        
      def cartincome_cart(self, operation_id, empl_name, id_session, expedition, cart, operations):
          return self.get_xml(**{'_order_':['expedition','cart','invoices'],
                                 'event_type': 'cart_income_cart',
                                 'operation_id': operation_id,
                                 'expedition': expedition,
                                 'session': id_session,
                                 'operator': empl_name,
                                 'cart': cart,
                                 'invoices': operations,
                                 'invoices$item_tag': 'invoice'})

      def cartincome_end(self, operation_id, empl_name, id_session, expedition):
           return self.get_xml(**{'_order_':['expedition'],
                                  'event_type': 'cart_income_end',
                                  'operation_id': operation_id,
                                  'expedition': expedition,
                                  'session': id_session,
                                  'operator': empl_name})

  class VideoRegistrationManager:
      def get_holder(self, video_type):
          if (video_type == 'trassir'):
              t = Trassir()
              t.init()
              return t

  return VideoRegistrationManager().get_holder(video_type)


