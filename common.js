var is_ie = (/msie/i.test(navigator.userAgent) && !/opera/i.test(navigator.userAgent));
var is_opera = (navigator.appName == 'Opera');

var __eventListeners = [];

function regEvent(instance, eventName, listener) {
    var listenerFn = listener;
    if (instance.addEventListener) {
        instance.addEventListener(eventName, listenerFn, false);
    } else if (instance.attachEvent) {
        //listenerFn = function () {
        //    listener(window.event);
        //};
        instance.attachEvent("on" + eventName, listener);
    } else {
        throw new Error("Event registration not supported");
    }
    var event = {instance: instance, name: eventName, listener: listenerFn};
    __eventListeners.push(event);
    return event;
}

function delEvent(event) {
    var instance = event.instance;
    if (instance.removeEventListener) {
        instance.removeEventListener(event.name, event.listener, false);
    } else if (instance.detachEvent) {
        instance.detachEvent("on" + event.name, event.listener);
    }
    for (var i = 0; i < __eventListeners.length; i++) {
        if (__eventListeners[i] == event) {
            __eventListeners.splice(i, 1);
            break;
        }
    }
}

function unregisterAllEvents() {
    while (__eventListeners.length > 0) {
        delEvent(__eventListeners[0]);
    }
}

//----------------------------------------------------------------
// Периодическая отправка запроса на сервер и обработка результатов
// Используется для ИТСД Опросы, Автопополнение
function periodicCheck(code, handler, destination) {
    var req;
    if (document.location.href.indexOf(code) != -1) return;
    if (document.location.href.indexOf('/index?termnum=') != -1 || document.location.href.indexOf('/?termnum=') != -1)
        return;
    if ((document.location.href.indexOf('/index?username=') != -1 || document.location.href.indexOf('/?username=') != -1) && document.location.search.indexOf('password=') == -1)
        return;
    if (document.location.href.indexOf('/index?userbarcode') != -1) return;
    if ((document.location.href.indexOf('/SURVEY') > -1) ||
            (document.location.href.indexOf('/PLCHECK') > -1) ||
            (document.location.href.indexOf('/PRICECHECK') > -1)){
        return;
    }

    if (window.XMLHttpRequest)
        req = new XMLHttpRequest();
    else if (window.ActiveXObject) {
        try {
            req = new ActiveXObject('Msxml2.XMLHTTP');
        } catch (e) {
        }
        try {
            req = new ActiveXObject('Microsoft.XMLHTTP');
        } catch (e) {
        }
    }

    if (code == "/PLCHECK") {
        host = document.location.host;
        i = document.location.href.indexOf(host) + host.length;
        url = document.location.href;
        url = url.substr(i);
        //url = url.replace("&","@");
        url = escape(url);
        destination = destination + "?url=" + url;
    }

    if (req) {
        req.open("POST", handler, true);
        req.onreadystatechange = function () {
            if (req.readyState == 4 && req.status == 200) {
                if (req.responseText) {
                    document.location.href = destination;
                }
                try {
                    req.onreadystatechange = null
                } catch (e) {
                    req.onreadystatechange = function () {
                    };
                }
                req = null;
            }
        };
        req.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        try {
            req.send();
        }
        catch (e) {}
    }
}

//----------------------------------------------------------------
var GValidElelments = new Array();
GValidElelments = ["SELECT", "INPUT", "A"];
var GElementsList = new Array();
var GIndex = 0;
var GIndexPrev = 0;
var GScanElementIdx = null;
var GOnlyScanElement = null;
var GScanElementForm;
var PrevStyle = null;
var ScannerPrefixCode = 0;
var GScaning = false;
var readyForFocus = 0;
var ScrollStep = 8;
var g_EnterKeyDownFlag = false;
var gs1_stacked = false;
var needUp = 0;
var scan = 0;
var prev_scancode = null;
var prev_gindex = 0;

//----------------------------------------------------------------
function isInteger(charCode) {
    return (charCode >= 48 && charCode <= 57);
}

