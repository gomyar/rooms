
import time


_mock_time = None


def get_now():
    if _mock_time == None:
        return time.time()
    else:
        return _mock_time


def _set_mock_time(mock_time):
    global _mock_time
    _mock_time = mock_time


def _fast_forward(seconds):
    global _mock_time
    _mock_time += seconds
