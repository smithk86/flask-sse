from collections import OrderedDict

from flask import url_for
import pytest
import requests
import gevent

from flask_sse import ServerSentEvent


test_sse_data = [
    {'data': '1166aa5d-195b-4a7a-8289-b95347aa2185'},
    {'event': 'event2'},
    {'data': '82055a6c-8da5-404f-bd6e-b748c7bb468d', 'event': 'event3', 'id': 3},
    {'data': OrderedDict([('item1', '1'), ('item2', 2), ('item3', 3.99)]), 'event': 'event4', 'id': 4},
    {'data': '7be75703-aca9-4be4-a758-e9a78588a2f2', 'retry': 10000}
]
test_sse_objects = [
    ServerSentEvent(**test_sse_data[0]),
    ServerSentEvent(**test_sse_data[1]),
    ServerSentEvent(**test_sse_data[2]),
    ServerSentEvent(**test_sse_data[3]),
    ServerSentEvent(**test_sse_data[4])
]
test_sse_str_ping = 'data: -\nevent: ping\n\n'
test_sse_str_close = 'data: -\nevent: close\n\n'
test_sse_str = [
    'data: 1166aa5d-195b-4a7a-8289-b95347aa2185\n\n',
    'data: -\nevent: event2\n\n',
    'data: 82055a6c-8da5-404f-bd6e-b748c7bb468d\nevent: event3\nid: 3\n\n',
    'data: {"item1": "1", "item2": 2, "item3": 3.99}\nevent: event4\nid: 4\n\n',
    'retry: 10000\ndata: 7be75703-aca9-4be4-a758-e9a78588a2f2\n\n'
]


@pytest.mark.parametrize('sse,string', [
    pytest.param(test_sse_objects[0], test_sse_str[0]),
    pytest.param(test_sse_objects[1], test_sse_str[1]),
    pytest.param(test_sse_objects[2], test_sse_str[2]),
    pytest.param(test_sse_objects[3], test_sse_str[3]),
    pytest.param(test_sse_objects[4], test_sse_str[4])
])
def test_server_sent_event(sse, string):

    assert str(sse) == string


def test_server_sent_event_exception():

    with pytest.raises(ValueError, match='data and event cannot both be None'):
        ServerSentEvent(id=4)


@pytest.mark.usefixtures('live_server')
def test_sse_broker(request, app):

    def queue_sse(broker):
        for data in test_sse_data:
            broker.put(**data)
        gevent.sleep(2)
        for data in test_sse_data:
            broker.put(**data)
        broker.close()

    sse_output_proto = ''
    for s in test_sse_str:
        sse_output_proto += s
    sse_output_proto += test_sse_str_ping
    for s in test_sse_str:
        sse_output_proto += s
    sse_output_proto += test_sse_str_close

    gevent.spawn_later(1, queue_sse, app.extensions['sse'])

    sse_output_request = ''
    with requests.get(url_for('sse.route_subscribe', _external=True), stream=True) as r:
        for chunk in r.iter_content(decode_unicode=True):
            sse_output_request += chunk

    assert sse_output_proto == sse_output_request
