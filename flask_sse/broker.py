import logging

from flask import Blueprint, Response
from queue import Empty
from gevent.queue import Queue

from .server_sent_event import ServerSentEvent


logger = logging.getLogger(__name__)


class Broker:

    def __init__(self, app=None, keepalive_interval=60, url=None):

        self._subscribers = list()
        self.keepalive_interval = keepalive_interval

        if app:
            self.init_app(app, url)

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
        def route_subscribe():
            return Response(
                self.subscribe(),
                mimetype='text/event-stream'
            )
        return blueprint

    def subscribe(self, callback=None):

        q = Queue()
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

        logger.debug('queueing event: [{}]'.format(', '.join(['{}: {}'.format(k,v) for k, v in sse_args.items()])))
        for q in self._subscribers:
            sse = ServerSentEvent(**sse_args)
            q.put(sse)

    def close(self):

        self.put(event='close')

        for q in self._subscribers:
            q.put(StopIteration)
