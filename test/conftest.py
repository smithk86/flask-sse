from gevent import monkey
monkey.patch_all()

import pytest
from flask import Flask


@pytest.fixture
def app():
    """ flask app for pytest-flask to test flask-sse"""

    app = Flask('live_server')
    @app.route('/')
    def route():
        return 'OK'

    return app
