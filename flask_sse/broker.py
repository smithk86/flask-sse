import logging
from datetime import datetime
from copy import copy

from flask import Blueprint, Response, jsonify
from gevent.queue import Queue

from .server_sent_event import ServerSentEvent

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

logger = logging.getLogger(__name__)


class Broker:

    def __init__(self, app=None, debug=False, keepalive_interval=60, url='/events', cache_maxsize=100):
        self.debug = debug
        self._subscribers = list()
        self.keepalive_interval = keepalive_interval
        self.index = 0
        self.cache_maxsize = cache_maxsize
        self.init_cache()

        if app:
            self.init_app(app, url)

    def init_app(self, app, url):

        if 'sse' not in app.extensions:
            app.extensions['sse'] = self

        app.register_blueprint(self.create_blueprint(url))

        return self

    def __len__(self):
        return len(self._subscribers)

    def __iter__(self):
        for q in self._subscribers:
            yield q

    def cache(self):
        _copy = self._cache.copy()
        _copy.put(StopIteration)
        return _copy

    def init_cache(self):
        self._cache = Queue(maxsize=self.cache_maxsize)

    def create_blueprint(self, url):
        blueprint = Blueprint('sse', __name__)
        @blueprint.route(url)
        def subscribe():
            return Response(
                self.subscribe(),
                mimetype='text/event-stream'
            )
        if self.debug is True:
            @blueprint.route(url + '/debug')
            def debug():
                cache = list()
                for c in self.cache():
                    c = c.copy()
                    c['sse'] = dict(c.pop('sse'))
                    cache.append(c)
                return jsonify(
                    stats=self.stats(),
                    cache=cache
                )
        return blueprint

    def subscribe(self, use_cache=False, callback=None):

        q = Queue()
        if use_cache:
            for c in self.cache():
                q.put(c['sse'])

        self._subscribers.append(q)
        try:
            while True:
                try:
                    sse = q.get(timeout=self.keepalive_interval)
                    if sse is StopIteration:
                        break
                    elif isinstance(sse, ServerSentEvent):
                        sse = copy(sse)
                        if callable(callback):
                            callback(sse)
                        yield str(sse)
                except Empty:
                    yield str(ServerSentEvent(event='keepalive'))
        finally:
            logger.debug('removing queue from disconnected client')
            self._subscribers.remove(q)

    def put(self, **sse_args):

        self.index += 1
        if 'id' not in sse_args:
            sse_args['id'] = self.index
        sse = ServerSentEvent(**sse_args)

        if logger.isEnabledFor(logging.DEBUG):
            debug_sse_args = sse.format()
            debug_sse_args['data'] = debug_sse_args['data'] if len(debug_sse_args['data']) < 20 else '{}...'.format(debug_sse_args['data'][:20])
            logger.debug('queueing event: [{}]'.format(', '.join(['{}: {}'.format(k,v) for k, v in debug_sse_args.items()])))

        if self._cache.full():
            self._cache.get()
        self._cache.put({
            'index': self.index,
            'date': datetime.now(),
            'sse': sse
        })

        for q in self._subscribers:
            q.put(sse)

    def close(self):

        self.put(event='close')

        for q in self._subscribers:
            q.put(StopIteration)

    def cache_peek(self):

        try:
            return self._cache.peek_nowait()
        except Empty:
            return None

    def stats(self):

        return {
            'cache': {
                'qsize': self._cache.qsize(),
                'oldest': self.cache_peek()['date'] if self.cache_peek() else None
            },
            'subscribers_count': len(self._subscribers),
            'subscribers': [{'qsize': q.qsize()} for q in self._subscribers]
        }

    def put_rate(self, event):
        cache = self.cache()
        oldest_item =  cache.peek()
        if oldest_item is StopIteration:
            return
        date = oldest_item['date']
        event_count = 0
        for q in cache:
            if q['sse'].event == event:
                event_count += 1
        date_diff_seconds = (datetime.now() - date).total_seconds()
        rate = event_count / date_diff_seconds
        self.put(data=rate, event=f'{event}.rate')
