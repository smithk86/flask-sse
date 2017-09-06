import json
from collections import OrderedDict


# SSE "protocol" is described here: http://mzl.la/UPFyxY
class ServerSentEvent(object):

    def __init__(self, data=None, event=None, retry=None, id=None):

        if data is None and event is None:
            raise ValueError('data and event cannot both be None')

        self.data = data
        self.event = event
        self.retry = retry
        self.id = id

    def format(self):

        if self.data is None:
            _data = '-'
        elif isinstance(self.data, str):
            _data = self.data
        else:
            _data = json.dumps(self.data)

        output = OrderedDict()

        if self.retry:
            output['retry'] = self.retry
        output['data'] = _data
        if self.event:
            output['event'] = self.event
        if self.id:
            output['id'] = self.id

        return output

    def __str__(self):

        return '{}\n\n'.format('\n'.join(
            ['{}: {}'.format(k, v) for k, v in self.format().items()]
        ))
