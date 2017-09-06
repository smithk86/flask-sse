from gevent import monkey
monkey.patch_all()

import pytest
from flask import Flask

from flask_sse import Broker


@pytest.fixture
def app():
    """ flask app for pytest-flask to test flask-sse"""

    app = Flask('live_server')
    sse = Broker(app, keepalive_interval=2, url='/subscribe')
    @app.route('/')
    def route():
        return 'OK'

    return app
