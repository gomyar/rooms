

def _wrap(name, obj, parent):
    if type(obj) == dict:
        return SyncDict(name, obj, parent)
    if type(obj) == list:
        return SyncList(name, obj, parent)
    return obj



class SyncDict(object):
    def __init__(self, key, data, parent):
        self._key = key
        self._data = {}
        if data:
            for k, v in data.items():
                self._data[k] = _wrap(k, v, self)
        self._parent = parent

    def __eq__(self, rhs):
        return (type(rhs) is list and self._data == rhs) or (
            type(rhs) is SyncDict and self._data == rhs._data)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self._data)

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        if name in ['_data', '_key', '_parent', '_update_function']:
            super(SyncDict, self).__setattr__(name, value)
        else:
            self.__setitem__(name, value)

    def __getitem__(self, name):
        return self._data.get(name, None)

    def __setitem__(self, name, value):
        self._data[name] = _wrap(name, value, self)
        self._send_update("set", name, value)

    def _send_update(self, action, name, value=None):
        self._parent._send_update(action, self._key + '.' + name, value)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def pop(self, name):
        self._data.pop(name)
        self._send_update("pop", name)

    def __iter__(self):
        for name in self.keys():
            yield name

    def update(self, values):
        self._data.update(values)

    def __eq__(self, rhs):
        if type(rhs) is SyncDict:
            return self._data == rhs._data
        if type(rhs) is dict:
            return self._data == rhs
        else:
            return self == rhs


class SyncList(object):
    def __init__(self, key, data, parent):
        self._key = key
        self._data = [self._wrap(index, value) for (index, value) in enumerate(data)]
        self._parent = parent

    def __eq__(self, rhs):
        return (type(rhs) is list and self._data == rhs) or (
            type(rhs) is SyncList and self._data == rhs._data)

    def _wrap(self, name, obj):
        if type(obj) == dict:
            return SyncDict(name, obj, self)
        if type(obj) == list:
            return SyncList(name, obj, self)
        return obj

    def __repr__(self):
        return "<SyncList %s>" % (self._data,)

    def append(self, item):
        name = str(len(self._data))
        self._data.append(self._wrap(name, item))
        self._send_update("set", name, item)

    def pop(self, index=None):
        self._data.pop(index)
        self._send_update("pop", str(index))

    def _send_update(self, action, name, value=None):
        self._parent._send_update(action, self._key + '.' + name, value)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, value):
        self._data[index] = self._wrap(str(index), value)
        self._send_update("set", str(index), value)


class SyncState(SyncDict):
    def __init__(self, data, update_function):
        super(SyncState, self).__init__('state', data, None)
        self._update_function = update_function

    def _send_update(self, action, name, value):
        self._update_function(action, name, value)
