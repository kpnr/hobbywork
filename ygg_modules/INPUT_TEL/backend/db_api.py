# -*- coding: utf8 -*-
# Этот файл сгенерирован автоматически.


def CHECK_TELEGA_DATE(TASK_ID: int):
  """
Проверка даты операции тележки
  Output fields:
    IS_OLD: int
    OPDATE: datetime
  """
  rv = fetch_all("select 1 as is_old, op.opdate from sh_task tk left join operation op on op.ID_OP = tk.id_op where id_shtask = ? and op.opdate > current_timestamp - 30 ", TASK_ID)
  return rv


def getName(id_empl: str):
  """

  Output fields:
    NAME: str
  """
  rv = fetch_all("select NAME from SH_GETNAME(?)", ID_EMPL)
  return rv


def GET_CART_OPNUMBER(CART_ID: str):
  """
Получение номера операции по ID тележки
  Output fields:
    NUMBER: str
  """
  rv = fetch_all("SELECT OP.NUMBER FROM SH_TASK TK JOIN OPERATION OP ON OP.ID_OP = TK.ID_OP JOIN TRANSPORT_CART TC ON TC.ID_CART=TK.ID_CART WHERE TC.NUM_CART= ? ", CART_ID)
  return rv


def GET_SITE_BARCODE(SITE_ID: int):
  """
Проверка даты операции тележки
  Output fields:
    BARCODE: str
  """
  rv = fetch_all("SELECT BARCODE FROM SITE WHERE ID_SITE = ? ", SITE_ID)
  return rv


def GM_CARTINCOME_ADD(ID_EMPL: int, BARCODE: str):
  """

  Output fields:
    ID_SHTASK: int
    MES: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_ADD( ?, ? )", ID_EMPL, BARCODE)
  return rv


def GM_CARTINCOME_ADD_TRANZ(ID_EMPL: int, BARCODE: str, ID_OP: int=None):
  """

  Output fields:
    MES: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_ADD_TRANZ( ?, ?, ? )", ID_EMPL, BARCODE, ID_OP)
  return rv


def GM_CARTINCOME_BEGIN(ID_EMPL: int):
  """

  Output fields:
    ID_SHTASK: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_BEGIN( ? )", ID_EMPL)
  return rv


def GM_CARTINCOME_CREATE(ID_EMPL: int, BARCODEEX: str, BARCODE: str):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_CARTINCOME_CREATE( ?, ?, ? )", ID_EMPL, BARCODEEX, BARCODE)
  return rv


def GM_CARTINCOME_END(ID_SHTASK: int, BARCODESITE: int):
  """

  Output fields:
    MES: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_END( ?, ? )", ID_SHTASK, BARCODESITE)
  return rv


def GM_CARTINCOME_GETOPLISTFORTRANZ(VOPNUMBER: str, VNUMTASK: int):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_CARTINCOME_GETOPLISTFORTRANZ( ?, ? )", VOPNUMBER, VNUMTASK)
  return rv


def GM_CARTINCOME_GETTASKINFO(BARCODE: str):
  """

  Output fields:
    TASKTYPE: str
    OPNUMBER: str
    NUM: int
    MES: str
  """
  rv = fetch_all("select * from GM_CARTINCOME_GETTASKINFO( ? )", BARCODE)
  return rv


def GM_CARTINCOME_LISTCART(ID_OP: int, ID_EMPL: int):
  """

  Output fields:
    ID_SHTASK: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_LISTCART( ?, ? )", ID_OP, ID_EMPL)
  return rv


def GM_CARTINCOME_LISTOP(ID_EMPL: int):
  """

  Output fields:
    ID_OP: int
    OPNUMBER: str
    COUNTTEL: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_LISTOP( ? )", ID_EMPL)
  return rv


def GM_CARTINCOME_LIST_ROUTES(ID_ROUTE_IN: int, DATE_OUT_CUR: str, CHECK_NOT_END_ROUTE: str, RESERVED1: int=None, RESERVED2: int=None, RESERVED3: int=None):
  """
Получение списка маршрутов
  Output fields:
    ID_SHTASK: int
    NUMBER: int
    COUNTS: int
    COUNTNS: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_LIST_ROUTES( ?, ?, ?, ?, ?, ? )", ID_ROUTE_IN, DATE_OUT_CUR, CHECK_NOT_END_ROUTE, RESERVED1, RESERVED2, RESERVED3)
  return rv


def GM_CARTINCOME_PRINT(ID_EMPL: int, PRINTERBARCODE: str):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_CARTINCOME_PRINT( ?, ? )", ID_EMPL, PRINTERBARCODE)
  return rv


def GM_CARTINCOME_ROUTES(BARCODE: str, CHECK_TYPE: str, ID_ROUTE_IN: int, DATE_OUT: str, RESERVED1: int=None, RESERVED2: int=None, RESERVED3: int=None):
  """
