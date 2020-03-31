
try:
    from urllib.parse import urlparse, urljoin
except:
    from urlparse import urlparse, urljoin

import os

from pymongo import MongoClient

import flask
from flask import request
from flask import flash
from flask import url_for
from flask import Blueprint

from flask_login import login_user
from flask_login import logout_user
from flask_login import LoginManager
from flask_login import login_required
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from rooms.flask.app import container

mongo = MongoClient()
login_manager = LoginManager()

bp_login = Blueprint('login', __name__,
                     template_folder=os.path.join(
                        os.path.dirname(__file__), 'templates'),
                     static_folder=os.path.join(
                        os.path.dirname(__file__), 'static/accounts'),
                     static_url_path='/static/accounts')


class User(UserMixin):
    def __init__(self, username, pw_hash, admin=False):
        self.username = username
        self.pw_hash = pw_hash
        self.admin = admin

    def get_id(self):
        return self.username

    def is_admin(self):
        return self.admin


def create_user(username, pw_hash, admin=False):
    if not container.dbase.filter_one('users', {'username': username}):
        container.dbase.save_object({
            'username': username,
            'pw_hash': pw_hash,
            'admin': admin}, 'users')
        return User(username, pw_hash)
    else:
        raise Exception("User already exists")


@login_manager.user_loader
def load_user(username):
    res = container.dbase.filter_one('users', {'username': username})
    if res:
        return User(res['username'], res['pw_hash'], res.get('admin'))
    else:
        return None


def is_safe_url(target):
    # check if target is on same server as self
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


@bp_login.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = load_user(request.form['username'])
        if user and check_password_hash(user.pw_hash, \
                                        request.form['password']):
            login_user(user)

            flash('Logged in successfully.')

            next_url = request.form.get('next')
            if next_url and not is_safe_url(next_url):
                return flask.abort(400)

            return flask.redirect(next_url or flask.url_for('index'))
    return flask.render_template('login.html',
                                 next_url=request.args.get('next'))


@bp_login.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for('index'))


@bp_login.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = create_user(request.form['username'], generate_password_hash(
            request.form['password']))
        return flask.redirect(flask.url_for('index'))
    else:
        return flask.render_template('register.html')


def init_login(app):
    login_manager.init_app(app)
    login_manager.login_view = 'login.login'
