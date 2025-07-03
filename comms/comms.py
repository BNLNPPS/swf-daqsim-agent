import os
import sys
import stomp
import ssl

# Ensure the path to the DAQSIM_PATH is set correctly
daqsim_path = os.environ.get('DAQSIM_PATH', '../')  # Default to parent directory if not set
if daqsim_path not in sys.path: sys.path.append(daqsim_path)

mq_user     = os.environ.get('MQ_USER',     None)
mq_passwd   = os.environ.get('MQ_PASSWD',   None)

mq_port     = int(os.environ.get('MQ_PORT', 61612))

mq_host     = os.environ.get('MQ_HOST',     'pandaserver02.sdcc.bnl.gov')
mq_cafile   = os.environ.get('MQ_CAFILE',   daqsim_path + '/config/full-chain.pem')

class Messenger:
    """
    A messenger class for sending and receiving messages using ActiveMQ, for communication
    with other components in the ePIC streaming testbed system.

    This class provides methods to connect to an ActiveMQ server, send messages,
    subscribe to topics, and receive messages. It uses the `stomp.py` library
    for communication with the ActiveMQ server.
    """

    def __init__(self, host=mq_host, port=mq_port, username=mq_user, password=mq_passwd, verbose=False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        if(not self.username or not self.password):
            raise ValueError("MQ_USER and MQ_PASSWD environment variables must be set.")

        self.verbose = verbose
        print(f"Initializing Messenger with host={self.host}, port={self.port}, username={self.username}")
        self.conn = stomp.Connection(host_and_ports=[(host, port)], vhost=host,try_loopback_connect=False)

        if not self.conn: raise Exception("Connection object is not initialized.")
    
        # Set SSL parameters for the connection
        if not os.path.exists(mq_cafile):      
            raise FileNotFoundError(f"MQ_CAFILE '{mq_cafile}' does not exist.")

        self.conn.transport.set_ssl(
            for_hosts=[(mq_host, mq_port)],
            ca_certs=mq_cafile,
            ssl_version=ssl.PROTOCOL_TLS_CLIENT
        )

        try:
            self.conn.connect(login=self.username, passcode=self.password, wait=True, version='1.2')
            if self.conn.is_connected():
                print("Connected to MQ server at {}:{}".format(self.host, self.port))
            else:
                print("Failed to connect to MQ server at {}:{}".format(self.host, self.port))
        except Exception as e:
            print("Connection failed:", type(e).__name__, e)



    def disconnect(self):
        """Disconnect from the ActiveMQ server."""
        if self.conn:
            self.conn.disconnect()


    def send(self):
        try:
            self.conn.connect(login=self.username, passcode=self.password, wait=True, version='1.2')
            if self.conn.is_connected():
                print("Connected to ActiveMQ server at {}:{}".format(self.host, self.port))
            else:
                print("Failed to connect to ActiveMQ server at {}:{}".format(self.host, self.port))
                return
            self.conn.send(destination='epictopic', body='heartbeat', headers={'persistent': 'true'})

            print("Message sent")
            self.conn.disconnect()
        except Exception as e:
            print("Connection failed:", type(e).__name__, e)

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