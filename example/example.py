#!/usr/bin/env python

import logging
from uuid import uuid4

from flask import current_app, Flask, render_template
from flask_sse import Broker
import gevent
from gevent.wsgi import WSGIServer


logging.basicConfig(level=logging.DEBUG)

app = Flask(
	'example',
	template_folder=''
)
Broker(app, debug=True)


def put_uuid():
	while True:
		gevent.sleep(15)
		with app.app_context():
			broker = current_app.extensions['sse']
			broker.put(event='uuid', data=str(uuid4()))
gevent.spawn(put_uuid)


@app.route('/')
def index():
	return render_template('example.html')


@app.route('/<msg>')
def message(msg):
    broker = current_app.extensions['sse']
    broker.put(data=msg)
    return 'OK'


WSGIServer(('0.0.0.0', 5000), app).serve_forever()
