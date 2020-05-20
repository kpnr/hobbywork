# -*- coding: utf-8 -*-
_endpoints = set()

def videoRegistration(video_type):
    def unique(seq, idfun=None):
        if idfun is None:

            def idfun(x):
                return x
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            if seen.has_key(marker):
                continue
            seen[marker] = 1
            result.append(item)
        return result


    class XMLBuilder:

        def init(self, indent=2):
            self.indent = indent

        def get_meta(self, data_dict, key):
            result = {}
            if data_dict.has_key(key):
                l = len(key)
                key_meta = filter(lambda x: x.find(key + str('$')) > -1,
                    data_dict.keys())
                for i in key_meta:
                    result[i[l + 1:]] = data_dict[i]
            return result

        def translate_data(self, data, meta={}, start_indent=0):
            xml_data = str('')
            if same_type(data, {}):
                xml_data += self.dict_to_xml(data, start_indent)
            elif same_type(data, []):
                xml_data += self.list_to_xml(meta.get(str('item_tag'), str(
                    'item')), data, start_indent)
            else:
                xml_data += str(data)
            return xml_data

        def list_to_xml(self, tag, items, start_indent=0):
            xml_data = str('')
            for item in items:
                if xml_data != str(''):
                    xml_data += str('\n')
                nl = same_type(item, []) or same_type(item, {})
                xml_data += str(' ') * (start_indent + self.indent) + (str(
                    '<%s>') + [str(''), str('\n')][nl] + str('%s') + [str(''), 
                    str('\n') + str(' ') * (start_indent + self.indent)][nl] +
                    str('</%s>')) % (tag, self.translate_data(item, {}, 
                    start_indent + self.indent), tag)
            return xml_data

        def dict_to_xml(self, data, start_indent=0):
            xml_data = str('')
            key_list = []
            if data.has_key(str('_order_')):
                key_list = filter(lambda x: x in data.keys(), data[str('_order_')])
                key_list.extend(filter(lambda x: x not in key_list and x != str
                    ('_order_') and x.find(str('$')) == -1, data.keys()))
            else:
                key_list = filter(lambda x: x not in key_list and x != str(
                    '_order_') and x.find(str('$')) == -1, data.keys())
            key_list = unique(key_list)
            for k in key_list:
                v = data[k]
                nl = same_type(v, []) or same_type(v, {})
                if xml_data != str(''):
                    xml_data += str('\n')
                xml_data += str(' ') * (start_indent + self.indent) + (str(
                    '<%s>') + [str(''), str('\n')][nl] + str('%s') + [str(''), 
                    str('\n') + str(' ') * (start_indent + self.indent)][nl] +
                    str('</%s>')) % (k, self.translate_data(v, self.get_meta(
                    data, k), start_indent + self.indent), k)
            return xml_data

        def get_xml(self, root_tag=str('root'), **data):
            xml = str('<?xml version="1.0" encoding="windows-1251"?>\n') + str(
                '<%s>\n') % (root_tag,) + str('%s') + str('\n</%s>') % (root_tag,)
            xml_data = self.dict_to_xml(data)
            return xml % (xml_data,)


    class Trassir:

        def init(self):
            self.xb = XMLBuilder()
            self.xb.init()

        def get_time(self):
            return DateTime().strftime(str('%H:%M:%S'))

        def get_date(self):
            return DateTime().strftime(str('%d/%m/%Y'))

        def get_xml(self, **data):
            data[str('date')] = self.get_date()
            data[str('time')] = self.get_time()
            order = [str('event_type'), str('operation_id'), str('date'), str(
                'time'), str('session'), str('operator')]
            order.extend(data.setdefault(str('_order_'), []))
            data[str('_order_')] = order
            return self.xb.get_xml(str('transaction'), **data)

        def cartincome_begin(self, operation_id, empl_name, id_session, expedition
            ):
            return self.get_xml(**{str('_order_'): [str('expedition')], str(
                'event_type'): str('cart_income_begin'), str('operation_id'):
                operation_id, str('expedition'): expedition, str('session'):
                id_session, str('operator'): empl_name})

        def cartincome_cart(self, operation_id, empl_name, id_session,
            expedition, cart, operations):
            return self.get_xml(**{str('_order_'): [str('expedition'), str(
                'cart'), str('invoices')], str('event_type'): str(
                'cart_income_cart'), str('operation_id'): operation_id, str(
                'expedition'): expedition, str('session'): id_session, str(
                'operator'): empl_name, str('cart'): cart, str('invoices'):
                operations, str('invoices$item_tag'): str('invoice')})

        def cartincome_end(self, operation_id, empl_name, id_session, expedition):
            return self.get_xml(**{str('_order_'): [str('expedition')], str(
                'event_type'): str('cart_income_end'), str('operation_id'):
                operation_id, str('expedition'): expedition, str('session'):
                id_session, str('operator'): empl_name})


    class VideoRegistrationManager:

        def get_holder(self, video_type):
            if video_type == str('trassir'):
                t = Trassir()
                t.init()
                return t


    return VideoRegistrationManager().get_holder(video_type)

