import logging

from flask import Blueprint, Response
from queue import Empty
from gevent.queue import Queue

from .server_sent_event import ServerSentEvent


logger = logging.getLogger(__name__)


class Broker:

    def __init__(self, app=None, timeout=30, url=None):

        self._subscribers = list()
        self.timeout = timeout

        if app:
            self.init_app(app, url)

    def init_app(self, app, url=None):

        if 'sse' not in app.extensions:
            app.extensions['sse'] = self

        if url:
            app.register_blueprint(self.create_blueprint(url))

    def __len__(self):

        return len(self._subscribers)

    def __iter__(self):

        for subscriber in self._subscribers:
            yield subscriber

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

        subscriber = {
            'queue': Queue(),
            'events_stats': dict()
        }
        self._subscribers.append(subscriber)

        try:
            while True:
                try:
                    sse = subscriber['queue'].get(timeout=self.timeout)
                    if sse is StopIteration:
                        break
                    if callable(callback):
                        sse = callback(sse)
                    if sse:
                        yield str(sse)
                except Empty:
                    yield str(ServerSentEvent(event='ping'))

        finally:
            logger.debug('removing queue from disconnected client')
            self._subscribers.remove(subscriber)

    def put(self, **sse_args):

        stats_event_key = sse_args.get('event') if sse_args.get('event') else '_'
        logger.debug('queueing SSE: [{}]'.format(', '.join(['{}: {}'.format(k,v) for k, v in sse_args.items()])))
        for subscriber in self._subscribers:
            sse = ServerSentEvent(**sse_args)
            if stats_event_key not in subscriber['events_stats']:
                subscriber['events_stats'][stats_event_key] = 0
            subscriber['events_stats'][stats_event_key] += 1
            subscriber['queue'].put(sse)

    def close(self):

        self.put(event='close')

        for q in [s['queue'] for s in self._subscribers]:
            q.put(StopIteration)
