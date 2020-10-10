# -*- coding: windows-1251 -*-

import os
import math
import decimal
import cherrypy

from server import base, CONFIG, DB

try:
    import json
except ImportError:
    import simplejson as json


units = (
    u'ноль', (u'1', u'1a'), (u'2', u'2a'), u'3', u'4', u'5', u'6', u'7', u'8', u'9'
)

teens = (
    u'10', u'11', u'12', u'13', u'14', u'15', u'16', u'17', u'18', u'19'
)

tens = (
    teens, u'20', u'30', u'40', u'50', u'60', u'70', u'80', u'90'
)

hundreds = (
    u'100', u'200', u'300', u'400', u'500', u'600', u'700', u'800', u'900'
)

orders = (  # plural forms and gender
    #  ((u'', u'', u''), 'm'), # ((u'рубль', u'рубля', u'рублей'), 'm'), # ((u'копейка', u'копейки', u'копеек'), 'f')
    ((u'tys', u'tys2', u'tys1'), 'f'),
    ((u'миллион', u'миллиона', u'миллионов'), 'm'),
    ((u'миллиард', u'миллиарда', u'миллиардов'), 'm'),
)

minus = u'минус'


def thousand(rest, sex):
    """Converts numbers from 19 to 999"""
    prev = 0
    plural = 2
    name = []
    use_teens = rest % 100 >= 10 and rest % 100 <= 19
    if not use_teens:
        data = ((units, 10), (tens, 100), (hundreds, 1000))
    else:
        data = ((teens, 10), (hundreds, 1000))
    for names, x in data:
        cur = int(((rest - prev) % x) * 10 / x)
        prev = rest % x
        if x == 10 and use_teens:
            plural = 2
            name.append(teens[cur])
        elif cur == 0:
            continue
        elif x == 10:
            name_ = names[cur]
            if isinstance(name_, tuple):
                name_ = name_[0 if sex == 'm' else 1]
            name.append(name_)
            if cur >= 2 and cur <= 4:
                plural = 1
            elif cur == 1:
                plural = 0
            else:
                plural = 2
        else:
            name.append(names[cur-1])
    return plural, name


def num2text(num, main_units=((u'', u'', u''), 'm')):
    u"""
    Преобразование числа ``num`` в строку с использованием единиц ``main_units``

    Used in :func:`~.decimal2text`

    Args:
        num (int): число для преобразования в текст
        main_units: единицы в разных падежах и род единицы

    Returns:
        (str) текстовое представление числа с указанием единиц
    """

    _orders = (main_units,) + orders
    if num == 0:
        return ' '.join((units[0], _orders[0][0][2])).strip()  # ноль

    rest = abs(num)
    ord_cnt = 0
    name = []
    while rest > 0:
        plural, nme = thousand(rest % 1000, _orders[ord_cnt][1])
        if nme or ord_cnt == 0:
            name.append(_orders[ord_cnt][0][plural])
        name += nme
        rest = int(rest / 1000)
        ord_cnt += 1
    if num < 0:
        name.append(minus)
    name.reverse()
    return ' '.join(name).strip()


def decimal2text(value, places=2,
                 int_units=(('', '', ''), 'm'),
                 exp_units=(('', '', ''), 'm')):
    u"""
    Args:
        value (float): число, переводимое в строку
        places (int): количество знаков после запятой
        int_units: единицы в разных падежах и род единицы для целой части числа
        exp_units: единицы в разных падежах и род единицы для дробной части числа

    Returns:
        (str) текстовое представление числа с указанием единиц
    """

    value = decimal.Decimal(value)
    q = decimal.Decimal(10) ** -places

    integral, exp = str(value.quantize(q)).split('.')
    return u'%s %s' % (
        num2text(int(integral), int_units),
        num2text(int(exp), exp_units)
    )


def price_to_parts(price):
    u"""
    Разделение цены на целую и дробную части

    Args:
        price (float): входная цена

    Returns:
        (int, str): (количество рублей в цене, количество копеек в цене
        с ведущим нулем)
    """

    price_kop, price_rub = math.modf(price)
    return int(price_rub), '%02d' % int(round(price_kop * 100))


def is_android(headers):
    u"""
    Проверяет является ли клиент устройством на андроиде по заголовкам

    Проверка осуществляется поиском вхождения строки **android** в заголовке
    ``User-Agent`` либо ``X-Requested-With``

    Args:
        headers (dict): заголовки HTTP запроса

    Returns:
        bool: является ли клиент устройством на андроиде
    """

    useragent = (headers.get('User-Agent') or '').lower()
    requested_with = (headers.get('User-Agent') or 'X-Requested-With').lower()
    return 'android' in useragent or 'android' in requested_with


