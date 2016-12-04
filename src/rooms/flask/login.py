
from urlparse import urlparse, urljoin

from pymongo import MongoClient

import flask
from flask import request
from flask import flash
from flask import url_for
from flask import Blueprint

from flask_login import UserMixin
from flask_login import login_user
from flask_login import logout_user
from flask_login import LoginManager
from flask_login import login_required
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

mongo = MongoClient()
login_manager = LoginManager()

bp_login = Blueprint('login', __name__, template_folder='templates',
                     static_folder='static')


def users():
    return mongo.spike_flask.users


class User(UserMixin):
    def __init__(self, username, pw_hash):
        self.username = username
        self.pw_hash = pw_hash

    def get_id(self):
        return self.username


def create_user(username, pw_hash):
    if not users().find_one({'username': username}):
        users().insert_one({
            'username': username,
            'pw_hash': pw_hash })
        return User(username, pw_hash)
    else:
        raise Exception("User already exists")


@login_manager.user_loader
def load_user(username):
    res = users().find_one({'username': username})
    if res:
        return User(res['username'], res['pw_hash'])
    else:
        raise Exception("No such user")


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
