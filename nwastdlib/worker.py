import signal
import sys
import json

from queue import Queue
from stomp import Connection, ConnectionListener

from . import Either, unargs
from . import dict as Dict
from .ex import show_ex


class Mailbox(ConnectionListener):
    """Mailbox that contains messages from a STOMP connection.

    Messages are queued for a received to process them one-by-one. A message
    is a pair of body and headers."""

    def __init__(self):
        self.__inbox = Queue()

    def receive(self):
        return self.__inbox.get()

    def on_message(self, headers, message):
        self.__inbox.put((message, headers))

    def on_error(self, headers, message):
        print("Received an error from the broker\nMessage: %s\nHeaders: %s" % (message, headers))


class Broker(object):
    def __init__(self, hostname, port):
        self.__host_and_port = (hostname, port)

    def connect(self, username, password, mailbox, **connect_args):
        self.__conn = Connection(host_and_ports=[self.__host_and_port], **connect_args)
        self.__conn.start()
        self.__conn.connect(username, password, wait=True)
        self.__conn.set_listener('mailbox', mailbox)
        self.__subscriptions = []

    def subscribe(self, subid, queue):
        assert self.__conn, "Not connected"
        self.__conn.subscribe(destination=queue, id=subid, ack="auto")  # TODO manually ack processed messages
        self.__subscriptions.append(subid)

    def send(self, destination, message):
        assert self.__conn, "Not connected"
        self.__conn.send(body=message, destination=destination)

    def disconnect(self):
        assert self.__conn, "Not connected"
        [self.__conn.unsubscribe(x) for x in self.__subscriptions]
        self.__conn.disconnect(wait=True)
        self.__conn.stop()

    def __str__(self):
        return "%s:%d" % self.__host_and_port


class Worker(object):
    def __init__(self, broker, subid, inbound_queue):
        self.mailbox = Mailbox()
        self.broker = broker
        self.subid = subid
        self.inbound_queue = inbound_queue
        self.processed_messages_count = 0
        self.erroneous_messages_count = 0
        self.fatal_messages_count = 0

    def __connect(self):
        self.broker.connect(self.mailbox)
        self.broker.subscribe(self.subid, self.inbound_queue)

    def __disconnect(self):
        self.broker.disconnect()

    def __sighub(self, signal, frame):
        print("Reconnecting..")
        self.__disconnect()
        self.__connect()

    def __sigterm(self, signal, frame):
        print("Interrupted with signal %s. Shutting down.." % signal)
        self.__disconnect()
        sys.exit()

    def __sigusr1(self, signal, frame):
        print("Worker Report: %d processed; %d erroneous; %d fatal" %
              (self.processed_messages_count, self.erroneous_messages_count, self.fatal_messages_count))

    def run(self, handler):
        '''
        Start the worker and run incoming messages through `handler` - a function
        that is called with metadata and payload and returns None.
        '''

        def parse_dict(s):
            try:
                data = json.loads(s)
                if type(data) == dict:
                    return Either.Right(data)
                else:
                    return Either.Left("not a json dict: %s" % s)
            except:
                return Either.Left("invalid json data: %s" % s)

        def parse_message(message):
            def extract_metadata_and_payload(data):
                metadata = Dict.getByKeys({"subscription_id", "task_id", "reply_to"}, data).first(lambda k: "missing key: %s" % k)
                payload = Dict.lookup("payload", data).maybe(Either.Left("missing key: payload"), parse_dict)
                return Either.sequence((metadata, payload))

            return parse_dict(message) \
                .flatmap(extract_metadata_and_payload)

        try:
            self.__connect()
        except Exception as e:
            print("Cannot connect to broker %s\n%s" % (self.broker, e), file=sys.stderr)
            sys.exit(2)

        signal.signal(signal.SIGTERM, self.__sigterm)
        signal.signal(signal.SIGINT, self.__sigterm)
        signal.signal(signal.SIGHUP, self.__sighub)
        signal.signal(signal.SIGUSR1, self.__sigusr1)

        print("Worker is now connected to %s and listening on '%s'" % (self.broker, self.inbound_queue))

        while True:
            (message, headers) = self.mailbox.receive()

            def handle_success(ignore):
                self.processed_messages_count += 1

            def handle_error(err):
                print("Error while processing message: %s\nMessage: %s" % (err, message), file=sys.stderr)
                self.erroneous_messages_count += 1

            try:
                parse_message(message) \
                    .flatmap(unargs(handler)) \
                    .either(handle_error, handle_success)
            except Exception as e:
                self.fatal_messages_count += 1
                print("Failed to handle message: %s\n%s" % (message, show_ex(e)), file=sys.stderr)

    def reply(self, metadata, data):
        def send(destination):
            payload = Dict.delete("reply_to", metadata)
            self.broker.send(destination, json.dumps({"status": "complete", **payload, **data}))

        Dict.lookup("reply_to", metadata).maybe(Either.Left("reply_to not in metadata"), Either.Right) \
            .map(send) \
            .first(lambda msg: print("Failed to send reply: %s" % msg))
