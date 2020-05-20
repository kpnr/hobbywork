# -*- coding: utf-8 -*-
_endpoints = set(["gettelegaAction"])

def gettelegaAction():
    request = container.REQUEST
    response = request.RESPONSE
    outurl = request.get(str('outurl'))
    tcode = request.get(str('tcode'), str(''))
    uid = request.get(str('uid'))
    tid = request.get(str('tid'))
    tovarid = request.get(str('tovarid'))
    printtid = request.get(str('printtid'))
    printersk = request.get(str('printersk'), str('')) or str('')
    labelbarcode = request.get(str('labelbarcode'))
    id_shtask = request.get(str('id_shtask'))
    id_cart = request.get(str('id_cart'))
    act = request.get(str('act'))
    err = str('')
    if act == str('prn_printervalidate'):
        if id_shtask and id_cart and printersk != str(''
            ) and labelbarcode is not None:
            res = container.GM_GETPALLET_PRINTCART(ID_SHTASK=id_cart, ID_EMPL=
                uid, PRINTERBARCODE=printersk, LABELBARCODE=labelbarcode)
            if not len(res):
                act = str('prn_printersk')
                err = str('Произошла ошибка')
            elif res[0].MES:
                act = str('prn_printersk')
                err = res[0].MES
            else:
                container.GM_GETPALLET_FINISHTASK(ID_SHTASK=id_shtask)
                return response.redirect(outurl.decode(str('base64')))
        else:
            act = str('prn_printersk')
            err = str('Не указана этикетка')
    if act == str('prn_printersk'):
        if id_shtask and id_cart and printersk != str(''):
            if not err:
                res = container.GM_GETPALLET_PRINTCART(ID_SHTASK=id_cart,
                    ID_EMPL=uid, PRINTERBARCODE=printersk, LABELBARCODE=None)
                if not len(res) or res[0].MES:
                    act = str('wantprint')
                    err = res[0].MES
            if act == str('prn_printersk'):
                return container.frm_printervalidate(err=err, printersk=
                    printersk, id_cart=id_cart, id_shtask=id_shtask, tcode=tcode)
        else:
            act = str('wantprint')
            err = str('Неверный ШК принтера')
    if act == str('viewtelega'):
        if tid and id_shtask:
            tovarlist0 = container.GM_GETPALLET_CART_ARTS(ID_SHTASKP=id_shtask,
                ID_SHTASKT=tid, MODE=0) or None
            tovarlist1 = container.GM_GETPALLET_CART_ARTS(ID_SHTASKP=id_shtask,
                ID_SHTASKT=tid, MODE=1) or None
            tovarlist2 = container.GM_GETPALLET_CART_ARTS(ID_SHTASKP=id_shtask,
                ID_SHTASKT=tid, MODE=2) or None
            err = None
            return container.frm_listTovar(id_shtask=id_shtask, t_ok=tovarlist0,
                t_diff=tovarlist1, tnumber=request.get(str('tnumber')),
                t_notscaned=tovarlist2, tid=tid, tcode=tcode, err=err)
    if act == str('wantprint'):
        if id_shtask and id_cart:
            return container.frm_SRCHgetPrinterSk(err=err, id_shtask=id_shtask,
                id_cart=id_cart, tcode=tcode)
    currenttovar = None
    totalcnt = 0
    currname = None
    if tovarid and id_shtask:
        id = request.get(str('id'))
        res = container.GM_GET_ARTS_BARCODE(BARCODE=tovarid)
        if not len(res):
            err = str('Товар с таким ШК не найден')
        elif len(res) == 1:
            currenttovar = res[0]
        elif not id:
            return container.frm_doublearts(mes=str('Несколько товаров с ШК %s'
                ) % tovarid, data=res, id_shtask=id_shtask, tovarid=tovarid,
                tcode=tcode)
        else:
            res = [x for x in res if str(x.ID_ART) == id]
            if len(res) == 1:
                currenttovar = res[0]
        if currenttovar:
            totalcnt = container.GM_GETPALLET_ADDART(ID_SHTASK=id_shtask,
                ID_ART=currenttovar.ID_ART)
            if len(totalcnt):
                totalcnt = totalcnt[0].COUNTART
            currenttovar = currenttovar.NAME
    elif not id_shtask:
        id_shtask = container.GM_GETPALLET_STARTTASK(ID_EMPL=uid)[0].ID_SHTASK
    alltovar = container.GM_GETPALLET_CARTS(ID_SHTASKP=id_shtask, STTCODE=tcode
        ) or None
    return container.frm_listTelegs(err=err, id_shtask=id_shtask, totalcnt=
        totalcnt, currenttovar=currenttovar, alltovar=alltovar, tcode=tcode)

