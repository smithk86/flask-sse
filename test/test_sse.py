from collections import OrderedDict

from flask import url_for
import pytest
import requests
import gevent
from gevent import sleep
from gevent.pool import Group

from flask_sse import ServerSentEvent, Broker
from pytest_flask_gevent_wsgiserver.plugin import live_server

_sse_keepalive_data = {'event': 'keepalive'}
_sse_close_data = {'event': 'close'}
_sse_test_data = [
    {'data': '1166aa5d-195b-4a7a-8289-b95347aa2185'},
    {'event': 'event2'},
    {'data': '82055a6c-8da5-404f-bd6e-b748c7bb468d', 'event': 'event3', 'id': 3},
    {'data': OrderedDict([('item1', '1'), ('item2', 2), ('item3', 3.99)]), 'event': 'event4', 'id': 4},
    {'data': '7be75703-aca9-4be4-a758-e9a78588a2f2', 'retry': 10000}
]

_sse_keepalive_obj = ServerSentEvent(**_sse_keepalive_data)
_sse_close_obj = ServerSentEvent(**_sse_close_data)
_sse_test_objects = [
    ServerSentEvent(**_sse_test_data[0]),
    ServerSentEvent(**_sse_test_data[1]),
    ServerSentEvent(**_sse_test_data[2]),
    ServerSentEvent(**_sse_test_data[3]),
    ServerSentEvent(**_sse_test_data[4])
]

_sse_keepalive_str = 'data: -\nevent: keepalive\n\n'
_sse_close_str = 'data: -\nevent: close\n\n'
_sse_test_str = [
    'data: 1166aa5d-195b-4a7a-8289-b95347aa2185\n\n',
    'data: -\nevent: event2\n\n',
    'data: 82055a6c-8da5-404f-bd6e-b748c7bb468d\nevent: event3\nid: 3\n\n',
    'data: {"item1": "1", "item2": 2, "item3": 3.99}\nevent: event4\nid: 4\n\n',
    'retry: 10000\ndata: 7be75703-aca9-4be4-a758-e9a78588a2f2\n\n'
]


def capture_stream(url):
    sse_output_request = ''
    with requests.get(url, stream=True) as r:
        for chunk in r.iter_content(decode_unicode=True):
            sse_output_request += chunk
    return sse_output_request


@pytest.mark.parametrize('obj,string', [
    pytest.param(_sse_keepalive_obj, _sse_keepalive_str),
    pytest.param(_sse_close_obj, _sse_close_str),
    pytest.param(_sse_test_objects[0], _sse_test_str[0]),
    pytest.param(_sse_test_objects[1], _sse_test_str[1]),
    pytest.param(_sse_test_objects[2], _sse_test_str[2]),
    pytest.param(_sse_test_objects[3], _sse_test_str[3]),
    pytest.param(_sse_test_objects[4], _sse_test_str[4])
])
def test_server_sent_event(obj, string):

    assert str(obj) == string


def test_server_sent_event_exception():

    with pytest.raises(ValueError, match='data and event cannot both be None'):
        ServerSentEvent(id=4)


def test_broker_maxsize():

    with pytest.raises(ValueError, match='cache maxsize must be greater than zero'):
        Broker(cache_maxsize=0)

    with pytest.raises(TypeError, match='unorderable types: NoneType\(\) < int\(\)'):
        Broker(cache_maxsize=None)

    with pytest.raises(TypeError, match='unorderable types: str\(\) < int\(\)'):
        Broker(cache_maxsize='3000')


@pytest.mark.usefixtures('live_server')
class TestBroker:

    def test_sequence(request, app):
        """ run event sequence with multiple subscribers """

        def event_data(with_sleep=False):
            i = 0
            for data in _sse_test_data:
                i += 1
                data['id'] = i
                yield data
            sleep(3)
            for data in _sse_test_data:
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
            for _ in range(len(_sse_test_data)):
                data = next(events_iter)
                output += str(ServerSentEvent(**data))
            output += _sse_keepalive_str
            for _ in range(len(_sse_test_data)):
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
        assert broker.cache.qsize() == (len(_sse_test_data) * 2) + 1
        for output in subscriber_output:
            assert generate_mock_output() == output

    def test_keepalive(request, app):

        broker = Broker(keepalive_interval=2, url='/subscribe')
        broker.init_app(app)

        output = ''
        for _ in range(4):
            output += _sse_keepalive_str
        output += str(ServerSentEvent(**{'event': 'close', 'id': 1}))

        gevent.spawn_later(9, broker.close)

        stream = capture_stream(
            url_for('sse.subscribe', _external=True)
        )

        assert output == stream
