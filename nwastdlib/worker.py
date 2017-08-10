import signal
import sys
import json

from queue import Queue
from stomp import Connection, ConnectionListener

from . import Either, unargs


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

    def connect(self, mailbox):
        self.__conn = Connection(host_and_ports=[self.__host_and_port])
        self.__conn.start()
        self.__conn.connect(wait=True)
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
    def __init__(self, broker_host, broker_port, subid, inbound_queue):
        self.mailbox = Mailbox()
        self.broker = Broker(broker_host, broker_port)
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
        def parse_message(message):
            def getValue(k, data):
                v = data.get(k)
                if v is None:
                    return Either.Left("%s is not specified" % k)
                else:
                    return Either.Right(v)

            try:
                data = json.loads(message)
            except:
                return Either.Left("invalid data format")

            Either.sequence((
                getValue("subscription_id", data),
                getValue("job_id", data),
                getValue("step_id", data),
                getValue("payload", data)
            ))

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
                    .map(lambda args: (dict(subscription_id=args[0], job_id=args[1], step_id=args[2]), args[3])) \
                    .flatmap(unargs(handler)) \
                    .either(handle_error, handle_success)
            except Exception as e:
                print("%s: %s (message: %s)" % (e.__class__.__name__, e, message), file=sys.stderr)
                self.fatal_messages_count += 1
