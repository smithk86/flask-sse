from gevent import monkey
monkey.patch_all()

import pytest
from flask import Flask

from flask_sse import Broker


@pytest.fixture
def app():
    """ flask app for pytest-flask """

    app = Flask('live_server')
    sse = Broker(app, timeout=2, url='/subscribe')
    @app.route('/')
    def route():
        return 'OK'

    return app
