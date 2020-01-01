
import uuid


class IDFactory(object):
    _instance = None

    @staticmethod
    def create_id():
        return IDFactory._instance._create_id()

    def _create_id(self):
        return str(uuid.uuid1())

IDFactory._instance = IDFactory()

