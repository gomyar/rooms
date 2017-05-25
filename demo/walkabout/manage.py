#!/usr/bin/env python

import os
from flask_script import Manager, Server
from flask import current_app
from flask_collect import Collect
from server import create_app
from werkzeug.security import generate_password_hash
from rooms.flask.login import create_user


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


@manager.command
def add_user():
    username = raw_input("Enter username:")
    password = raw_input("Enter password:")
    admin = raw_input("is admin? (y/n)") in ('y', 'Y')
    passhash = generate_password_hash(password)
    create_user(username, passhash, admin)


if __name__ == "__main__":
    manager.run()
