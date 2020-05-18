# -*- coding: utf8 -*-
# Этот файл сгенерирован автоматически.


def CHECK_TELEGA_DATE(task_id: int):
  """
Проверка даты операции тележки
  Output fields:
    is_old: int
    opdate: datetime
  """
  rv = fetch_all("select 1 as is_old, op.opdate from sh_task tk left join operation op on op.ID_OP = tk.id_op where id_shtask = ? and op.opdate > current_timestamp - 30 ", task_id)
  return rv


def getName(id_empl: str):
  """

  Output fields:
    name: str
  """
  rv = fetch_all("select NAME from SH_GETNAME(?)", id_empl)
  return rv


def GET_CART_OPNUMBER(cart_id: str):
  """
Получение номера операции по ID тележки
  Output fields:
    number: str
  """
  rv = fetch_all("SELECT OP.NUMBER FROM SH_TASK TK JOIN OPERATION OP ON OP.ID_OP = TK.ID_OP JOIN TRANSPORT_CART TC ON TC.ID_CART=TK.ID_CART WHERE TC.NUM_CART= ? ", cart_id)
  return rv


def GET_SITE_BARCODE(site_id: int):
  """
Проверка даты операции тележки
  Output fields:
    barcode: str
  """
  rv = fetch_all("SELECT BARCODE FROM SITE WHERE ID_SITE = ? ", site_id)
  return rv


def GM_CARTINCOME_ADD(id_empl: int, barcode: str):
  """

  Output fields:
    id_shtask: int
    mes: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_ADD( ?, ? )", id_empl, barcode)
  return rv


def GM_CARTINCOME_ADD_TRANZ(id_empl: int, barcode: str, id_op: int=None):
  """

  Output fields:
    mes: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_ADD_TRANZ( ?, ?, ? )", id_empl, barcode, id_op)
  return rv


def GM_CARTINCOME_BEGIN(id_empl: int):
  """

  Output fields:
    id_shtask: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_BEGIN( ? )", id_empl)
  return rv


def GM_CARTINCOME_CREATE(id_empl: int, barcodeex: str, barcode: str):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_CARTINCOME_CREATE( ?, ?, ? )", id_empl, barcodeex, barcode)
  return rv


def GM_CARTINCOME_END(id_shtask: int, barcodesite: int):
  """

  Output fields:
    mes: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_END( ?, ? )", id_shtask, barcodesite)
  return rv


def GM_CARTINCOME_GETOPLISTFORTRANZ(vopnumber: str, vnumtask: int):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_CARTINCOME_GETOPLISTFORTRANZ( ?, ? )", vopnumber, vnumtask)
  return rv


def GM_CARTINCOME_GETTASKINFO(barcode: str):
  """

  Output fields:
    tasktype: str
    opnumber: str
    num: int
    mes: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_GETTASKINFO( ? )", barcode)
  return rv


def GM_CARTINCOME_LISTCART(id_op: int, id_empl: int):
  """

  Output fields:
    id_shtask: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_LISTCART( ?, ? )", id_op, id_empl)
  return rv


def GM_CARTINCOME_LISTOP(id_empl: int):
  """

  Output fields:
    id_op: int
    opnumber: str
    counttel: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_LISTOP( ? )", id_empl)
  return rv


def GM_CARTINCOME_LIST_ROUTES(id_route_in: int, date_out_cur: str, check_not_end_route: str, reserved1: int=None, reserved2: int=None, reserved3: int=None):
  """
Получение списка маршрутов
  Output fields:
    id_shtask: int
    number: int
    counts: int
    countns: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_LIST_ROUTES( ?, ?, ?, ?, ?, ? )", id_route_in, date_out_cur, check_not_end_route, reserved1, reserved2, reserved3)
  return rv


def GM_CARTINCOME_PRINT(id_empl: int, printerbarcode: str):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_CARTINCOME_PRINT( ?, ? )", id_empl, printerbarcode)
  return rv


def GM_CARTINCOME_ROUTES(barcode: str, check_type: str, id_route_in: int, date_out: str, reserved1: int=None, reserved2: int=None, reserved3: int=None):
  """
Получение информации о маршруте
  Output fields:
    id_shtask: int
    number: int
    counts: int
    countns: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_ROUTES( ?, ?, ?, ?, ?, ?, ? )", barcode, check_type, id_route_in, date_out, reserved1, reserved2, reserved3)
  return rv


def GM_CARTPUT_FINDART(barcode: str=None, id_shtask: int=None):
  """
