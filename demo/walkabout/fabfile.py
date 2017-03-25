
from fabric.operations import run, put, env, sudo, local
from fabric.context_managers import prefix, cd
from fabric.contrib.files import exists

import time


def deploy(update_deps=False):
    env.project_name = 'walkabout'
    env.forward_agent = True

    # Install directory
    env.tstamp = time.strftime("%Y%m%d%H%M%S")
    env.inst_dir = "/opt/%(project_name)s/%(tstamp)s" % env
    env.build_file = "build.%(tstamp)s.tar.gz" % env
    env.build_path = "/tmp/%(build_file)s" % env

    # Push project
    run("mkdir %(inst_dir)s" % env)
    local("rm -f %(build_path)s" % env)
    local("tar -zcvf %(build_path)s --exclude=*.pyc --exclude=*.gz ./" % env)
    put(env.build_path, env.inst_dir)
    run("tar -zxvf %(inst_dir)s/%(build_file)s -C %(inst_dir)s" % env)
    run("rm %(inst_dir)s/%(build_file)s" % env)
    local("rm %(build_path)s" % env)

    put("conf/nginx-%(project_name)s.conf" % env, env.inst_dir)

    # Setup virtualenv
    if update_deps or not exists("/opt/%(project_name)s/virtualenvs/current" % env):
        create_venv()

    env.venv_dir = run("readlink /opt/%(project_name)s/virtualenvs/current" % env)
    run("ln -s %(venv_dir)s %(inst_dir)s/virtualenv" % env)

    # Link project
    run("rm -f /opt/%(project_name)s/current" % env)
    run("ln -s %(inst_dir)s /opt/%(project_name)s/current" % env)

    # Collect static files
#    run("mkdir %(inst_dir)s/static" % env)
    with prefix("source %(inst_dir)s/virtualenv/bin/activate" % env):
        with cd("%(inst_dir)s" % env):
            run("python manage.py collect")

    # Restart services
    sudo("service uwsgi restart")
    sudo("touch /opt/%(project_name)s/uwsgi_touch_reload" % env)


def create_venv():
    run("virtualenv /opt/%(project_name)s/virtualenvs/%(tstamp)s" % env)
    with prefix("source /opt/%(project_name)s/virtualenvs/%(tstamp)s/bin/activate" % env):
        run("pip install -r %(inst_dir)s/requirements.txt" % env)
    run("rm -f /opt/%(project_name)s/virtualenvs/current" % env)
    run("ln -s /opt/%(project_name)s/virtualenvs/%(tstamp)s "
        "/opt/%(project_name)s/virtualenvs/current" % env)
