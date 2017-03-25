#!/usr/bin/env python

import os
from flask_script import Manager, Server
from flask import current_app
from flask_collect import Collect
from server import create_app

app = create_app()

app.config['COLLECT_STATIC_ROOT'] = (
    os.path.join(os.path.dirname(__file__), 'collectstatic'))
app.config['COLLECT_STORAGE'] = 'flask_collect.storage.file'


manager = Manager(app)

collect = Collect()
collect.init_app(app)


@manager.command
def collect():
    return current_app.extensions['collect'].collect()


if __name__ == "__main__":
    manager.run()
