# -*- coding: utf-8 -*-
_endpoints = set(["gettelegaAction"])

def gettelegaAction():
  request = container.REQUEST
  response = request.RESPONSE

  #===============================================================================
  # переменные окружения
  #===============================================================================
  outurl = request.get('outurl')

  tcode = request.get('tcode','') # тип кода
  uid = request.get('uid') # пользователь
  #id_site = request.get('id_site') # ид экспедиции
  tid = request.get('tid') # id телеги
  tovarid = request.get('tovarid') # шк товара
  printtid = request.get('printtid') # хотим печатать шк телеги
  printersk = request.get('printersk','') or '' # шк принтера
  labelbarcode = request.get('labelbarcode') # распечатаная этикетка
  id_shtask = request.get('id_shtask') # задание
  id_cart = request.get('id_cart')
  act = request.get('act')
  err = ''

  #===============================================================================
  # погнали
  #===============================================================================

  ##<dtml-sqlvar ID_EMPL type="int" optional> 

  if act == 'prn_printervalidate':
      if id_shtask and id_cart and printersk != '' and labelbarcode is not None:
          # ok
          res  = container.GM_GETPALLET_PRINTCART(
                                           ID_SHTASK = id_cart,
                                           ID_EMPL = uid,
                                           PRINTERBARCODE = printersk, 
                                           LABELBARCODE = labelbarcode
                                           )
          if not len(res):
              act = 'prn_printersk'
              err = 'Произошла ошибка'
          elif res[0].MES:
              act = 'prn_printersk'
              err = res[0].MES
          else:
              # ok
              container.GM_GETPALLET_FINISHTASK(ID_SHTASK = id_shtask)
              return response.redirect(outurl.decode('base64'))
      else:
          act = 'prn_printersk'
          err = 'Не указана этикетка'

  if act == 'prn_printersk':
      if id_shtask and id_cart and printersk != '':
          # ok
          if not err:
              res = container.GM_GETPALLET_PRINTCART(ID_SHTASK = id_cart, ID_EMPL = uid, PRINTERBARCODE = printersk, LABELBARCODE = None)
              if not len(res) or res[0].MES:
                  act = 'wantprint'
                  err = res[0].MES
          
          if act == 'prn_printersk':
              return container.frm_printervalidate(
                                                   err = err, printersk = printersk, id_cart = id_cart, 
                                                   id_shtask = id_shtask, tcode = tcode)
      else:
          act = 'wantprint'
          err = 'Неверный ШК принтера'
          
          
  if act == 'viewtelega':
      if tid and id_shtask:
          # ok
          tovarlist0 = container.GM_GETPALLET_CART_ARTS(ID_SHTASKP = id_shtask, ID_SHTASKT = tid, MODE = 0) or None
          tovarlist1 = container.GM_GETPALLET_CART_ARTS(ID_SHTASKP = id_shtask, ID_SHTASKT = tid, MODE = 1) or None
          tovarlist2 = container.GM_GETPALLET_CART_ARTS(ID_SHTASKP = id_shtask, ID_SHTASKT = tid, MODE = 2) or None
          
          err = None
          #telegaDateCheck = container.CHECK_TELEGA_DATE(TASK_ID=request.get('tid'))
          #if (len(telegaDateCheck) > 0 and telegaDateCheck[0]['is_old'] == 1):
          #    err = 'Внимание! Тележка привязана к операции от ' + DateTime(str(telegaDateCheck[0]['opdate'])).strftime('%d.%m.%Y')

          return container.frm_listTovar(id_shtask = id_shtask, 
                                         t_ok = tovarlist0, t_diff = tovarlist1, tnumber = request.get('tnumber'),
                                         t_notscaned = tovarlist2, tid = tid, tcode = tcode, err=err
                                         )   


  if act == 'wantprint':
      if id_shtask and id_cart:
          return container.frm_SRCHgetPrinterSk(err = err, id_shtask = id_shtask, id_cart = id_cart, tcode = tcode)



  currenttovar = None
  totalcnt = 0
  currname = None
  if tovarid and id_shtask:
      id = request.get('id')
      # OK
      #GM_GET_BARCODE_TASK
      #GM_GET_ARTS_BARCODE
      res = container.GM_GET_ARTS_BARCODE(BARCODE = tovarid)
      if not len(res):
          err = 'Товар с таким ШК не найден'
      elif len(res) == 1:
          currenttovar = res[0]
      else:
          if not id:
              return container.frm_doublearts(
                                          mes = 'Несколько товаров с ШК %s' % tovarid, data = res,
                                          id_shtask = id_shtask,tovarid = tovarid, tcode = tcode
                                          )
          else:
              res = [x for x in res if str(x.ID_ART) == id]
              if len(res) == 1:
                  currenttovar = res[0]
      
      if currenttovar:
          totalcnt = container.GM_GETPALLET_ADDART(ID_SHTASK = id_shtask, ID_ART = currenttovar.ID_ART)
          if len(totalcnt):
              totalcnt = totalcnt[0].COUNTART
          currenttovar = currenttovar.NAME
          
  elif not id_shtask:
      # ok
      id_shtask = container.GM_GETPALLET_STARTTASK(ID_EMPL = uid)[0].ID_SHTASK

  #ok
  alltovar = container.GM_GETPALLET_CARTS(ID_SHTASKP = id_shtask, STTCODE = tcode) or None
  return container.frm_listTelegs(
                                  err = err, id_shtask = id_shtask, totalcnt = totalcnt,
                                  currenttovar = currenttovar, alltovar = alltovar, tcode = tcode)


