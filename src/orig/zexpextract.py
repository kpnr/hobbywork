#!python2
import sys
import logging
import os
import json
from cStringIO import StringIO
from pickle import Pickler, Unpickler
from struct import pack, unpack

FORMAT = '%(levelname)s :%(lineno)d %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


class Dummy2:
    def __init__(self, *a, **b):
        # print a,b
        self.argmt = [a, b]

    def __repr__(self):
        return '<%s dict=%s>' % (self.__class__.__name__, self.__dict__)


class CustomUnpickler(Unpickler):
    def find_class(self, module, name):
        clname = ('%s.%s' % (module, name)).replace('.', '_').replace('-', '_')
        # print '>>find_class ', module,name, ' -> ', clname
        exec ('class %s(Dummy2):pass' % clname)
        return eval(clname)


_oid = '\0' * 8


def FileToNodes(fpath):
    # Copyright (c) Zope
    # https://github.com/zopefoundation/ZODB/blob/master/src/ZODB/ExportImport.py

    f = file(fpath, 'rb')
    magic = f.read(4)
    if magic != 'ZEXP':
        raise Exception("Invalid export header")

    oids = {}
    export_end_marker = '\377' * 16
    blob_begin_marker = b'\000BLOBSTART'

    def new_oid():
        global _oid
        last = _oid
        d = ord(last[-1])
        if d < 255:  # fast path for the usual case
            last = last[:-1] + chr(d + 1)
        else:  # there's a carry out of the last byte
            last_as_long, = unpack(">Q", last)
            last = pack(">Q", last_as_long + 1)
        _oid = last
        return last

    def u64(v):
        """Unpack an 8-byte string into a 64-bit long integer."""
        return unpack(">Q", v)[0]

    class Ghost(object):
        __slots__ = ("oid",)

        def __init__(self, oid):
            self.oid = oid

        def __repr__(self):
            return '<%s dict=%s>' % (self.__class__.__name__, self.oid)

    def persistent_id(obj):
        if isinstance(obj, Ghost):
            return obj.oid

    def persistent_load(ooid):
        """Remap a persistent id to a new ID and create a ghost for it."""
        klass = None
        if isinstance(ooid, tuple):
            ooid, klass = ooid
        if ooid in oids:
            oid = oids[ooid]
        else:
            if klass is None:
                oid = new_oid()
            else:
                oid = new_oid(), klass
            oids[ooid] = oid
        return Ghost(oid)

    out = []
    while 1:
        header = f.read(16)
        if header == export_end_marker:
            break
        if len(header) != 16:
            raise Exception("Truncated export file")

        # Extract header information
        ooid = header[:8]
        length = u64(header[8:16])
        data = f.read(length)
        if len(data) != length:
            raise Exception("Truncated export file")

        if oids:
            oid = oids[ooid]
            if isinstance(oid, tuple):
                oid = oid[0]
        else:
            oids[ooid] = oid = new_oid()

        if 'blob' in data:
            if f.read(len(blob_begin_marker)) != blob_begin_marker:
                raise ValueError("No data for blob object")
            raise NotImplementedError("No blob support now")

            # blob_len = u64(f.read(8))
            # blob_filename = mktemp(self._storage.temporaryDirectory())
            # blob_file = open(blob_filename, "wb")
            # cp(f, blob_file, blob_len)
            # blob_file.close()
        else:
            blob_filename = None

        pfile = StringIO(data)
        unpickler = CustomUnpickler(pfile)
        unpickler.persistent_load = persistent_load
        a = unpickler.load()
        b = unpickler.load()
        #
        out.append([oid, a, b])

    return out


def make_filelist(node, path, flist, index):
    objs = node.get('_objects', [])
    xobjs = {}
    for i in objs:
        xobjs[i['id']] = i['meta_type']
    keys = xobjs.keys()
    keys.sort()
    for i in keys:
        oid = node[i].oid
        if xobjs[i] in ('Folder', 'Folder (Ordered)'):
            flist = make_filelist(index[oid], path + [i], flist, index)
        flist.append({'node': index[oid], 'path': path + [i], 'meta_type': xobjs[i]})
    return flist