Получение информации о маршруте
  Output fields:
    ID_SHTASK: int
    NUMBER: int
    COUNTS: int
    COUNTNS: int
  """
  rv = fetch_all("select * from GM_CARTINCOME_ROUTES( ?, ?, ?, ?, ?, ?, ? )", BARCODE, CHECK_TYPE, ID_ROUTE_IN, DATE_OUT, RESERVED1, RESERVED2, RESERVED3)
  return rv


def GM_CARTPUT_FINDART(BARCODE: str=None, ID_SHTASK: int=None):
  """
GM_CARTPUT_FINDART
  Output fields:
    
  """
  rv = fetch_all("select * from GM_GET_BARCODE_TASK( ?, ? )", BARCODE, ID_SHTASK)
  return rv


def GM_GETPALLET_ADDART(ID_SHTASK: int, ID_ART: int):
  """

  Output fields:
    COUNTART: int
  """
  rv = fetch_all("select * from GM_GETPALLET_ADDART ( ?, ? )", ID_SHTASK, ID_ART)
  return rv


def GM_GETPALLET_CARTS(ID_SHTASKP: int, STTCODE: str):
  """

  Output fields:
    ID_SHTASK: int
    NUMBER: int
    COUNTS: int
    COUNTNS: int
  """
  rv = fetch_all("select * from GM_GETPALLET_CARTS( ?, ? )", ID_SHTASKP, STTCODE)
  return rv


def GM_GETPALLET_CART_ARTS(ID_SHTASKP: int, ID_SHTASKT: int, MODE: int):
  """

  Output fields:
    ARTNAME: str
    ARTREST: int
  """
  rv = fetch_all("select * from GM_GETPALLET_CART_ARTS( ?, ?, ? )", ID_SHTASKP, ID_SHTASKT, MODE)
  return rv


def GM_GETPALLET_CHKBARCODE(BARCODE: str=None, ID_EMPL: int=None, ID_SHTASK: int=None, ID_PALLET: int=None):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from GM_GETPALLET_CHKBARCODE( ?, ?, ?, ? )", BARCODE, ID_EMPL, ID_SHTASK, ID_PALLET)
  return rv


def GM_GETPALLET_FINISHTASK(ID_SHTASK: int):
  """

  Output fields:
    SUCCESS: str
    MES: str
  """
  rv = fetch_all("select * from GM_GETPALLET_FINISHTASK( ? )", ID_SHTASK)
  return rv


def GM_GETPALLET_PRINTCART(ID_SHTASK: int, ID_EMPL: int, PRINTERBARCODE: str=None, LABELBARCODE: str=None):
  """

  Output fields:
    RET: int
    MES: str
  """
  rv = fetch_all("select * from GM_GETPALLET_PRINTCART( ?, ?, ?, ? )", ID_SHTASK, ID_EMPL, PRINTERBARCODE, LABELBARCODE)
  return rv


def GM_GETPALLET_STARTTASK(ID_EMPL: int):
  """

  Output fields:
    ID_SHTASK: int
  """
  rv = fetch_all("select * from GM_GETPALLET_STARTTASK ( ? ) ", ID_EMPL)
  return rv


def GM_GETSITE(ID_SITE: int=None, BARCODE: str=None):
  """

  Output fields:
    ID_SITE: int
    ID_SITETYPE: int
    ID_SITETYPETYPE: int
    CODETYPE: str
    CODETYPETYPE: str
    NAME: str
    FULLNAME: str
    NAMETYPE: str
    NAMETYPETYPE: str
  """
  rv = fetch_all("select * from GM_GETSITE( ?, ? )", ID_SITE, BARCODE)
  return rv


def GM_GET_ARTS_BARCODE(BARCODE: str):
  """

  Output fields:
    ID_ART: int
    NAME: str
  """
  rv = fetch_all("select ID_ART, NAME from GM_GET_ARTS_BARCODE( ? ) group by ID_ART, NAME", BARCODE)
  return rv


def GM_GET_BARCODE_TASK(BARCODE: str=None, ID_SHTASK: int=None):
  """

  Output fields:
    ID_ART: int
    ID_SHARTTASK: int
    NAME: str
    QUANTITY: int
    WORKQUANTITY: int
    BCQUANTITY: int
  """
  rv = fetch_all("select * from GM_GET_BARCODE_TASK( ?, ? )", BARCODE, ID_SHTASK)
  return rv


def NEW_GUID():
  """

  Output fields:
    GUID: str
  """
  rv = fetch_all("select rupper(createguid()) GUID from sh_config", )
  return rv


def SH_JOINSITE(ID_SHTASK: int, BARCODE: str):
  """

  Output fields:
    
  """
  rv = fetch_all("select * from SH_JOINSITE( ?, ? )", ID_SHTASK, BARCODE)
  return rv


def SQL_TERMCONNECTION(ID_EMPL: int):
  """

  Output fields:
    ID_SHTERMCON: int
  """
  rv = fetch_all("select max(ID_SHTERMCON) AS ID_SHTERMCON from SH_TERMCONNECTION where DISCONNECTTIME is null and ID_EMPL=?", ID_EMPL)
  return rv


