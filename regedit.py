# -*- encoding: utf-8 -*-
__author__ = 'pahaz'

import _winreg as reg
import itertools
import pickle

RegRoots = {
    reg.HKEY_CLASSES_ROOT: 'HKEY_CLASSES_ROOT',
    reg.HKEY_CURRENT_USER: 'HKEY_CURRENT_USER',
    reg.HKEY_LOCAL_MACHINE: 'HKEY_LOCAL_MACHINE',
    reg.HKEY_USERS: 'HKEY_USERS',
}


class RegKey(object):
    """ A handy wrapper around the raw stuff in the _winreg module.

        >>> import _winreg
        >>> rawkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, '')
        >>> rk = RegKey(rawkey, _winreg.HKEY_CURRENT_USER, '')
        >>> rk.root is _winreg.HKEY_CURRENT_USER
        True
        >>> rk.path
        ''
        >>> rk.key is rawkey
        True
    """

    def __init__(self, rawkey, root, path):
        """
        @param rawkey: OpenKey handler (ex: OpenKey(_winreg.HKEY_CURRENT_USER,
            'Software\\urfuclub_soft'))
        @param root: handler root (ex: _winreg.HKEY_CURRENT_USER)
        @param path: handler path (ex: 'Software\\urfuclub_soft')
        """
        self.key = rawkey
        self.root = root
        self.path = path

    def __str__(self):
        return "%s\\%s" % (RegRoots.get(self.root, hex(self.root)), self.path)

    def close(self):
        reg.CloseKey(self.key)

    def values(self):
        """ Iterate the values in this key.
        """
        for ikey in itertools.count():
            try:
                yield reg.EnumValue(self.key, ikey)
            except EnvironmentError:
                break

    def subkey_names(self):
        """ Iterate the names of the subkeys in this key.
        """
        for ikey in itertools.count():
            try:
                yield reg.EnumKey(self.key, ikey)
            except EnvironmentError:
                break

    def subkeys(self):
        """ Iterate the subkeys in this key.
        """
        for subkey_name in self.subkey_names():
            if self.path:
                sub = self.path + '\\' + subkey_name
            else:
                sub = subkey_name

            try:
                rawkey = reg.OpenKey(self.root, sub)
                yield RegKey(rawkey, self.root, sub)
            except Exception, e:
                print "Couldn't open %r %r: %s" % (self.root, sub, e)

            yield None

    def set(self, name, value, typ=reg.REG_SZ):
        """ Set value by name
        """
        if typ == reg.REG_SZ:
            value = str(value)

        rawkey = reg.OpenKey(self.root, self.path, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(rawkey, name, 0, typ, value)
        reg.CloseKey(rawkey)

    def get(self, name):
        """ Get value by name
        """
        return reg.QueryValue(self.key, name)

    def pset(self, name, value):
        " set using pickle "
        self.set(name, pickle.dumps(value))

    def pget(self, name):
        " get using pickle "
        return pickle.loads(self.get(name))


def OpenRegKey(root, path):
    try:
        rawkey = reg.OpenKey(root, path)
    except Exception, e:
        print "Couldn't open %r %r: %s" % (root, path, e)
        return None

    return RegKey(rawkey, root, path)


def grep_key(key, target, repl=None):
    for name, value, typ in key.values():
        if isinstance(value, basestring) and target in value:
            print "Finded! %s\\%s \n = %r" % (key, name, value)
            if repl:
                replaced = value.replace(target, repl)
                key.set(name, value, typ)
                print " > %r !Replaced" % (replaced,)

    for subkey in key.subkeys():
        if not subkey:
            continue
        grep_key(subkey, target, repl)
        subkey.close()


def grep_registry(finde, repl=None):
    for root in RegRoots.keys():
        rawkey = reg.OpenKey(root, "")
        grep_key(RegKey(rawkey, root, ""), finde, repl)


if __name__ == '__main__':
    company, project = "urfuclub", "windows_register_searcher"
    keyname = "Software\\%s\\%s" % (company, project)

    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, keyname)
        print 'sercher re inited! :)'
    except:
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, keyname)
        print 'sercher inited! xD'

    key.Close()

    # or
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, keyname)
    r = RegKey(key, reg.HKEY_CURRENT_USER, keyname)
    r.set("test", "hello string data")
    r.pset("testp", 123)
    r.close()
    assert "hello string data" == r.get("test"), "Fail 1"
    assert 123 == r.pget("testp"), "Fail 2"

    grep_registry("Python_clean", "Python27")
