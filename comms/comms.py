import os
import sys
import stomp

# Ensure the path to the DAQSIM_PATH is set correctly
daqsim_path = os.environ.get('DAQSIM_PATH', '../')  # Default to parent directory if not set
if daqsim_path not in sys.path: sys.path.append(daqsim_path)

class Messenger:
    """
    A messenger class for sending and receiving messages using ActiveMQ, for communication
    with other components in the ePIC streaming testbed system.

    This class provides methods to connect to an ActiveMQ server, send messages,
    subscribe to topics, and receive messages. It uses the `stomp.py` library
    for communication with the ActiveMQ server.
    """

    def __init__(self, host='localhost', port=61613, username=None, password=None, verbose=False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conn = None

    def connect(self):
        """Connect to the ActiveMQ server."""
        import stomp
        self.conn = stomp.Connection([(self.host, self.port)])
        if self.username and self.password:
            self.conn.connect(self.username, self.password, wait=True)
        else:
            self.conn.connect(wait=True)

    def disconnect(self):
        """Disconnect from the ActiveMQ server."""
        if self.conn:
            self.conn.disconnect()

    def send(self, destination, message, headers=None):
        """Send a message to a specified destination."""
        if not self.conn:
            raise Exception("Not connected to ActiveMQ server.")
        headers = headers or {}
        self.conn.send(destination=destination, body=message, headers=headers)

    def subscribe(self, destination, callback, id='1', ack='auto'):
        """Subscribe to a topic and set a callback for received messages."""
        if not self.conn:
            raise Exception("Not connected to ActiveMQ server.")
        self.conn.set_listener(id, callback)
        self.conn.subscribe(destination=destination, id=id, ack=ack)

    def unsubscribe(self, id='1'):
        """Unsubscribe from a topic."""
        if not self.conn:
            raise Exception("Not connected to ActiveMQ server.")
        self.conn.unsubscribe(id=id)


    def receive(self, timeout=None):
        """Receive a message from the ActiveMQ server."""
        if not self.conn:
            raise Exception("Not connected to ActiveMQ server.")
        return self.conn.receive(timeout=timeout) if timeout else self.conn.receive()
    def is_connected(self):
        """Check if the connection to the ActiveMQ server is active."""
        return self.conn is not None and self.conn.is_connected()
    def get_connection_info(self):
        """Get the connection information."""
        if not self.conn:
            raise Exception("Not connected to ActiveMQ server.")
        return {
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'is_connected': self.is_connected()
        }
    def __enter__(self):
        """Enter the runtime context related to this object."""
        self.connect()
        return self