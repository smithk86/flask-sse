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
        items = OrderedDict(self)
        if items['data'] is None:
            items['data'] = '-'
        elif isinstance(items['data'], str):
            pass
        else:
            items['data'] = json.dumps(items['data'])
        return items

    def __iter__(self):
        if self.retry:
            yield 'retry', self.retry
        yield 'data', self.data
        if self.event:
            yield 'event', self.event
        if self.id:
            yield 'id', self.id

    def __str__(self):
        return '{}\n\n'.format('\n'.join(
            ['{}: {}'.format(k, v) for k, v in self.format().items()]
        ))

    def __repr__(self):
        return '<ServerSentEvent event="{}">'.format(self.event if self.event else '')
