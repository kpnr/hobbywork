# -*- coding: utf-8 -*-
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
  #ast = py_parse(test_src, 'zope_script_file.py', 'exec')
  ast = py_parse(src, 'zope_script_file.py', 'exec')
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

test_src="""#Получаем настройки для видеофиксации
video_global_config, video_registrators = container.extconfig('videoserver', None)


def sid(id_empl):
  r = container.SQL_TERMCONNECTION(ID_EMPL=id_empl)
  return r[0].ID_SHTERMCON

request = container.REQUEST
response = request.RESPONSE
session = context.REQUEST.SESSION

#===============================================================================
# переменные окружения
#===============================================================================
uid = request.get('uid') # пользователь
mpsk = request.get('mpsk')# or option_mpsk# шк МП / экспедиции
id_site = request.get('id_site') # ид экспедиции
id_shtask = request.get('id_shtask') # код созданного задания 'INPUT_TEL'
tid = request.get('tid') # шк телеги
opid = request.get('opid') # ид операции для просмотра отсканированных телег по ней
opnumber = request.get('opnumber') # номер документа для просмотра телег по нему
endflag = request.get('endflag') # хотим завершить всё
printersk = request.get('printersk') # шк принтера
endflagok = request.get('endflagok') # реально всё завершаем и переходим в начало
emptyconfirm = request.get('emptyconfirm') # добавить ли телегу без данных через скан другой телеги?
BARCODENOTEX = request.get('BARCODENOTEX')
BARCODEEX = request.get('BARCODEEX')

cleansearch = request.get('cleansearch')
cleanshtask = request.get('cleanshtask')

trans_opid = request.get('trans_opid')

err = ''
warn = ''

#===============================================================================
# погнали
#===============================================================================

# VIDEO TEST
#if (video_global_config['enabled']):
#    for video in video_registrators:
#        if (container.videoRegistration(video['driver']) is not None):
#            video_data = container.videoRegistration(video['driver']).cartincome_begin(container.getUserName(uid=uid), None, '')
#            container.network(video['ip'], int(video['port']), video_data)


if cleansearch and cleanshtask:
    container.GM_GETPALLET_FINISHTASK(ID_SHTASK=cleanshtask)


# если нет ни ид ни шк МП — нужно отсканировать
if not mpsk and not id_site and not id_shtask:
    return container.frm_getExpeditionSk(err=err)


# добавляем телегу через скан другой телеги
if id_site and id_shtask and BARCODEEX and BARCODENOTEX:
    # ok
    res = container.GM_CARTINCOME_CREATE(ID_EMPL=uid, BARCODEEX=BARCODEEX, BARCODE=BARCODENOTEX)
    if len(res) and res[0].MES:
        BARCODEEX = ''
        emptyconfirm = 1
        err = res[0].MES

# хотим отсканировать другую телегу из прихода
if emptyconfirm and id_site and id_shtask and BARCODENOTEX and not BARCODEEX:
    return container.frm_regetTelegaSk(err=err, id_site=id_site, id_shtask=id_shtask, BARCODENOTEX=BARCODENOTEX)



# есть шк МП, еще нет его id, пытаемся получить
if not id_shtask and mpsk and not id_site:
    # ok
    res = container.GM_GETSITE(BARCODE=mpsk)
    
    if not len(res) or res[0].CODETYPE != 'E':
        return container.frm_getExpeditionSk(err='Вы отсканировали не ШК местоположения') 
    r = container.GM_CARTINCOME_BEGIN(ID_EMPL=uid)
    if not len(r) or not r[0].ID_SHTASK:
        return container.frm_getExpeditionSk(err='Ошибка при создании задания')
    else:
        container.SH_JOINSITE(ID_SHTASK=r[0].ID_SHTASK, BARCODE=mpsk)
        id_shtask = r[0].ID_SHTASK
        id_site = res[0].ID_SITE
        
        if (video_global_config['enabled']):
            session['operation_id'] = container.NEW_GUID()[0]['GUID'].strip()
            for video in video_registrators:
                if (container.videoRegistration(video['driver']) is not None):
                    video_data = container.videoRegistration(video['driver']).cartincome_begin(session['operation_id'], container.getUserName(uid=uid), sid(uid), mpsk)
                    container.network(video['ip'], int(video['port']), video_data)


# просмотр отсканированных телег по операции
if id_site and opid and id_shtask:
    # ok
    scanned_cartlist = container.GM_CARTINCOME_LISTCART(ID_EMPL=uid, ID_OP=opid) or None
    return container.frm_listOpCartlist(cartlist=scanned_cartlist, opid=opid, id_shtask=id_shtask, id_site=id_site, opnumber=opnumber)


# завершаем приемку — хотим получить шк принтера для распечатки отчета
if id_site and endflag and id_shtask:
    return container.frm_getPrinterSk(id_site=id_site, id_shtask=id_shtask)


# завершаем приемку — имеем шк принтера, запускаем отчет, хотим подтверждения завершения
if id_site and printersk and id_shtask:
    container.GM_CARTINCOME_PRINT(ID_EMPL=uid, PRINTERBARCODE=printersk)
    return container.frm_finishYesNo(id_site=id_site, id_shtask=id_shtask)
    

# реально завершаем приемку и переходим в начало
if id_site and endflagok and id_shtask:
    # ok
    # Для видео-фиксации получим список операций и список тележек по каждой операции
    if (video_global_config['enabled']):
        oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid)
        cart_list = {}
        if (oplist):
            for op in oplist:
                cart_list[op['id_op']] = container.GM_CARTINCOME_LISTCART(ID_OP=op['id_op'], ID_EMPL=uid)
        site_barcode = container.GET_SITE_BARCODE(SITE_ID=id_site)
        if (site_barcode and len(site_barcode) > 0):
            site_barcode = site_barcode[0]['barcode']
    
    res = container.GM_CARTINCOME_END(ID_SHTASK=id_shtask, BARCODESITE=id_site)
    err = None
    if len(res) and res[0].MES:
        err = res[0].MES
    id_site = ''

    # Фиксируем видео-инфу
    if (not err and video_global_config['enabled']):
         for video in video_registrators:
                 if (container.videoRegistration(video['driver']) is not None):
                     video_data = container.videoRegistration(video['driver']).cartincome_end(session['operation_id'], container.getUserName(uid=uid), sid(uid), site_barcode)
                     container.network(video['ip'], int(video['port']), video_data)
         session.delete('operation_id')
    return container.frm_getExpeditionSk(err=err)


# определили OPID транзитной операции
if id_site and id_shtask and tid and trans_opid:
    trans_id_shtask = request.get('trans_id_shtask')
    trans_printersk = request.get('trans_printersk')
    trans_label = request.get('trans_label')

    if trans_id_shtask == 'None':
        trans_id_shtask = ''

    if trans_label:
        res  = container.GM_GETPALLET_PRINTCART(
            ID_SHTASK=trans_id_shtask, ID_EMPL=uid,
            PRINTERBARCODE=trans_printersk, LABELBARCODE=trans_label
        )
        if not len(res):
            trans_label = None
            err = 'Произошла ошибка'
        elif res[0].MES:
            trans_label = None
            err = res[0].MES
        else:
            res = container.GM_CARTINCOME_ADD_TRANZ(ID_EMPL=uid, BARCODE=tid, ID_OP=trans_opid)
            if len(res) and res[0].MES:
                if res[0].MES in ('В базе несколько тележек с таким ШК.',
                                  'Тележка не найдена в БД, добавлена.'):
                    warn = res[0].MES
                if res[0].MES in ('Тележка уже принималась.'):
                    err = res[0].MES
            outurl = 'taskAction?uid=%s&id_site=%s&id_shtask=%s' % (uid, id_site, id_shtask)
            outurl = outurl.encode('base64')
            scanned_oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid) or None
            return container.frm_getTelegaSk(
                err=err, warn=warn, oplist=scanned_oplist, id_site=id_site,
                id_shtask=id_shtask, outurl=outurl
            )

    if trans_printersk and not trans_label:
        res = container.GM_GETPALLET_PRINTCART(
            ID_SHTASK=trans_id_shtask, ID_EMPL=uid,
            PRINTERBARCODE=trans_printersk, LABELBARCODE=None
        )
        if not len(res) or res[0].MES:
            err = res[0].MES
            trans_printersk = None
        else:
            return container.frm_transPrinterValidate(
                err=err, printersk=printersk, id_site=id_site, id_shtask=id_shtask, tid=tid,
            trans_opid=trans_opid, trans_id_shtask=trans_id_shtask, trans_printersk=trans_printersk
            )

    if trans_id_shtask and not trans_label and not trans_printersk:
        return container.frm_getTransPrinterSk(
            err=err, id_site=id_site, id_shtask=id_shtask, tid=tid,
            trans_opid=trans_opid, trans_id_shtask=trans_id_shtask
        )

    if not trans_id_shtask:
        res = container.GM_CARTINCOME_ADD_TRANZ(ID_EMPL=uid, BARCODE=tid, ID_OP=trans_opid)
        if len(res) and res[0].MES:
            if res[0].MES in ('В базе несколько тележек с таким ШК.',
                              'Тележка не найдена в БД, добавлена.'):
                warn = res[0].MES
            if res[0].MES in ('Тележка уже принималась.'):
                err = res[0].MES
        outurl = 'taskAction?uid=%s&id_site=%s&id_shtask=%s' % (uid, id_site, id_shtask)
        outurl = outurl.encode('base64')
        scanned_oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid) or None
        return container.frm_getTelegaSk(
            err=err, warn=warn, oplist=scanned_oplist, id_site=id_site,
            id_shtask=id_shtask, outurl=outurl
        )



# просто если есть ид мп — добавляем тележку (если указан шк тележки — tid) и выводим список тележек
if id_site and id_shtask and not opid and not trans_opid:
    if tid:
        op_number = None
        # обработка транзитных тележек
        tranzinfo = container.GM_CARTINCOME_GETTASKINFO(BARCODE=tid)
        if len(tranzinfo) and tranzinfo[0].MES:
            err = tranzinfo[0].MES
        elif len(tranzinfo) and tranzinfo[0].TASKTYPE == 'TRANZ':
            tranz_opnumber = tranzinfo[0].OPNUMBER
            tranz_num = tranzinfo[0].NUM
            tranz_mes = tranzinfo[0].MES
            op_number = tranz_opnumber
            res = container.GM_CARTINCOME_ADD_TRANZ(ID_EMPL=uid, BARCODE=tid, ID_OP=None)
            if len(res) and res[0].MES in (
                'В базе несколько тележек с таким ШК.',
                'Тележка не найдена в БД, добавлена.'
            ):
                warn = res[0].MES
            elif len(res) and res[0].MES == 'Выберите операцию.':
                res = container.GM_CARTINCOME_GETOPLISTFORTRANZ(
                    VOPNUMBER=tranz_opnumber, VNUMTASK=tranz_num
                )
                return container.frm_getTransOpId(
                    oplist=res, id_site=id_site, id_shtask=id_shtask, tid=tid
                )
            elif len(res) and res[0].MES:
                err = res[0].MES

        elif len(tranzinfo) and tranzinfo[0].TASKTYPE == 'USUAL':
            op_number = container.GET_CART_OPNUMBER(CART_ID=tid)
            if (op_number and len(op_number) > 0):
                op_number = op_number[0]['number']
            res = container.GM_CARTINCOME_ADD(ID_EMPL=uid, BARCODE=tid)
            if len(res):
                if res[0].MES and res[0].MES != 'Нет данных по тележке.':
                    err = res[0].MES
                elif res[0].MES == 'Нет данных по тележке.':
                    return container.frm_emptyTelegaConfirm(
                        err=res[0].MES, id_site=id_site, id_shtask=id_shtask,
                        BARCODENOTEX=tid
                        )
            else:
                err = 'Введен неверный ШК тележки'

        if (video_global_config['enabled'] and not err):
            site_barcode = mpsk
            if (site_barcode is None):
                site_barcode = container.GET_SITE_BARCODE(SITE_ID=id_site)
                if (site_barcode and len(site_barcode) > 0):
                    site_barcode = site_barcode[0]['barcode']
            operations = [item['NUMBER'].strip() for item in container.GET_CART_OPNUMBER(CART_ID = tid)]

            for video in video_registrators:
                if (container.videoRegistration(video['driver']) is not None):
                    video_data = container.videoRegistration(video['driver']).cartincome_cart(session['operation_id'], container.getUserName(uid=uid), sid(uid), site_barcode, tid, operations)
                    container.network(video['ip'], int(video['port']), video_data)

    outurl = 'taskAction?uid=%s&id_site=%s&id_shtask=%s' % (uid, id_site, id_shtask)
    outurl = outurl.encode('base64')

    scanned_oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid) or None

    return container.frm_getTelegaSk(
        err=err, warn=warn, oplist=scanned_oplist, id_site=id_site,
        id_shtask=id_shtask, outurl=outurl
    )
"""
