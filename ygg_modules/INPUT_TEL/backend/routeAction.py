# -*- coding: utf-8 -*-
_endpoints = set(["routeAction"])

def routeAction():
    request = container.REQUEST
    response = request.RESPONSE
    tcode = request.get(str('tcode'), str(''))
    uid = request.get(str('uid'))
    id_site = request.get(str('id_site'))
    tid = request.get(str('tid'), str(''))
    tovarid = request.get(str('tovarid'))
    printtid = request.get(str('printtid'))
    printersk = request.get(str('printersk'), str('')) or str('')
    labelbarcode = request.get(str('labelbarcode'))
    id_shtask = request.get(str('id_shtask'))
    id_cart = request.get(str('id_cart'))
    act = request.get(str('act'))
    err = None
    id_route = request.get(str('id_route'))
    date_out = request.get(str('date_out'))
    if act == str('scan1') or act == str('select_route'):
        if tid or act == str('scan1'):
            route = container.GM_CARTINCOME_ROUTES(BARCODE=tid, CHECK_TYPE=act,
                ID_ROUTE_IN=None, DATE_OUT=None)
            if len(route) and route[0].MES:
                request = container.REQUEST
    response = request.RESPONSE
    tcode = request.get(str('tcode'), str(''))
    uid = request.get(str('uid'))
    id_site = request.get(str('id_site'))
    tid = request.get(str('tid'), str(''))
    tovarid = request.get(str('tovarid'))
    printtid = request.get(str('printtid'))
    printersk = request.get(str('printersk'), str('')) or str('')
    labelbarcode = request.get(str('labelbarcode'))
    id_shtask = request.get(str('id_shtask'))
    id_cart = request.get(str('id_cart'))
    act = request.get(str('act'))
    err = None
    id_route = request.get(str('id_route'))
    date_out = request.get(str('date_out'))
    if act == str('scan1') or act == str('select_route'):
        if tid or act == str('scan1'):
            route = container.GM_CARTINCOME_ROUTES(BARCODE=tid, CHECK_TYPE=act,
                ID_ROUTE_IN=None, DATE_OUT=None)
            if len(route) and route[0].MES:
                err = route[0].MES
            if not err:
                id_route = route[0].ID_ROUTE
            else:
                route_list = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN=
                    None, DATE_OUT_CUR=None, CHECK_NOT_END_ROUTE=str('1'))
                return container.frm_listCarRoute(id_shtask=id_shtask, id_site=
                    id_site, route_list=route_list, err=err)
        route_list = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN=id_route,
            DATE_OUT_CUR=None, CHECK_NOT_END_ROUTE=str('0'))
        return container.frm_setCarRoute(id_shtask=id_shtask, id_site=id_site,
            route_list=route_list, err=err, confirm=0)
    if act == str('scan2'):
        route = container.GM_CARTINCOME_ROUTES(BARCODE=tid, CHECK_TYPE=act,
            ID_ROUTE_IN=id_route, DATE_OUT=date_out)
        if len(route) and route[0].MES:
            err = route[0].MES
            date_out = None
        if not err:
            err = str('Для завершения работы с маршрутом, подтвердите отъезд')
            date_out = route[0].DATE_OUT_CURR
        route_list = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN=id_route,
            DATE_OUT_CUR=date_out, CHECK_NOT_END_ROUTE=str('0'))
        return container.frm_setCarRoute(id_shtask=id_shtask, id_site=id_site,
            route_list=route_list, err=err)
    if act == str('setdateout'):
        route = container.GM_CARTINCOME_ROUTES(BARCODE=tid, CHECK_TYPE=act,
            ID_ROUTE_IN=id_route, DATE_OUT=date_out)
        return response.redirect(str(
            'taskAction?uid=%s&id_site=%s&id_shtask=%s') % (request.uid,
            request.get(str('id_site')), request.get(str('id_shtask'))))
    if act == str('start'):
        route_list = container.GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN=None,
            DATE_OUT_CUR=date_out, CHECK_NOT_END_ROUTE=str('1'))
        return container.frm_listCarRoute(id_shtask=id_shtask, id_site=id_site,
            route_list=route_list, err=err)

