from collections import OrderedDict as _OrderedDict
from flask_sse import ServerSentEvent as _ServerSentEvent


sse_keepalive_data = {'event': 'keepalive'}
sse_close_data = {'event': 'close'}
sse_test_data = [
    {'data': '1166aa5d-195b-4a7a-8289-b95347aa2185'},
    {'event': 'event2'},
    {'data': '82055a6c-8da5-404f-bd6e-b748c7bb468d', 'event': 'event3', 'id': 3},
    {'data': _OrderedDict([('item1', '1'), ('item2', 2), ('item3', 3.99)]), 'event': 'event4', 'id': 4},
    {'retry': 10000, 'data': '7be75703-aca9-4be4-a758-e9a78588a2f2'}
]

sse_keepalive_obj = _ServerSentEvent(**sse_keepalive_data)
sse_close_obj = _ServerSentEvent(**sse_close_data)
sse_test_objects = [
    _ServerSentEvent(**sse_test_data[0]),
    _ServerSentEvent(**sse_test_data[1]),
    _ServerSentEvent(**sse_test_data[2]),
    _ServerSentEvent(**sse_test_data[3]),
    _ServerSentEvent(**sse_test_data[4])
]

sse_keepalive_str = 'data: -\nevent: keepalive\n\n'
sse_close_str = 'data: -\nevent: close\n\n'
sse_test_str = [
    'data: 1166aa5d-195b-4a7a-8289-b95347aa2185\n\n',
    'data: -\nevent: event2\n\n',
    'data: 82055a6c-8da5-404f-bd6e-b748c7bb468d\nevent: event3\nid: 3\n\n',
    'data: {"item1": "1", "item2": 2, "item3": 3.99}\nevent: event4\nid: 4\n\n',
    'retry: 10000\ndata: 7be75703-aca9-4be4-a758-e9a78588a2f2\n\n'
]
