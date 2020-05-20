# -*- coding: utf-8 -*-
_endpoints = set(["taskAction"])

def taskAction():
    video_global_config, video_registrators = container.extconfig(str(
        'videoserver'), None)


    def sid(id_empl):
        r = container.SQL_TERMCONNECTION(ID_EMPL=id_empl)
        return r[0].ID_SHTERMCON


    request = container.REQUEST
    response = request.RESPONSE
    session = context.REQUEST.SESSION
    uid = request.get(str('uid'))
    mpsk = request.get(str('mpsk'))
    id_site = request.get(str('id_site'))
    id_shtask = request.get(str('id_shtask'))
    tid = request.get(str('tid'))
    opid = request.get(str('opid'))
    opnumber = request.get(str('opnumber'))
    endflag = request.get(str('endflag'))
    printersk = request.get(str('printersk'))
    endflagok = request.get(str('endflagok'))
    emptyconfirm = request.get(str('emptyconfirm'))
    BARCODENOTEX = request.get(str('BARCODENOTEX'))
    BARCODEEX = request.get(str('BARCODEEX'))
    cleansearch = request.get(str('cleansearch'))
    cleanshtask = request.get(str('cleanshtask'))
    trans_opid = request.get(str('trans_opid'))
    err = str('')
    warn = str('')
    if cleansearch and cleanshtask:
        container.GM_GETPALLET_FINISHTASK(ID_SHTASK=cleanshtask)
    if not mpsk and not id_site and not id_shtask:
        return container.frm_getExpeditionSk(err=err)
    if id_site and id_shtask and BARCODEEX and BARCODENOTEX:
        res = container.GM_CARTINCOME_CREATE(ID_EMPL=uid, BARCODEEX=BARCODEEX,
            BARCODE=BARCODENOTEX)
        if len(res) and res[0].MES:
            BARCODEEX = str('')
            emptyconfirm = 1
            err = res[0].MES
    if emptyconfirm and id_site and id_shtask and BARCODENOTEX and not BARCODEEX:
        return container.frm_regetTelegaSk(err=err, id_site=id_site, id_shtask=
            id_shtask, BARCODENOTEX=BARCODENOTEX)
    if not id_shtask and mpsk and not id_site:
        res = container.GM_GETSITE(BARCODE=mpsk)
        if not len(res) or res[0].CODETYPE != str('E'):
            return container.frm_getExpeditionSk(err=str(
                'Вы отсканировали не ШК местоположения'))
        r = container.GM_CARTINCOME_BEGIN(ID_EMPL=uid)
        if not len(r) or not r[0].ID_SHTASK:
            return container.frm_getExpeditionSk(err=str(
                'Ошибка при создании задания'))
        else:
            container.SH_JOINSITE(ID_SHTASK=r[0].ID_SHTASK, BARCODE=mpsk)
            id_shtask = r[0].ID_SHTASK
            id_site = res[0].ID_SITE
            if video_global_config[str('enabled')]:
                session[str('operation_id')] = container.NEW_GUID()[0][str('GUID')
                    ].strip()
                for video in video_registrators:
                    if container.videoRegistration(video[str('driver')]
                        ) is not None:
                        video_data = container.videoRegistration(video[str(
                            'driver')]).cartincome_begin(session[str(
                            'operation_id')], container.getUserName(uid=uid),
                            sid(uid), mpsk)
                        container.network(video[str('ip')], int(video[str(
                            'port')]), video_data)
    if id_site and opid and id_shtask:
        scanned_cartlist = container.GM_CARTINCOME_LISTCART(ID_EMPL=uid, ID_OP=opid
            ) or None
        return container.frm_listOpCartlist(cartlist=scanned_cartlist, opid=
            opid, id_shtask=id_shtask, id_site=id_site, opnumber=opnumber)
    if id_site and endflag and id_shtask:
        return container.frm_getPrinterSk(id_site=id_site, id_shtask=id_shtask)
    if id_site and printersk and id_shtask:
        container.GM_CARTINCOME_PRINT(ID_EMPL=uid, PRINTERBARCODE=printersk)
        return container.frm_finishYesNo(id_site=id_site, id_shtask=id_shtask)
    if id_site and endflagok and id_shtask:
        if video_global_config[str('enabled')]:
            oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid)
            cart_list = {}
            if oplist:
                for op in oplist:
                    cart_list[op[str('id_op')]] = container.GM_CARTINCOME_LISTCART(
                        ID_OP=op[str('id_op')], ID_EMPL=uid)
            site_barcode = container.GET_SITE_BARCODE(SITE_ID=id_site)
            if site_barcode and len(site_barcode) > 0:
                site_barcode = site_barcode[0][str('barcode')]
        res = container.GM_CARTINCOME_END(ID_SHTASK=id_shtask, BARCODESITE=id_site)
        err = None
        if len(res) and res[0].MES:
            err = res[0].MES
        id_site = str('')
        if not err and video_global_config[str('enabled')]:
            for video in video_registrators:
                if container.videoRegistration(video[str('driver')]) is not None:
                    video_data = container.videoRegistration(video[str('driver')]
                        ).cartincome_end(session[str('operation_id')],
                        container.getUserName(uid=uid), sid(uid), site_barcode)
                    container.network(video[str('ip')], int(video[str('port')]),
                        video_data)
            session.delete(str('operation_id'))
        return container.frm_getExpeditionSk(err=err)
    if id_site and id_shtask and tid and trans_opid:
        trans_id_shtask = request.get(str('trans_id_shtask'))
        trans_printersk = request.get(str('trans_printersk'))
        trans_label = request.get(str('trans_label'))
        if trans_id_shtask == str('None'):
            trans_id_shtask = str('')
        if trans_label:
            res = container.GM_GETPALLET_PRINTCART(ID_SHTASK=trans_id_shtask,
                ID_EMPL=uid, PRINTERBARCODE=trans_printersk, LABELBARCODE=
                trans_label)
            if not len(res):
                trans_label = None
                err = str('Произошла ошибка')
            elif res[0].MES:
                trans_label = None
                err = res[0].MES
            else:
                res = container.GM_CARTINCOME_ADD_TRANZ(ID_EMPL=uid, BARCODE=
                    tid, ID_OP=trans_opid)
                if len(res) and res[0].MES:
                    if res[0].MES in (str(
                        'В базе несколько тележек с таким ШК.'), str(
                        'Тележка не найдена в БД, добавлена.')):
                        warn = res[0].MES
                    if res[0].MES in str('Тележка уже принималась.'):
                        err = res[0].MES
                outurl = str('taskAction?uid=%s&id_site=%s&id_shtask=%s') % (uid,
                    id_site, id_shtask)
                outurl = outurl.encode(str('base64'))
                scanned_oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid
                    ) or None
                return container.frm_getTelegaSk(err=err, warn=warn, oplist=
                    scanned_oplist, id_site=id_site, id_shtask=id_shtask,
                    outurl=outurl)
        if trans_printersk and not trans_label:
            res = container.GM_GETPALLET_PRINTCART(ID_SHTASK=trans_id_shtask,
                ID_EMPL=uid, PRINTERBARCODE=trans_printersk, LABELBARCODE=None)
            if not len(res) or res[0].MES:
                err = res[0].MES
                trans_printersk = None
            else:
                return container.frm_transPrinterValidate(err=err, printersk=
                    printersk, id_site=id_site, id_shtask=id_shtask, tid=tid,
                    trans_opid=trans_opid, trans_id_shtask=trans_id_shtask,
                    trans_printersk=trans_printersk)
        if trans_id_shtask and not trans_label and not trans_printersk:
            return container.frm_getTransPrinterSk(err=err, id_site=id_site,
                id_shtask=id_shtask, tid=tid, trans_opid=trans_opid,
                trans_id_shtask=trans_id_shtask)
        if not trans_id_shtask:
            res = container.GM_CARTINCOME_ADD_TRANZ(ID_EMPL=uid, BARCODE=tid,
                ID_OP=trans_opid)
            if len(res) and res[0].MES:
                if res[0].MES in (str('В базе несколько тележек с таким ШК.'),
                    str('Тележка не найдена в БД, добавлена.')):
                    warn = res[0].MES
                if res[0].MES in str('Тележка уже принималась.'):
                    err = res[0].MES
            outurl = str('taskAction?uid=%s&id_site=%s&id_shtask=%s') % (uid,
                id_site, id_shtask)
            outurl = outurl.encode(str('base64'))
            scanned_oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid) or None
            return container.frm_getTelegaSk(err=err, warn=warn, oplist=
                scanned_oplist, id_site=id_site, id_shtask=id_shtask, outurl=outurl
                )
    if id_site and id_shtask and not opid and not trans_opid:
        if tid:
            op_number = None
            tranzinfo = container.GM_CARTINCOME_GETTASKINFO(BARCODE=tid)
            if len(tranzinfo) and tranzinfo[0].MES:
                err = tranzinfo[0].MES
            elif len(tranzinfo) and tranzinfo[0].TASKTYPE == str('TRANZ'):
                tranz_opnumber = tranzinfo[0].OPNUMBER
                tranz_num = tranzinfo[0].NUM
                tranz_mes = tranzinfo[0].MES
                op_number = tranz_opnumber
                res = container.GM_CARTINCOME_ADD_TRANZ(ID_EMPL=uid, BARCODE=
                    tid, ID_OP=None)
                if len(res) and res[0].MES in (str(
                    'В базе несколько тележек с таким ШК.'), str(
                    'Тележка не найдена в БД, добавлена.')):
                    warn = res[0].MES
                elif len(res) and res[0].MES == str('Выберите операцию.'):
                    res = container.GM_CARTINCOME_GETOPLISTFORTRANZ(VOPNUMBER=
                        tranz_opnumber, VNUMTASK=tranz_num)
                    return container.frm_getTransOpId(oplist=res, id_site=
                        id_site, id_shtask=id_shtask, tid=tid)
                elif len(res) and res[0].MES:
                    err = res[0].MES
            elif len(tranzinfo) and tranzinfo[0].TASKTYPE == str('USUAL'):
                op_number = container.GET_CART_OPNUMBER(CART_ID=tid)
                if op_number and len(op_number) > 0:
                    op_number = op_number[0][str('number')]
                res = container.GM_CARTINCOME_ADD(ID_EMPL=uid, BARCODE=tid)
                if len(res):
                    if res[0].MES and res[0].MES != str('Нет данных по тележке.'):
                        err = res[0].MES
                    elif res[0].MES == str('Нет данных по тележке.'):
                        return container.frm_emptyTelegaConfirm(err=res[0].MES,
                            id_site=id_site, id_shtask=id_shtask, BARCODENOTEX=tid)
                else:
                    err = str('Введен неверный ШК тележки')
            if video_global_config[str('enabled')] and not err:
                site_barcode = mpsk
                if site_barcode is None:
                    site_barcode = container.GET_SITE_BARCODE(SITE_ID=id_site)
                    if site_barcode and len(site_barcode) > 0:
                        site_barcode = site_barcode[0][str('barcode')]
                operations = [item[str('NUMBER')].strip() for item in container
                    .GET_CART_OPNUMBER(CART_ID=tid)]
                for video in video_registrators:
                    if container.videoRegistration(video[str('driver')]
                        ) is not None:
                        video_data = container.videoRegistration(video[str(
                            'driver')]).cartincome_cart(session[str(
                            'operation_id')], container.getUserName(uid=uid),
                            sid(uid), site_barcode, tid, operations)
                        container.network(video[str('ip')], int(video[str(
                            'port')]), video_data)
        outurl = str('taskAction?uid=%s&id_site=%s&id_shtask=%s') % (uid,
            id_site, id_shtask)
        outurl = outurl.encode(str('base64'))
        scanned_oplist = container.GM_CARTINCOME_LISTOP(ID_EMPL=uid) or None
        return container.frm_getTelegaSk(err=err, warn=warn, oplist=
            scanned_oplist, id_site=id_site, id_shtask=id_shtask, outurl=outurl)