function isFloat(charCode) {
    if (document.activeElement.value.indexOf('.') == -1) {
        return (charCode == 46 || isInteger(charCode));
    }
    return (isInteger(charCode));
}

function isSpecifyKey(charCode) {
    return (charCode < 31 || (charCode >= 37 && charCode <= 40));
}

function isInputControls(charCode) {
    return (charCode == 13 || charCode == 8 || charCode == 37 || charCode == 39);
}

function selectRange(elem, from, to) {
}

function CancelAction(e) {
    if (e.preventDefault) {
        //FF, Opera
        e.preventDefault();
        return false;
    }
    e.returnValue = false;
    //IE
}

function getKeyCode(event) {
    var keycode = event.charCode ? event.charCode : event.keyCode;
    return keycode;
}


////////Фильтры на инпуты/////////////////////////////////////////////////////
var pos = 0;
var prev_datetime_field = null;

function intFilter(e) {
    if (isInputControls(getKeyCode(e))) {
        return true;
    }
    if (!isInteger(getKeyCode(e))) {
        CancelAction(e);
    }
}

function floatFilter(e) {
    if (isInputControls(getKeyCode(e))) {
        return true;
    }
    if (!isFloat(getKeyCode(e))) {
        CancelAction(e);
    }
}

function datetimeFilter(type, event, blur) {
    if (type == 'date') {
        var maxpos = 2;
        var mindigit = [1, 1, 0];
        var maxdigit = [31, 12, 99];
    } else if (type == 'time') {
        var maxpos = 1;
        var mindigit = [0, 0];
        var maxdigit = [23, 59];
    } else {
        CancelAction(event);
        return false;
    }

    var obj = getTarget(event);
    if (obj != prev_datetime_field) {
        pos = 0;
        prev_datetime_field = obj;
    }
    if (blur != null) {
        if (document.selection) {
            document.selection.empty();
        } else if (window.getSelection) {
            window.getSelection().removeAllRanges();
        }
        pos = 0;
        return false;
    }
    var c = getKeyCode(event);
    if (c == 37) {
        pos = pos - 1;
        if (pos < 0) {
            pos = 0;
        }
    } else if (c == 39) {
        pos = pos + 1;
        if (pos > maxpos) {
            pos = maxpos;
        }
    } else if (c >= 48 && c <= 57) {
        var t = obj.value;
        var dig1 = t.substring(pos * 3, pos * 3 + 1);
        var dig2 = t.substring(pos * 3 + 1, pos * 3 + 2);
        if (dig1 != '_') {
            dig1 = '_';
        } else if (dig2 != '_') {
            dig1 = dig2;
        }
        dig2 = String.fromCharCode(c);
        var dig = ((dig1 + dig2).replace('_', '')) - 0;
        if (dig > maxdigit[pos] || (dig < mindigit[pos] && dig1 != '_')) {
            dig1 = '_';
            dig2 = '_';
        }
        obj.value = t.substring(0, pos * 3) + dig1 + dig2 + t.substring(pos * 3 + 2);
        if (dig1 != '_') {
            pos += (pos < maxpos) ? 1 : 0;
        }
    } else if (c === 8 && obj.attributes['bspall'] !== undefined) {    // если у поля есть аттрибут bspall, то разрешить
        // удаление всех данных кнопкой backspace
        var current_value = obj.value,
            new_value = "";

        // Удаление всех данных
        for (var ctr = 0; ctr < current_value.length; ctr++) {
            if (ctr % 3 === 2) {
                new_value += current_value[ctr];
            } else {
                new_value += "_";
            }
        }
        pos = 0;
        obj.value = new_value;
    } else if (c === 8 && obj.attributes['bsppos'] !== undefined) {    // если у поля есть аттрибут bsppos, то разрешить
        // удаление данных по группам кнопкой backspace
        var current_value = obj.value,
            new_value = "";

        // удалять по-группам
        var dig1 = current_value.substring(pos * 3, pos * 3 + 1),
            dig2 = current_value.substring(pos * 3 + 1, pos * 3 + 2);
        if (dig1 === '_' && dig2 === '_') {
            pos = pos - 1;
            if (pos < 0) {
                pos = maxpos;
            }
        }
        new_value = current_value.substring(0, pos * 3) + '__' + current_value.substring(pos * 3 + 2);
        obj.value = new_value;
    }
    obj.focus();
    if (obj.setSelectionRange == null) {
        var rng = obj.createTextRange();
        rng.moveStart("character", pos * 3);
        if (type == 'date') {
            rng.moveEnd("character", -(8 - (pos * 3 + 2)));
        } else if (type == 'time') {
            rng.moveEnd("character", -(5 - (pos * 3 + 2)));
        }
        rng.select();
    } else {
        obj.setSelectionRange(pos * 3, pos * 3 + 2);
    }
    CancelAction(event);
    return false;
}

