# -*- coding: utf-8 -*-
_endpoints = set(["routeAction"])

def routeAction():
  request = container.REQUEST
  response = request.RESPONSE

  #===============================================================================
  # переменные окружения
  #===============================================================================

  tcode = request.get('tcode','') # тип кода
  uid = request.get('uid') # пользователь
  id_site = request.get('id_site') # ид экспедиции
  tid = request.get('tid','') # id телеги
  tovarid = request.get('tovarid') # шк товара
  printtid = request.get('printtid') # хотим печатать шк телеги
  printersk = request.get('printersk','') or '' # шк принтера
  labelbarcode = request.get('labelbarcode') # распечатаная этикетка
  id_shtask = request.get('id_shtask') # задание
  id_cart = request.get('id_cart')
  act = request.get('act')
  err = None
  id_route = request.get('id_route')
  date_out = request.get('date_out')

  #===============================================================================
  # погнали
  #===============================================================================

  ##<dtml-sqlvar ID_EMPL type="int" optional> 

  if act == 'scan1' or act == 'select_route':    
      if tid or act == 'scan1':        
          route = container.GM_CARTINCOME_ROUTES(BARCODE = tid,
                                              CHECK_TYPE = act,
                                              ID_ROUTE_IN = None,
                                              DATE_OUT = None)
          if len(route) and route[0].MES:request = container.REQUEST
  response = request.RESPONSE

  #===============================================================================
  # переменные окружения
  #===============================================================================

  tcode = request.get('tcode','') # тип кода
  uid = request.get('uid') # пользователь
  id_site = request.get('id_site') # ид экспедиции
  tid = request.get('tid','') # id телеги
  tovarid = request.get('tovarid') # шк товара
  printtid = request.get('printtid') # хотим печатать шк телеги
  printersk = request.get('printersk','') or '' # шк принтера
  labelbarcode = request.get('labelbarcode') # распечатаная этикетка
  id_shtask = request.get('id_shtask') # задание
  id_cart = request.get('id_cart')
  act = request.get('act')
  err = None
  id_route = request.get('id_route')
  date_out = request.get('date_out')

  #===============================================================================
  # погнали
  #===============================================================================

  ##<dtml-sqlvar ID_EMPL type="int" optional> 

  if act == 'scan1' or act == 'select_route':    
      if tid or act == 'scan1':        
          route = container.GM_CARTINCOME_ROUTES(BARCODE = tid,
                                              CHECK_TYPE = act,
                                              ID_ROUTE_IN = None,
                                              DATE_OUT = None)
          if len(route) and route[0].MES:
              err = route[0].MES
          if not err:
              id_route = route[0].ID_ROUTE
          else:
              route_list  = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN = None, DATE_OUT_CUR = None, CHECK_NOT_END_ROUTE = '1')
              return container.frm_listCarRoute(id_shtask = id_shtask, id_site = id_site, route_list = route_list, err = err)
      
      
      route_list  = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN = id_route, DATE_OUT_CUR = None, CHECK_NOT_END_ROUTE = '0')    
      return container.frm_setCarRoute(id_shtask = id_shtask, id_site = id_site, route_list = route_list, err = err, confirm = 0)

  if act == 'scan2':
      route = container.GM_CARTINCOME_ROUTES(BARCODE = tid,
                                              CHECK_TYPE = act,
                                              ID_ROUTE_IN = id_route,
                                              DATE_OUT = date_out)
      if len(route) and route[0].MES:
          err = route[0].MES
          date_out = None
      if not err:
          err = 'Для завершения работы с маршрутом, подтвердите отъезд'
          date_out = route[0].DATE_OUT_CURR
          
      route_list  = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN = id_route, DATE_OUT_CUR = date_out, CHECK_NOT_END_ROUTE = '0')    
      return container.frm_setCarRoute(id_shtask = id_shtask, id_site = id_site, route_list = route_list, err = err)
      
  if act == 'setdateout':
      route = container.GM_CARTINCOME_ROUTES(BARCODE = tid,
                                              CHECK_TYPE = act,
                                              ID_ROUTE_IN = id_route,
                                              DATE_OUT = date_out)
      return response.redirect('taskAction?uid=%s&id_site=%s&id_shtask=%s'%(request.uid, request.get('id_site'), request.get('id_shtask')))

  if act == 'start':
      route_list  = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN = None, DATE_OUT_CUR = date_out, CHECK_NOT_END_ROUTE = '1')
      return container.frm_listCarRoute(id_shtask = id_shtask, id_site = id_site, route_list = route_list, err = err)