def class_name_get(o):
    if hasattr(o,'__class__'):
        o = o.__class__
    return o.__name__

def attr_count_get(o):
    rv = getattr(o,'__dict__', {})
    return len(rv)

def jdefault(o):
    """
    if isinstance(o, Dummy2):
        return list(o)
    import pdb; pdb.set_trace()
    return o.__dict__
    """
    class_name = class_name_get(o)
    attr_count = attr_count_get(o)
    rv = None
    if class_name == 'copy_reg___newobj__' and attr_count == 5:
        rv = dict(argmt=o.argmt, globals=o.globals, raw=o.raw, _vars=o._vars, __name__=o.__name__)
    elif class_name == 'Shared_DC_Scripts_Bindings_NameAssignments' and attr_count == 1:
        rv = dict(_asgns=o._asgns)
    elif class_name == 'Shared_DC_Scripts_Signature_FuncCode' and attr_count == 2:
        rv = dict(co_argcount=o.co_argcount, co_varnames=o.co_varnames)
    elif class_name == 'Shared_DC_ZRDB_Aqueduct_Args' and attr_count == 2:
        rv = dict(_data=o._data, _keys=o._keys)
    elif class_name == 'Shared_DC_ZRDB_DA_SQL' and attr_count == 2:
        rv = dict(__doc__=o.__doc__, __module__=o.__module__)
    elif class_name == 'Ghost' and attr_count == 0:
        rv = dict(oid=o.oid)
    if rv is None:
        rv = repr(o)
    else:
        rv = json.dumps(rv, ensure_ascii=False, indent=4, default=jdefault)
    return rv


def parseZobj(objs):
    index = {}
    for i in objs:
        index[i[0]] = i[2]
    root = objs[0][2]
    flist = make_filelist(root, [root['id']], [], index)
    if not flist:
        flist.append({'node': root, 'path': [root['id']], 'meta_type': 'unknown'})

    for item in flist:
        full_path = '/'.join(item['path'])
        directory = os.path.dirname(full_path) or '.'
        if not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists(directory + '/__meta/'):
            os.makedirs(directory + '/__meta/')

        meta_type = item['meta_type']
        logging.getLogger(__name__).info('Extracting %s - %s', full_path, meta_type)
        with open(directory + '/__meta/' + item['path'][-1], 'wb') as fh:
            json.dump(item, fh, ensure_ascii=False, indent=4, default=jdefault)

        if meta_type[0:6] != 'Folder':
                if meta_type == 'File':
                    out = item['node']['data'].oid if hasattr(item['node']['data'], 'oid') else item['node']['data']
                    file_ext = ''
                elif meta_type == 'Script (Python)':
                    out = item['node']['_body']
                    file_ext = '.py'
                elif meta_type == 'Page Template':
                    out = item['node']['_text']
                    file_ext = '.html'
                elif meta_type == 'Z SQL Method':
                    out = item['node']['src']
                    file_ext = '.sql'
                elif meta_type == 'SyncDict':
                    out = item['node'] or '{}'
                    file_ext = '.dict'
                elif meta_type == 'DTML Document':
                    out = item['node']['raw']
                    file_ext = '.dtml'
                elif meta_type == 'External Method':
                    out = item['node']
                    out = 'Title: %s\nModule: %s\nFunction: %s\n' % (out['title'], out['_module'], out['_function'])
                    file_ext = '.external'
                else:
                    node = item['node']
                    out = node.get('data', '') or node.get('_body', '') or node.get('_text', '')\
                           or node.get('src', '') or 'WTF?'
                    file_ext = ''
                with open(full_path + file_ext, 'wb') as fh :
                    fh.write(out)
    return


def get_plain_content(fpath):
    """ return content of zexp-file """
    objs = FileToNodes(fpath)
    # return objs
    return parseZobj(objs)


if __name__ == '__main__':
    import pprint
    get_plain_content(sys.argv[1])