function datetimeFilter_add(event) {
    return false;
}

///////////////////////////////////////////////////////////////////////////////

function IsValidElement(element, array) {
    if (array && array.length > 0) {
        for (var i = 0; i < array.length; i++) {
            if (array[i] == element) {
                return true;
            }
        }
    }
    return false;
}

function getTarget(event) {
    return event.target || event.srcElement;
}

function getNodeText(Node) {
    var nodeText = ''
    if (Node.nodeValue != null) nodeText += Node.nodeValue;
    for (var i = 0; i < Node.childNodes.length; i++) {
        Node2 = Node.childNodes[i];
        nodeText += getNodeText(Node2);
    }
    return nodeText;
}

function getPRM(Node) {

    var scanprm = null;
    var validprm = null;
    if (Node.attributes['prms'] != null) {
        var idsplit = Node.attributes['prms'].nodeValue.split(':');
        scanprm = idsplit[0];
        validprm = idsplit[1];
    }
    return {scanprm: scanprm, validprm: validprm}
}

function checkDoubleEnter(evt) {
    if (evt.returnValue === false) return;

    if (g_EnterKeyDownFlag) {
        evt.cancelBubbles = true;
        evt.returnValue = false;
        alert("Подождите, выполняется действие...(не более 10 секунд)");
    } else {
        g_EnterKeyDownFlag = true;
        window.setTimeout(function () {
            g_EnterKeyDownFlag = false;
        }, 10000);
    }
}

