import pytest

from data import *
from flask_sse import ServerSentEvent


@pytest.mark.parametrize('obj,string', [
    pytest.param(sse_keepalive_obj, sse_keepalive_str),
    pytest.param(sse_close_obj, sse_close_str),
    pytest.param(sse_test_objects[0], sse_test_str[0]),
    pytest.param(sse_test_objects[1], sse_test_str[1]),
    pytest.param(sse_test_objects[2], sse_test_str[2]),
    pytest.param(sse_test_objects[3], sse_test_str[3]),
    pytest.param(sse_test_objects[4], sse_test_str[4])
])
def test_server_sent_event(obj, string):

    assert str(obj) == string


def test_server_sent_event_exception():

    with pytest.raises(ValueError, match='data and event cannot both be None'):
        ServerSentEvent(id=4)
