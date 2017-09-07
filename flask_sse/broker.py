import logging
from datetime import datetime

from flask import Blueprint, Response, jsonify
from gevent.queue import Queue

from .server_sent_event import ServerSentEvent

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

logger = logging.getLogger(__name__)


class Broker:

    def __init__(self, app=None, debug=False, keepalive_interval=60, url=None, cache_maxsize=100):

        cache_maxsize = int(cache_maxsize)

        if cache_maxsize < 1:
            raise ValueError('cache maxsize must be greater than zero')

        self.debug = debug
        self._subscribers = list()
        self.keepalive_interval = keepalive_interval
        self.index = 0
        self.cache = Queue(maxsize=cache_maxsize)

        if app:
            self.init_app(app, url, )

    def init_app(self, app, url='/events'):

        if 'sse' not in app.extensions:
            app.extensions['sse'] = self

        app.register_blueprint(self.create_blueprint(url))

        return self

    def __len__(self):
        return len(self._subscribers)

    def __iter__(self):
        for q in self._subscribers:
            yield q

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
                for c in self.cache_dump():
                    c = c.copy()
                    c['sse'] = dict(c.pop('sse'))
                    cache.append(c)
                return jsonify(
                    stats=self.stats(),
                    cache=cache
                )
        return blueprint

    def subscribe(self, use_cache=False, callback=None):

        q = self.cache.copy() if use_cache is True else Queue()
        self._subscribers.append(q)

        try:
            while True:
                try:
                    sse = q.get(timeout=self.keepalive_interval)
                    if sse is StopIteration:
                        break
                    if callable(callback):
                        sse = callback(sse)
                    if sse:
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
        logger.debug('queueing event: [{}]'.format(', '.join(['{}: {}'.format(k,v) for k, v in sse_args.items()])))

        if self.cache.full():
            self.cache.get()
        self.cache.put({
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
            return self.cache.peek_nowait()
        except Empty:
            return None

    def stats(self):

        return {
            'cache': {
                'qsize': self.cache.qsize(),
                'oldest': self.cache_peek()['date'] if self.cache_peek() else None
            },
            'subscribers_count': len(self._subscribers),
            'subscribers': [{'qsize': q.qsize()} for q in self._subscribers]
        }

    def cache_dump(self):

        _copy = self.cache.copy()
        while _copy.qsize() > 0:
            yield _copy.get()