function GenerateElementsList(ElementContainer, currentForm) {
    var Node = null;
    for (var i = 0; i < ElementContainer.childNodes.length; i++) {
        Node = ElementContainer.childNodes[i];
        if (readyForFocus == 0 && Node.id == 'data') {
            readyForFocus = 1;
        }
        if (Node.id == 'warning') {
            needUp = 1;
        }
        if (Node.tagName == 'TD') {
            v = getNodeText(Node);
            /*if (v!=null && v!=''){
              if (! isNaN(v*1)){
                 //digit, float
                 Node.style.textAlign='right';
              }else if(v=='+' || v=='-' || v=='v' || v=='V'){
                 //status
                 Node.style.textAlign='center';
              }else{
                 //string
                 Node.style.textAlign='left';
              }
           }*/
        }

        if (Node.tagName == "A" && Node.href.match(/#$/) == null) {
            var listener = regEvent(Node, "click", checkDoubleEnter);
        }

        if (IsValidElement(Node.tagName, GValidElelments)) {
            if (Node.tagName == "INPUT" && Node.type == "hidden") {
                continue;
            }
            var prm = getPRM(Node);
            //Scan/OnlyScan/Focus
            if (prm.scanprm == 'onlyscan') {
                Node.style.display = 'none';
                GOnlyScanElement = Node;
                GScanElementForm = currentForm;
            } else {
                GElementsList.push(Node);
                if (readyForFocus == 1) {
                    GIndex = GElementsList.length - 1;
                    readyForFocus = 2;
                }
            }
            if (prm.scanprm) {
                if (prm.scanprm == 'focus') {
                    GIndex = GElementsList.length - 1;
                }
                if (prm.scanprm == 'scan') {
                    GScanElementIdx = GElementsList.length - 1;
                }
                if (prm.scanprm == 'fscan') { //focus and scan
                    GIndex = GElementsList.length - 1;
                    GScanElementIdx = GElementsList.length - 1;
                }
            }
            if (prm.validprm) {
                //int/float/date
                eventName = "keypress";
                //if (idsplit[1]=='onlyscan'){eventName="change";}
                if (prm.validprm == 'int') {
                    var listener = regEvent(Node, eventName, intFilter);
                }
                if (prm.validprm == 'float') {
                    var listener = regEvent(Node, eventName, floatFilter);
                }
                if (prm.validprm == 'date') {
                    var listener = regEvent(Node, 'focus', function (ev) {
                        return datetimeFilter('date', ev);
                    });
                    if (navigator.appName == 'Opera') {
                        Node.onkeydown = datetimeFilter('date');
                        Node.onkeypress = datetimeFilter_add;
                    } else {
                        var listener = regEvent(Node, "keydown", function (ev) {
                            return datetimeFilter('date', ev);
                        });
                    }
                }
                if (prm.validprm == 'time') {
                    var listener = regEvent(Node, 'focus', function (ev) {
                        return datetimeFilter('time', ev);
                    });
                    if (navigator.appName == 'Opera') {
                        Node.onkeydown = datetimeFilter('time');
                        Node.onkeypress = datetimeFilter_add;
                    } else {
                        var listener = regEvent(Node, "keydown", function (ev) {
                            return datetimeFilter('time', ev);
                        });
                    }
                }
            }
            /*if (Node.tagName=='INPUT'){
                 var listener = regEvent( Node,
                                           "focus",
            function(event){getTarget(event).select();}
            )
            }*/
        } else if (Node.childNodes.length > 0) {
            if (Node.tagName == "FORM") {
                var listener = regEvent(Node, "submit", checkDoubleEnter);
                currentForm = Node;
            }
            GenerateElementsList(Node, currentForm);
        }
    }
}

function MoveMarker(evt, step) {
    var newGIndex = GIndex + step;
    if (newGIndex < 0) {
        newGIndex = 0;
    }
    if (newGIndex > GElementsList.length - 1) {
        newGIndex = GElementsList.length - 1
    }
    if (newGIndex != GIndex) {
        GIndexPrev = GIndex;
        GIndex = newGIndex;
        DrawMarker();
    }
    CancelAction(evt);
}

function DrawMarker(no_offset) {
    no_offset = typeof no_offset !== 'undefined' ? no_offset : false;
    if (GIndexPrev != GIndex) {
        elem = GElementsList[GIndexPrev];
        elem.className = PrevStyle;
    }
    elem = GElementsList[GIndex];
    var el_y = getAbsolutePos(elem).y;
    if (!no_offset) {
        window.scrollTo(0, el_y - 50);
    }
    GIndexPrev = GIndex;
    PrevStyle = elem.className;
    elem.className = 'Marker';
    elem.focus();

    var scrll = document.body.scrollTop;
    if (is_ie) var scrll = 0;

    if ((elem.type == 'text' || elem.type == 'password') && !elem.readOnly && !elem.disabled) {
        if (getPRM(elem).validprm != 'date' && getPRM(elem).validprm != 'time') elem.select();
    } else {
        if (document.selection) document.selection.empty();
    }
    pos = 0;
}

var esc_pressed_flag = false;

function KeyDownAction(evt) {
    if (getKeyCode(evt) == 27) {
        //this flag not checked in "confirm" and "alert" modal box
        esc_pressed_flag = true;
    }
    if (GScaning != false) {
        if (getKeyCode(evt) == 13) {
            if (GScaning == 'hscan') {
                if (GScanElementForm.no_submit != "yes" || evt.target.id == 'btn_submit') {
                    GScanElementForm.submit();
                }
                CancelAction(evt);
            }
            if (GScaning == 'no') {
                CancelAction(evt);
            }
            GScaning = false;
        }
    } else {
        var node = GElementsList[GIndex];
        var isTextField = node.tagName == 'INPUT' && (node.type == 'text' || node.type == 'password');

        //backspace block
        if (getKeyCode(evt) == 8 && !isTextField) {
            CancelAction(evt);
        }
        if (getKeyCode(evt) == 40) {
            //KEY DOWN
            //document.getElementById('code').value = 'Down';
            MoveMarker(evt, +1)
            /*if (GIndex<GElementsList.length-1) {
              GIndexPrev = GIndex;
              GIndex = GIndex+1;
              DrawMarker();
              CancelAction(evt);
              }*/
        }
        if (getKeyCode(evt) == 38) {
            //KEY UP
            MoveMarker(evt, -1)
            //document.getElementById('code').value = 'UP';
            /*if (GIndex>=1) {
              GIndexPrev = GIndex;
              GIndex = GIndex-1;
              DrawMarker();
              CancelAction(evt);
              }*/
        }
        if (!isTextField) {
            if (getKeyCode(evt) == 37) {
                //KEY LEFT
                MoveMarker(evt, -ScrollStep)
                /*if (GIndex != 0){
                  GIndexPrev = GIndex;
                  if (GIndex > ScrollStep){
                  GIndex = GIndex - ScrollStep;
                  }else {
                  GIndex = 0;
                  }
                  DrawMarker();
                  CancelAction(evt);
                  }*/
            }
            if (getKeyCode(evt) == 39) {
                //KEY RIGHT
                MoveMarker(evt, +ScrollStep)
                /*if (GIndex<GElementsList.length-1){
                  GIndexPrev = GIndex;
                  if (GElementsList.length-1-GIndex > ScrollStep){
                  GIndex = GIndex + ScrollStep;
                  }else {
                  GIndex = GElementsList.length-1;
                  }
                  DrawMarker();
                  CancelAction(evt);
                  }*/
            }
        }
        if (getKeyCode(evt) == ScannerPrefixCode) {
            //KEY Scanner
            if (GOnlyScanElement != null) {
                //Hidden scan
                //alert('Before:'+document.getElementById(GOnlyScanElementId).value);
                GScaning = 'hscan';
                CancelAction(evt);
                return false;
            } else if (GScanElementIdx != null) {
                //Usual scan
                GScaning = 'scan';
                id = GElementsList[GIndex].id
                if (id == null) id = '';
                if (id.split(':')[1] != 'scan') {
                    GIndexPrev = GIndex;
                    GIndex = GScanElementIdx;
                }
                GElementsList[GIndex].value = '';
                DrawMarker();
            } else {
                GScaning = 'no';
            }
        }
    }
}

function KeyPressAction(evt) {
    if (getKeyCode(evt) != 37 && getKeyCode(evt) != 39 && getKeyCode(evt) != 38 && getKeyCode(evt) != 40) {
        if (GScaning == 'no') {
            CancelAction(evt);
        }
        if (getKeyCode(evt) === 12) {
            // gs1_stacked = true;
            CancelAction(evt);
            return;
        }
        if (GScaning == 'hscan' || GScaning == 'scan') {
            var scanEl = GOnlyScanElement != null ? GOnlyScanElement : GElementsList[GScanElementIdx];
            if (getKeyCode(evt) != ScannerPrefixCode) {
                var keyCode = getKeyCode(evt);
                // scanEl.value = scanEl.value + String.fromCharCode((96 <= keyCode && keyCode <= 105) ? keyCode-48 : keyCode);
                if (evt.shiftKey == true) {
                    scanEl.value = scanEl.value + String.fromCharCode(keyCode).toUpperCase();
                } else {
                    scanEl.value = scanEl.value + String.fromCharCode(keyCode);
                }
            }
            CancelAction(evt);
        }
    } else if (!GScaning){
      // do this strange magic only when not scanning
      CancelAction(evt);
    }
}

function KeyUpAction(evt) {
    if (getKeyCode(evt) == 27) {
        if (esc_pressed_flag == true) {
            esc_pressed_flag = false;
            var back_b = document.getElementById('backlink')
            if (back_b != null) {
                var t = back_b.href
                if (t != null && t != '#') {
                    document.location.href = t;
                    CancelAction(evt);
                }
            }
        }
    }
}

function parsePage() {
    function fix_gs1_scan(input_obj){
      function _gs1_fix(event){
        var input_obj_value=input_obj.value;
        if(input_obj_value != input_obj_value_prev){
          input_obj_value = input_obj_value.replace(/CONTROL001D/g, String.fromCharCode(29));
          input_obj.value = input_obj_value;
        };
        input_obj_value_prev = input_obj_value;
        return true;
      }
      
      function form_submit_hook(form){
        var submit_orig=form.submit;
        form.submit=function(){
          _gs1_fix(null);
          return submit_orig.apply(form);
        };
      }
      if (is_ie) return; //IE need no fixes
      var frm = input_obj, input_obj_value_prev=null;
      while(frm && frm.tagName != 'FORM'){
        //search for inclusing FORM
        frm = frm.parentNode;
      }
      if(!frm) return; //input field is not in form
      //event fired when form submitted by UI
      regEvent(frm, 'submit', _gs1_fix);
      //hook fired when form submitted by JS
      form_submit_hook(frm);
    };
    function scanEl_get(){
      return GOnlyScanElement!=null ? GOnlyScanElement : GElementsList[GScanElementIdx];
    };
    GenerateElementsList(document.body, null);
    //null-parent form
    if (GIndex == 0 && GScanElementIdx) {
        GIndex = GScanElementIdx;
    }
    GIndexPrev = GIndex;
    DrawMarker();
    fix_gs1_scan(scanEl_get());
    var listener = regEvent(document, "keydown", function (ev) {
        if (getKeyCode(ev) === 13) {
            var scanEl = scanEl_get();
            if (scanEl.attributes['skipgs1check'] == null) {
                if (scanEl.value.length > 20 && scanEl.value.slice(0, 2) === '01') {
                    scanEl.value = scanEl.value.slice(2, 16);
                }
            }
        }
        if (getKeyCode(ev) === 0) {
            if (prev_scancode === 13 && prev_gindex == GIndex) {
                GElementsList[GIndex].value = '';
                //CancelAction(ev);
            }
        }

        if (getKeyCode(ev) === 13 && (scan == 1 || scan == 2)) {

            scan = 0;
            //GElementsList[GIndex].value=''
        }
        //document.getElementById('debug').value = getKeyCode(ev).toString()+' '+scan.toString()+'\n';

        if (getKeyCode(ev) != 37 && getKeyCode(ev) != 39 && getKeyCode(ev) != 38 && getKeyCode(ev) != 40) {
            if (scan < 2) {

                //Если несколько нулей подряд, то считаем за один
                if (getKeyCode(ev) === 0 && prev_scancode !=0) {
                    scan += 1;
                }
                prev_scancode = getKeyCode(ev);
                prev_gindex = GIndex;
                KeyDownAction(ev);
            } else {
                //ноль среди сканирования - прерываемся
                GScaning = false;
                CancelAction(ev);
            }
        } else {
            GScaning = false;
            //document.getElementById('code').value = getKeyCode(ev).toString() + ' ' + GScaning.toString();
            KeyDownAction(ev);
        }
        //KeyDownAction(ev);
    });
    //Navigation Keys
    var listener = regEvent(document, "keypress", function (ev) {
        KeyPressAction(ev);
    });
    var listener = regEvent(document, "keyup", function (ev) {
        KeyUpAction(ev);
    });
    //focus follow to mouse
    var listener = regEvent(document, "click", function (ev) {
        var t = getTarget(ev)
        for (var i = 0; i < GElementsList.length; i++) {
            if (GElementsList[i] == t) {
                if (GIndex != i) {
                    GIndex = i;
                    DrawMarker();
                }
                break;
            }
        }
    });
    if (needUp == 1) {
        window.scroll(0, 0);
    }
    //All other keys
}

getAbsolutePos = function (el) {

    var SL = 0, ST = 0;
    var is_div = /^div$/i.test(el.tagName);
    if (is_div && el.scrollLeft)
        SL = el.scrollLeft;
    if (is_div && el.scrollTop)
        ST = el.scrollTop;
    var r = {x: el.offsetLeft - SL, y: el.offsetTop - ST};
    if (el.offsetParent) {
        var tmp = getAbsolutePos(el.offsetParent);
        r.x += tmp.x;
        r.y += tmp.y;
    }
    return r;

};

/*
 * Получение списка элементов по названию класса в IE
 */
function getElementsByClassName(cl) {
    var retnode = [];
    var elem = this.getElementsByTagName('*');
    for (var i = 0; i < elem.length; i++) {
        if ((' ' + elem[i].className + ' ').indexOf(' ' + cl + ' ') > -1) {
            retnode.push(elem[i]);
        }
    }
    return retnode;
};

/* Sankov N.S., 27.09.2011 */

/*
 * This handler recieves set of characters that is allowed to type into input field
 * You should call this method on keydown event. Example:
 *      <input type="text" onkeydown="return allowChars(event, '0-9');" />
 * This will disallow all chars except numbers
 */
function allowChars(event, charList) {
    if (!event)
        return true;

    regex = new RegExp('[^' + charList + ']');
    printable = /[\d\w\s]/;

    // Cross implementation
    key = (window.event) ? event.keyCode : event.which;
    keyChar = String.fromCharCode(key);

    /* Keep key pressing if it is not printable */
    if (!printable.test(keyChar) || (key >= 112 && key <= 123) || event.ctrlKey || key == 9) {
        return true;
    }

    return !regex.test(keyChar);
}

/*
 * Wrapper for allowChars, disallows all except numbers
 */
function allowNaturals(event) {
    return allowChars(event, '0-9');
}

/*
 * Wrapper for allowChars, disallows all, except numbers in given range [from, to]
 */
function range(event, from, to) {
    result = allowChars('0-9');
    if (result)
        return (event.currentTarget.value >= from && event.currentTarget.value <= to);
    else
        return result;
}

function isInViewport(element) {
    var rect = element.getBoundingClientRect(),
        html = document.documentElement;
    return (
        rect.top >= -(element.offsetHeight - 1) &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || html.clientHeight) &&
        rect.right <= (window.innerWidth || htmlclientWidth)
    );
}

