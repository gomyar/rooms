
import time
import gevent


class Timer(object):
    _instance = None

    @staticmethod
    def _get_instance():
        if not Timer._instance:
            Timer._instance = Timer()
        return Timer._instance

    @staticmethod
    def now():
        return Timer._get_instance()._now()

    @staticmethod
    def sleep(seconds):
        Timer._get_instance()._sleep(seconds)

    def _sleep(self):
        gevent.sleep(seconds)

    def _now(self):
        return time.time()
