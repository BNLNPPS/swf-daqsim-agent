import os
import sys
import stomp
import ssl
import time

###################################################################
# Ensure the path to the DAQSIM_PATH is set correctly
daqsim_path = os.environ.get('DAQSIM_PATH', '../')  # Default to parent directory
if daqsim_path not in sys.path: sys.path.append(daqsim_path)

mq_user     = os.environ.get('MQ_USER',     None) # this will fail if not set
mq_passwd   = os.environ.get('MQ_PASSWD',   None)

mq_port     = int(os.environ.get('MQ_PORT', 61612))

mq_host     = os.environ.get('MQ_HOST',     'pandaserver02.sdcc.bnl.gov')
mq_cafile   = os.environ.get('MQ_CAFILE',   daqsim_path + '/config/full-chain.pem')


###################################################################
class Messenger:
    """
    A messenger class for sending and receiving messages using ActiveMQ/Artemis,
    for communication with other components in the ePIC streaming testbed system.

    This class provides methods to connect to an ActiveMQ/Artemis server, send messages,
    subscribe to topics, and receive messages. It uses the `stomp.py` library
    for communication with the ActiveMQ server.
    """

    def __init__(self, host=mq_host, port=mq_port, username=mq_user, password=mq_passwd, verbose=False):
        self.host       = host
        self.port       = port
        self.username   = username
        self.password   = password

        if(not self.username or not self.password):
            raise ValueError("MQ_USER and MQ_PASSWD environment variables must be set.")

        self.verbose = verbose
        if self.verbose:
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



    def disconnect(self):
        """Disconnect from the ActiveMQ server."""
        if self.conn:
            self.conn.disconnect()

    
    # ^ Upstream is commmon for sender and receiver ^

    def connect(self):
        print('** Base class: Connecting to ActiveMQ server... **')


    def send(self):
        print('** Base class: Sending message to ActiveMQ server... **')

###################################################################
class Sender(Messenger):
    def __init__(self, host=mq_host, port=mq_port, username=mq_user, password=mq_passwd, verbose=False):
        super().__init__(host=mq_host, port=mq_port, username=mq_user, password=mq_passwd, verbose=verbose)


    # ---
    def connect(self):
        print('** Sender connecting to ActiveMQ server... **', self.verbose)
        try:
            self.conn.connect(login=self.username, passcode=self.password, wait=True, version='1.2')
            if self.conn.is_connected():
                if self.verbose:
                    print("*** Sender connected to MQ server at {}:{} ***".format(self.host, self.port))
            else:
                # if self.verbose:
                print("*** Sender not connected to MQ server at {}:{} ***".format(self.host, self.port))
        except Exception as e:
            print("Sender connection failed:", type(e).__name__, e)

    # ---
    def send(self, destination='epictopic', body='heartbeat', headers={'persistent': 'true'}):
        self.conn.send(destination=destination, body=body, headers=headers)

###################################################################
class Listener(stomp.ConnectionListener):
    def __init__(self, processor=None, verbose=False):
        super().__init__()
        self.processor  = processor
        self.verbose    = verbose


    def on_connected(self, headers):
        if self.verbose:
            print(f'''*** Connected to broker: {headers} ***''')

    def on_message(self, frame):
        if self.processor:
            self.processor(frame.body)

    def on_error(self, frame):
        print(f"Error from broker: {frame}")

    def on_disconnected(self):
        print("Disconnected from broker")


# ---
# The Receiver class is a subclass of Messenger that is used to receive messages from the ActiveMQ server.
# It inherits the connection and disconnection methods from Messenger and can be extended to add more functionality.

class Receiver(Messenger):
    def __init__(self, host=mq_host, port=mq_port, username=mq_user, password=mq_passwd, verbose=False, processor=None):
        super().__init__(host=mq_host, port=mq_port, username=mq_user, password=mq_passwd, verbose=verbose)
        self.processor = processor

    # ---
    def connect(self):
        # Attach listener
        self.conn.set_listener('', Listener(verbose=self.verbose, processor=self.processor))
        
        #self.conn.set_listener('debug', stomp.PrintingListener())
        # Connect with a durable client-id
        try:
            self.conn.connect(login=self.username, passcode=self.password, wait=True, version='1.2', headers={'client-id': 'sub-test-001'})
            if self.conn.is_connected():
                if self.verbose:
                    print("*** Receiver connected to MQ server at {}:{} ***".format(self.host, self.port))
            else:
                if self.verbose:
                    print("*** Receiver not connected to MQ server at {}:{} ***".format(self.host, self.port))
        except Exception as e:
            print("Receiver connection failed:", type(e).__name__, e)



        # Subscribe with durable subscription name
        self.conn.subscribe(
            destination='epictopic',
            id='sub-test-001',
            ack='auto',
            headers={'activemq.subscriptionName': 'test-durable-sub'}
            )