function isInViewportTopBottom(element) {
    var rect = element.getBoundingClientRect(),
        html = document.documentElement;
    return (
        rect.top >= -1 &&
        rect.bottom <= (window.innerHeight || html.clientHeight)
    );
}

window.onscroll = function (evt) {
    if (!isInViewportTopBottom(GElementsList[GIndex])) {
        for (var ctr = 0; ctr < GElementsList.length; ctr++) {
            var el = GElementsList[ctr];
            if (isInViewportTopBottom(GElementsList[ctr])) {
                GIndex = ctr;
                DrawMarker(true);
                break;
            }
        }
    }
}

//запускаем parsePage только после 2х вызовов onBodyLoad
onBodyLoad()

function log(s){
  function xhttp_get(){
    var req;
    if (window.XMLHttpRequest)
      req = new XMLHttpRequest();
    else if (window.ActiveXObject) {
      try {
        req = new ActiveXObject('Msxml2.XMLHTTP');
      } catch (e) {
        try {
          req = new ActiveXObject('Microsoft.XMLHTTP');
        } catch (e) {}
      }
    }
    return req;
  }
  //логирование в консоль, если доступна, иначе в элемент с id=='log'
  if(typeof(console)=='object' && console.log){
    console.log(s)
  }else{
    var le = document.getElementById('log');
    if(!le) return;
    le.innerHTML+= s+'<br>';
  }
  xhttp = xhttp_get();
  xhttp.open('POST','/PRICECHECK/log?m='+encodeURIComponent(s));
  xhttp.send();
}
/* TSD Browser crutch begin */
//убираем исключение, если AndroidFunction не определена - просто пустышка
if(typeof(AndroidFunction)=='undefined'){
  AndroidFunction = {
    resize:function(){}
    };
  };
//убираем исключение, если isMarkerVisible не определена - просто пустышка
if(typeof(isMarkerVisible)=='undefined') isMarkerVisible = function(){return true;};
/* TSD Browser crutch end */