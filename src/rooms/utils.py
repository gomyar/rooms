
import urlparse

import logging
log = logging.getLogger("rooms.wsgi")


def checked(func):
    def tryexcept(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            log.exception("Exception calling %s", func)
            raise
    return tryexcept

def _read_cookies(environ):
    cookie_str = environ['HTTP_COOKIE']
    cookies = cookie_str.split(';')
    cookies = map(lambda c: c.strip().split('='), cookies)
    return dict(cookies)


def _get_param(environ, param):
    if 'QUERY_STRING' in environ:
        params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
        if param in params:
            return params[param]
    return None