class module(base.base):
    VERSION = '2.0.10'

    #---------------------------------------------------------------------------
    def index(self, akey=None, android=None, **kwargs):
        u"""
        Отображение главной страницы

        Args:
            akey (str): нажатая на интерфейсе кнопка (down/up) для фиксации
                инциндентов по отсутствию ценника или товара в БД
            tid (int): номер задания ТСД (не используется)
            uid (int): идентификатор пользователя ТСД (не используется)
            zope_addr (str): адрес возврата к zope-серверу
            username (str): имя пользователя ТСД (не используется)

        Returns:
            Возвращается шаблон ``index_android`` или ``task`` в зависимости от
            используемого устройства (андроид или нет)
        """

        if not hasattr(self.session, 'FB_user'):
            self.session.FB_user = CONFIG.get('db', 'user')
            self.session.FB_password = CONFIG.get('db', 'pass')
            self.ifaceSes.client_ip = cherrypy.request.remote.ip

        if is_android(cherrypy.request.headers) or android:
            template = tmpl.index_android
        else:
            template = tmpl.task

        if akey and akey in ('down', 'up'):
            try:
                DB.execProc(
                    'GM_PRICECHECKER_UPDATE',
                    (self.ifaceSes.id_sharttask, 1 if akey == 'down' else 2, None, None),
                    'None'
                )
            except Exception, e:
                cherrypy.log('Exception GM_PRICECHECKER_UPDATE: %s' % str(e))

        return template(listart=None, artname=None, jsbodyload='init()', version=self.VERSION)

    index.exposed = True

    def artbarcodeinfo(self, artbarcode, mockup=None, **kwargs):
        u"""
        Отображение информации по товару по его ШК для Android (AJAX JSON)

        Args:
            artbarcode (str): ШК товара

        Returns:
            dict: {
                * price: цена строкой за единицу товара
                * pricew: цена строкой за вес
                * split_price_r: рубли числом за единицу товара
                * split_price_k: копейки строкой за единицу товара
                * split_price_w_r: рубли числом за вес
                * split_price_w_k: копейки строкой за вес
                * unit: единица товара (шт/кг)
                * unit_ex: расширенная единица товара (шт/кг/л)
                * artname: наименование товара
                * isweight: признак весового товара,
                * rest: остатки товара с округлением до 3 знаков после запятой
                * weight: вес товара
                * id_art: id товара
                * artbarcode: ШК товара
                * price_audio: результат работы метода :func:`~modules.GENERIC.PRICECHECK.module.price_audio`
                * version: версия модуля
                * error: ошибка выполнения метода
            }
        """

        if mockup or artbarcode[:6] == 'mockup':
            return json.dumps({
                'price': '123.45',  # строка за ед
                'pricew': '678.90',  # строка за вес

                'split_price_r': 123,
                'split_price_k': 45,
                'split_price_w_r': 678,
                'split_price_w_k': 90,

                'unit': u'кг',
                'unit_ex': u'кг',
                'artname': 'some mockup article',
                'isweight': True,
                'rest': 135.79,
                'weight': 100, 'id_art': 666, 'artbarcode': artbarcode,

                'version': self.VERSION
            })

        not_found_msg = 'Товар по штрих-коду не найден. Обратитесь на сервисную службу за информацией'.decode('cp1251')
        if not hasattr(self.session, 'FB_user'):
            self.session.FB_user = CONFIG.get('db', 'user')
            self.session.FB_password = CONFIG.get('db', 'pass')
            self.ifaceSes.client_ip = cherrypy.request.remote.ip

        try:
            listart = DB.execProc('PPRINT_INFO_BARCODE2', (artbarcode, None, None, None))
            data = DB.execProc('PARSE_GS1_BARCODE', (artbarcode, '01', None, None, None))
        except Exception, e:
            cherrypy.log('Exception PPRINT_INFO_BARCODE2/PARSE_GS1_BARCODE for %s: %s' % (artbarcode, str(e)))
            return json.dumps({'error': not_found_msg, 'version': self.VERSION, 'e': str(e)})

        artbarcode = data[0]['VAL'] if len(data) else artbarcode

        if not listart:
            try:
                DB.execProc('GM_PRICECHECKER_ADDTASK2', (artbarcode, None, self.ifaceSes.client_ip, None, None), 'None')
            except Exception, e:
                cherrypy.log('Exception GM_PRICECHECKER_ADDTASK2 for %s: %s' % (artbarcode, str(e)))
            finally:
                return json.dumps({'error': not_found_msg, 'version': self.VERSION, 'e': 'not listart'})

        if listart[0]['MODE'] != 'ART':
            return json.dumps({'error': not_found_msg, 'version': self.VERSION, 'e': 'mode != art'})

        id_art = listart[0]['ID']
        weight = listart[0]['WEIGHT']
        try:
            getid = DB.execProc('GM_PRICECHECKER_ADDTASK2', (artbarcode, id_art, self.ifaceSes.client_ip, None, None))
            data = DB.execProc('PPRINT_INFO_ART', (id_art, weight))
        except Exception, e:
            cherrypy.log('Exception GM_PRICECHECKER_ADDTASK2/PPRINT_INFO_ART for %s %s %s: %s' % (artbarcode, id_art, weight, str(e)))
            return json.dumps({'error': not_found_msg, 'version': self.VERSION, 'e': str(e)})

        self.ifaceSes.id_sharttask = getid[0]['ID_SHARTTASK']

        split_price = price_to_parts(data[0]['PRICE'])
        split_price_w = price_to_parts(data[0]['PRICEW'])

        return json.dumps({
            'price': data[0]['PRICESTR'].decode('cp1251'),  # строка за ед
            'pricew': data[0]['PRICESTRW'].decode('cp1251'),  # строка за вес

            'split_price_r': split_price[0],
            'split_price_k': split_price[1],
            'split_price_w_r': split_price_w[0],
            'split_price_w_k': split_price_w[1],

            'unit': data[0]['UNIT'].decode('cp1251'),
            'unit_ex': (data[0].get('UNIT_EX') or data[0]['UNIT']).decode('cp1251'),
            'artname': data[0]['NAME'].decode('cp1251'),
            'isweight': data[0]['isweight'],
            'rest': round(data[0].get('REST') or 0, 3),
            'weight': weight, 'id_art': id_art, 'artbarcode': artbarcode,

            # 'price_audio': self.price_audio(data[0]['PRICEW']),

            'version': self.VERSION
        })

    artbarcodeinfo.exposed = True


    def taskAction(self, artbarcode=None, id_art=None, weight=None, **kwargs):
        u"""
        Отображение информации по товару по его ШК для Windows

        Args:
            artbarcode (str): ШК товара
            id_art (int): id товара
            weight (float): вес товара

        Returns:
            Возвращается шаблон ``index_android`` или ``task`` в зависимости от
            используемого устройства (андроид или нет)
        """

        if is_android(cherrypy.request.headers):
            template = tmpl.index_android
        else:
            template = tmpl.task

        if not hasattr(self.session, 'FB_user'):
            self.session.FB_user = CONFIG.get('db', 'user')
            self.session.FB_password = CONFIG.get('db', 'pass')
            self.ifaceSes.client_ip = cherrypy.request.remote.ip

        if not id_art and not artbarcode:
            return template(listart=None, artname=None, jsbodyload='init()')

        if artbarcode:
            self.ifaceSes.barcode = artbarcode

        if not id_art:
            try:
                listart = DB.execProc('PPRINT_INFO_BARCODE2', (artbarcode, None, None, None))
                data = DB.execProc('PARSE_GS1_BARCODE', (artbarcode, '01', None, None, None))
            except Exception, e:
                cherrypy.log('Exception PPRINT_INFO_BARCODE2/PARSE_GS1_BARCODE for %s: %s' % (artbarcode, str(e)))
                return template(
                    listart=None, artname=None, jsbodyload='init()',
                    mes='Товар по штрих-коду не найден. Обратитесь на сервисную службу за информацией [1]',
                )

            shortbarcode = data[0]['VAL'] if data else artbarcode

            self.ifaceSes.barcode = shortbarcode

            if not listart:
                try:
                    DB.execProc('GM_PRICECHECKER_ADDTASK2', (shortbarcode, None, self.ifaceSes.client_ip, None, None), 'None')
                except Exception, e:
                    cherrypy.log('Exception GM_PRICECHECKER_ADDTASK2 for %s: %s' % (shortbarcode, str(e)))
                finally:
                    return template(
                        listart=None, artname=None, jsbodyload='init()',
                        mes='Товар по штрих-коду не найден. Обратитесь на сервисную службу за информацией [2]',
                    )
            #if len(listart) > 1:
            #    return template(listart=listart, artname=None, jsbodyload='init()')

            if listart[0]['MODE'] != 'ART':
                return template(
                    listart=None, artname=None, jsbodyload='init()',
                    mes='Товар по штрих-коду не найден. Обратитесь на сервисную службу за информацией [3]',
                )

            id_art = listart[0]['ID']
            weight = listart[0]['WEIGHT']

        if id_art:
            try:
                getid = DB.execProc('GM_PRICECHECKER_ADDTASK2', (self.ifaceSes.barcode, id_art, self.ifaceSes.client_ip, None, None))
                data = DB.execProc('PPRINT_INFO_ART', (id_art, weight))
            except Exception, e:
                cherrypy.log('Exception GM_PRICECHECKER_ADDTASK2/PPRINT_INFO_ART for %s %s %s: %s' % (self.ifaceSes.barcode, id_art, weight, str(e)))
                return template(
                    listart=None, artname=None, jsbodyload='init()',
                    mes='Товар по штрих-коду не найден. Обратитесь на сервисную службу за информацией [4]',
                )

            self.ifaceSes.id_sharttask = getid[0]['ID_SHARTTASK']

            split_price = price_to_parts(data[0]['PRICE'])
            split_price_w = price_to_parts(data[0]['PRICEW'])

            return template(
                listart=None,
                price=data[0]['PRICESTR'],  # строка за ед
                pricew=data[0]['PRICESTRW'],  # строка за вес

                split_price_r=split_price[0],
                split_price_k=split_price[1],
                split_price_w_r=split_price_w[0],
                split_price_w_k=split_price_w[1],

                unit=data[0]['UNIT'],
                unit_ex=data[0].get('UNIT_EX') or data[0]['UNIT'],

                artname=data[0]['NAME'],
                isweight=data[0]['isweight'], weight=weight, jsbodyload='init()'
            )

        return template(listart=None, artname=None, jsbodyload='init()')

    taskAction.exposed = True

    def price_audio(self, price, js=0, **kwargs):
        u"""
        Генерация аудиофайла для цены

        Args:
            price (float): цена, для которой будет сгенерирован аудиофайл

        Returns:
            dict: {
                * success (bool): успешность генерации аудиофайла
                * url (str): путь до сгенерированного аудиофайла
                * error (st): текст ошибки
            }

        Note:
            Генерация аудиофайла происходит только при отсутствии его на
            диске. Таким образом при замене аудиоисходников необходимо очистить
            кеш сгенерированных аудиофайлов цен на диске.

        Warnings:
            Для генерации аудиофайлов используется доработанная для python2.5
            версия ``pydub``. Оригинальную версию использовать нельзя.

        """
        try:
            res = DB.execSql("SELECT C(VBOOL) AS RES FROM CONFIGPRICE WHERE NAME = 'VOICEPLCHECK'", (), 'one')
            if res and res['RES'].strip() != '1':
                res = {'success': False, 'url': None, 'error': 'VOICEPLCHECK in CONFIGPRICE not set to "1"'}
                return json.dumps(res) if js else res
        except Exception:
            # в случае проблем с БД должна генерация должна быть включена
            pass

        if '.' in str(price) and int(str(price).split('.')[-1]) == 0:
            price = '%d' % int(float(price))
        else:
            price = '%0.2f' % float(price)

        filepath = '/usr/local/tander/libexec/tsdserver/static/audioprice/'
        filename = '%s/%s.wav' % (filepath, price)
        fileurl = '/audioprice/%s.wav' % price
        if os.path.exists(filename):
            res = {'success': True, 'url': fileurl, 'error': None}
            return json.dumps(res) if js else res

        try:
            from pydub import AudioSegment
        except ImportError, e:
            res = {'success': False, 'url': None, 'error': str(e)}
            return json.dumps(res) if js else res

        try:
            if '.' in price:
                res = decimal2text(
                    decimal.Decimal(price),
                    int_units=((u'rub', u'rub2', u'rub1'), 'm'),
                    exp_units=((u'kop', u'kop2', u'kop1'), 'f')
                )
            else:
                res = num2text(int(price), ((u'rub', u'rub2', u'rub1'), 'm'))

            waves = [
                '/usr/local/tander/libexec/tsdserver/modules/PRICECHECK/audiosrc/%s.wav' % x
                for x in res.split(' ') if x
            ]

            segments = [AudioSegment.from_wav(x) for x in waves]
            playlist = segments.pop(0)
            for song in segments:
                # playlist = playlist.append(AudioSegment.silent(duration=100), crossfade=0)
                playlist = playlist.append(song, crossfade=0)

            if not os.path.exists(filepath):
                os.makedirs(filepath)

            playlist.export(filename, format="wav")
            res = {'success': True, 'url': fileurl, 'error': None}
            return json.dumps(res) if js else res
        except Exception, e:
            res = {'success': False, 'url': None, 'error': str(e)}
            return json.dumps(res) if js else res

    price_audio.exposed = True

    def log(self, m='', **kwargs):
        with open('/var/log/tsd_front.log', 'a') as f:
            f.write('%s > %s\n' % (cherrypy.request.remote.ip, m))

    log.exposed = True
################################################################################