GM_CARTPUT_FINDART
  Output fields:
    
  """
  rv = fetch_all("select * from GM_GET_BARCODE_TASK( ?, ? )", barcode, id_shtask)
  return rv


def GM_GETPALLET_ADDART(id_shtask: int, id_art: int):
  """

  Output fields:
    countart: int
  """
  rv = fetch_all("select * from GM_GETPALLET_ADDART ( ?, ? )", id_shtask, id_art)
  return rv


def GM_GETPALLET_CARTS(id_shtaskp: int, sttcode: str):
  """

  Output fields:
    id_shtask: int
    number: int
    counts: int
    countns: int
  """
  rv = fetch_all("select * from GM_GETPALLET_CARTS( ?, ? )", id_shtaskp, sttcode)
  return rv


def GM_GETPALLET_CART_ARTS(id_shtaskp: int, id_shtaskt: int, mode: int):
  """

  Output fields:
    artname: str
    artrest: int
  """
  rv = fetch_all("select * from GM_GETPALLET_CART_ARTS( ?, ?, ? )", id_shtaskp, id_shtaskt, mode)
  return rv


def GM_GETPALLET_CHKBARCODE(barcode: str=None, id_empl: int=None, id_shtask: int=None, id_pallet: int=None):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_GETPALLET_CHKBARCODE( ?, ?, ?, ? )", barcode, id_empl, id_shtask, id_pallet)
  return rv


def GM_GETPALLET_FINISHTASK(id_shtask: int):
  """

  Output fields:
    success: str
    mes: str
  """
  rv = fetch_all("select * from GM_GETPALLET_FINISHTASK( ? )", id_shtask)
  return rv


def GM_GETPALLET_PRINTCART(id_shtask: int, id_empl: int, printerbarcode: str=None, labelbarcode: str=None):
  """

  Output fields:
    ret: int
    mes: str
  """
  rv = fetch_all("select * from GM_GETPALLET_PRINTCART( ?, ?, ?, ? )", id_shtask, id_empl, printerbarcode, labelbarcode)
  return rv


def GM_GETPALLET_STARTTASK(id_empl: int):
  """

  Output fields:
    id_shtask: int
  """
  rv = fetch_all("select * from GM_GETPALLET_STARTTASK ( ? ) ", id_empl)
  return rv


def GM_GETSITE(id_site: int=None, barcode: str=None):
  """

  Output fields:
    id_site: int
    id_sitetype: int
    id_sitetypetype: int
    codetype: str
    codetypetype: str
    name: str
    fullname: str
    nametype: str
    nametypetype: str
  """
  rv = fetch_all("select * from GM_GETSITE( ?, ? )", id_site, barcode)
  return rv


def GM_GET_ARTS_BARCODE(barcode: str):
  """

  Output fields:
    id_art: int
    name: str
  """
  rv = fetch_all("select ID_ART, NAME from GM_GET_ARTS_BARCODE( ? ) group by ID_ART, NAME", barcode)
  return rv


def GM_GET_BARCODE_TASK(barcode: str=None, id_shtask: int=None):
  """

  Output fields:
    id_art: int
    id_sharttask: int
    name: str
    quantity: int
    workquantity: int
    bcquantity: int
  """
  rv = fetch_all("select * from GM_GET_BARCODE_TASK( ?, ? )", barcode, id_shtask)
  return rv


def NEW_GUID():
  """

  Output fields:
    guid: str
  """
  rv = fetch_all("select rupper(createguid()) GUID from sh_config", )
  return rv


def SH_JOINSITE(id_shtask: int, barcode: str):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from SH_JOINSITE( ?, ? )", id_shtask, barcode)
  return rv


def SQL_TERMCONNECTION(id_empl: int):
  """

  Output fields:
    id_shtermcon: int
  """
  rv = fetch_all("select max(ID_SHTERMCON) AS ID_SHTERMCON from SH_TERMCONNECTION where DISCONNECTTIME is null and ID_EMPL=?", id_empl)
  return rv


