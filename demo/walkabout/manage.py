#!/usr/bin/env python

import os
from werkzeug.security import generate_password_hash
from rooms.flask.login import create_user


def add_user():
    username = input("Enter username:")
    password = input("Enter password:")
    admin = input("is admin? (y/n)") in ('y', 'Y')
    passhash = generate_password_hash(password)
    create_user(username, passhash, admin)


if __name__ == "__main__":
    add_user()
