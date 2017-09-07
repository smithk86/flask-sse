import sys
import json
from collections import OrderedDict

from flask import url_for
from  werkzeug.routing import BuildError
import pytest
import requests
import gevent
from gevent import sleep
from gevent.pool import Group

from data import *
from flask_sse import ServerSentEvent, Broker
from pytest_flask_gevent_wsgiserver.plugin import live_server

PY3 = sys.version_info > (3,)


def capture_stream(url):
    sse_output_request = ''
    with requests.get(url, stream=True) as r:
        for chunk in r.iter_content(decode_unicode=True):
            sse_output_request += chunk
    return sse_output_request


def test_broker_maxsize():

    Broker(cache_maxsize='3000')

    with pytest.raises(ValueError, match='cache maxsize must be greater than zero'):
        Broker(cache_maxsize=0)

    if PY3:
        with pytest.raises(TypeError, match="int\(\) argument must be a string, a bytes-like object or a number, not 'NoneType'"):
            Broker(cache_maxsize=None)
    else:
        with pytest.raises(TypeError, match="int\(\) argument must be a string or a number, not 'NoneType'"):
            Broker(cache_maxsize=None)


@pytest.mark.usefixtures('live_server')
class TestBroker:

    def test_broker(self, app):
        """ run event sequence with multiple subscribers """

        def event_data(with_sleep=False):
            i = 0
            for data in sse_test_data:
                i += 1
                data['id'] = i
                yield data
            sleep(3)
            for data in sse_test_data:
                i += 1
                data['id'] = i
                yield data

        def put_events(broker):
            for data in event_data(with_sleep=True):
                broker.put(**data)
            broker.close()

        def generate_mock_output():
            output = ''
            events_iter = event_data()
            for _ in range(len(sse_test_data)):
                data = next(events_iter)
                output += str(ServerSentEvent(**data))
            output += sse_keepalive_str
            for _ in range(len(sse_test_data)):
                data = next(events_iter)
                output += str(ServerSentEvent(**data))
            output += str(ServerSentEvent(**{'event': 'close', 'id': 11}))
            return output

        def do_stream(output_list, url):
            output_list.append(
                capture_stream(url)
            )

        Broker(app, keepalive_interval=2, url='/subscribe')
        broker = app.extensions['sse']

        # confirm the debug route DOES NOT work
        with pytest.raises(BuildError, match='Could not build url for endpoint'):
            url_for('sse.debug', _external=True)

        processes = Group()
        number_of_subscribers = 3
        subscriber_output = list()
        url = url_for('sse.subscribe', _external=True)
        for _ in range(number_of_subscribers):
            processes.add(gevent.spawn(do_stream, subscriber_output, url))
        while len(broker) != number_of_subscribers:
            sleep(.25)
        else:
            put_events(broker)
            processes.join()

        assert len(subscriber_output) == number_of_subscribers
        assert broker.cache.qsize() == (len(sse_test_data) * 2) + 1
        for output in subscriber_output:
            assert generate_mock_output() == output

    def test_keepalive(self, app):

        broker = Broker(keepalive_interval=2, url='/subscribe')
        broker.init_app(app)

        output = ''
        for _ in range(4):
            output += sse_keepalive_str
        output += str(ServerSentEvent(**{'event': 'close', 'id': 1}))

        gevent.spawn_later(9, broker.close)

        stream = capture_stream(
            url_for('sse.subscribe', _external=True)
        )

        assert output == stream

    def test_debug(self, app):

        Broker(app, debug=True, url='/subscribe')
        broker = app.extensions['sse']

        url = url_for('sse.debug', _external=True)
        r = requests.get(url)
        debug = json.loads(r.text)
        assert 'cache' in debug
        assert 'stats' in debug
