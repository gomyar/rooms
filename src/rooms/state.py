

class SyncDict(object):
    def __init__(self, data=None, public=True):
        self._data = data or {}
        self._actor = None
        self._public = public

    def __eq__(self, rhs):
        return self._data == rhs

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self._data)

    def _set_actor(self, actor):
        self._actor = actor
        for key in self._data:
            if isinstance(self._data[key], (SyncDict, SyncList)):
                self._data[key]._set_actor(actor)

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        if name in ['_public', '_data', '_actor']:
            super(SyncDict, self).__setattr__(name, value)
        else:
            self.__setitem__(name, value)

    def __getitem__(self, name):
        return self._data.get(name, None)

    def __setitem__(self, name, value):
        if isinstance(value, (SyncDict, SyncList)):
            value._set_actor(self._actor)
        self._data[name] = value
        if self._actor:
            self._actor._send_state_changed()

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def __iter__(self):
        for name in self.keys():
            yield name


class SyncList(object):
    def __init__(self, data=None, public=True):
        self._data = data or []
        self._public = public
        self._actor = None

    def __repr__(self):
        return "<SyncList %s>" % (self._data,)

    def append(self, item):
        self._data.append(item)
        self._actor._send_state_changed()

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, value):
        self._data[index] = value
        self._actor._send_state_changed()

    def _set_actor(self, actor):
        self._actor = actor
        for item in self._data:
            if isinstance(item, (SyncDict, SyncList)):
                item._set_actor(actor)
