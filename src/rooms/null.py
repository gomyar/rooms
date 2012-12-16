class Null(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, mname):
        return self

    def __setattr__(self, name, value):
        return self

    def __delattr__(self, name):
        return self

    def __repr__(self):
        return "<Null>"

    def __len__(self):
        return 0

    def __iter__(self):
        for i in []:
            yield i

    def __nonzero__(self):
        return False
