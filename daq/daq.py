#
# daq/daq.py
#
# This is the DAQ simulator. It includes the main DAQ class, which simulates the data acquisition process. 
# There are a number of utility functions as well.
#
# STF MQ mewssages are stubbed out, and then updated with the checksum and size of the generated STF file.


import numpy as np
import simpy, yaml, random, json, bisect, zlib, os, requests, random, urllib3
import datetime
from   datetime import datetime as dt

from api_utils import get_next_run_number  # to get the next run number from the run monitor (common)
# ---
timeformat = "%Y%m%d%H%M%S%f"  # Format for the STF start and end times in metadata

# ---
def calculate_adler32_from_file(file_path, chunk_size=4096):
    """
    Calculates the Adler-32 checksum of a file.

    Args:
        filepath (str): The path to the file.
        chunk_size (int): The size of chunks to read from the file.

    Returns:
        int: The Adler-32 checksum of the file.
    """
    adler32_checksum = 1  # Initial Adler-32 value

    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                adler32_checksum = zlib.adler32(chunk, adler32_checksum)
        return adler32_checksum & 0xffffffff  # Ensure 32-bit unsigned result
    except:
        print(f"Problem with file {file_path}")
        exit(-2)


# ---
def get_file_size(file_path):
    """
    Returns the size of the file at the given path in bytes.
    
    Args:
        file_path (str): The path to the file.
    
    Returns:
        int: The size of the file in bytes, or None if the file does not exist.
    """

    file_size_bytes = 0
    try:
        file_size_bytes = os.path.getsize(file_path)
    except:
        print(f"Error: problem with file '{file_path}'.")
        exit(-2)

    return file_size_bytes
# ---



# ---
def current_time():
    '''
    Returns the current time in a specific format to generate run id.
    Note that in this case we do not need the microseconds at the current stage of development.
    '''
    return dt.now().strftime("%Y%m%d%H%M%S")


###################################################################################
class Monitor(): # possibly to be implemented later
    ''' The Monitor class is used to record the time series of the parameters of choice,
        as the simulation is progressing through time steps.
        NB. Work in progress, to be implemented yet.
    '''

    def __init__(self, size=0):
        '''
        Initialize arrays for time series type of data
        '''

        self.buffer = np.zeros(size, dtype=float) # Current data volume in the buffer

###################################################################################
class DAQ:
    ''' The DAQ class is the main simulation class, which reads the schedule from a YAML file,
        simulates the data acquisition process, and generates simulated Super Time Frame data (STFs)
        at random intervals within the specified limits optionally writing them to filea
        and/or sending a message to a message queue (MQ) for further processing.
        The class uses SimPy for event simulation and can be configured to run in real-time or accelerated time.
    
        Note that the sended is initialized externally, so that the DAQ can send messages to a message queue (MQ) if needed.  
    '''
    def __init__(self,
                 schedule_f=None,
                 destination=None,
                 until=None,
                 clock=1.0,
                 factor=1.0,
                 low=1.0,
                 high=2.0,
                 sender=None,
                 receiver=None,
                 verbose=False,
                 test=False):
        
        self.state      = None          # current state of the DAQ, undergoes changes in time
        self.substate   = None          # current substate of the DAQ, undergoes changes in time
        self.schedule_f = schedule_f    # filename, of the YAML definition of the schefule
        self.destination= destination   # container folder for the output data folders, if empty do not write
        self.folder     = ''            # the actual folder for the current run, to be created later
        self.schedule   = None          # the actual schedule (a dictionary), to be filled later
        self.index      = 0             # current index into the schedule (currently a list of points)
        self.verbose    = verbose       #
        self.until      = until         # total duration of the sim
        self.clock      = clock         # scheduler clock
        self.factor     = factor        # real-time scaling factor
        self.low        = low           # low limit on the STF prod time
        self.high       = high          # high limit on same
        self.points     = []            # state switch points
        self.end        = 0.0           # will be updated -- the last of the points
        self.Nstf       = 0             # counter of the generated STFs
        self.sender     = sender        # the MQ sender, if any
        self.receiver   = receiver      # the MQ receiver, if any
        self.env        = None          # the SimPy environment, to be created later
        self.run_id     = ''            # to be filled later, the run name/number etc
        self.dataset    = ''            # to be filled later, based on the run number
        self.filename   = ''            # the current STF filename, to be generated later
        self.run_start_ts = None        # the start time of the run, as a timestamp
        self.run_start  = ''            # the start time of the run, to be used in the metadata
        self.run_stop   = ''            # the stop time of the run, to be used in the metadata
        self.test       = test          # test mode, if True get run number randomly, if False use API (not implemented yet)

        self.agent_name = 'daq-simulator'
        self.agent_type = 'daqsim'

        if not self.test:
            self.monitor_url    = os.getenv('SWF_MONITOR_URL', 'https://pandaserver02.sdcc.bnl.gov/swf-monitor')
            self.api_token      = os.getenv('SWF_API_TOKEN')
            if self.verbose:
                print(f'''*** The SWF_MONITOR_URL is set to {self.monitor_url} ***''')
                print(f'''*** The access token is set to {self.api_token} ***''')
            self.api_session = requests.Session()
            
            if self.api_token:
                self.api_session.headers.update({'Authorization': f'Token {self.api_token}'})

            self.api_session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Send initial registration/heartbeat
            self.send_heartbeat()        
        
        self.read_schedule()            # read the schedule from the YAML file

    # ---
    def read_schedule(self):
        try:
            f = open(self.schedule_f, 'r') # to read YAML from
        except:
            print(f'''Error opening the schedule file {self.schedule_f}, exiting...''')
            exit(-1)

        self.schedule = yaml.safe_load(f)
        
        current = 0.0 # the time origin: start populating the array of scheduling points
        self.points.append(current)

        for point in self.schedule: # span example: 0,0,0,1,0 - weeks, days, hours, minutes, seconds
            x = [int(p) for p in point['span'].split(',')] # parse the span into a list of integers
            if len(x) != 5:
                print(f'''Error in the schedule file {self.schedule_f}, span must be a comma-separated list of 5 integers, got {point['span']}''')
                exit(-1)
            
            # Create a timedelta object from the parsed span and convert it to seconds to update the current time
            # e.g. 0,0,0,1,0 -> 60 seconds
            
            interval = datetime.timedelta(weeks=x[0], days=x[1], hours=x[2], minutes=x[3], seconds=x[4])
            if self.verbose: print(f'''*** {point['state']}, {interval.total_seconds()}s ***''')
            current+=interval.total_seconds()
            self.points.append(current)

        self.state      = self.schedule[0]['state']
        self.substate   = self.schedule[0]['substate']
        self.end        = self.points[-1]

        if self.verbose:        print(f'''*** The end of the defined schedule is at {self.end}s ***''')
        if self.until is None:
            if self.verbose:    print(f'''*** Will stop simulation at the end of schedle defined in {self.schedule_f} ***''')
            self.until = self.end
        else:
            if self.verbose:    print(f'''*** Will run simulation until {self.until}s per command line options***''')

    # ---
    def get_simpy_time(self):
        """Get the current simulation time, according to the SimPy environment, formatted"""
        return f"{self.env.now:.1f}s"

    # ---
    # Keep for reference - we now moved to a different filename template, as seen below
    # The filename template: swf.20250625.<integer>.<state>.<substateate>.stf
    # filename = f'''swf.{formatted_date}.{formatted_time}.{formatted_us}.{self.state}.{self.substate}.stf'''
    # Keep for reference, dataset --- f'run_{str(self.run_id)}_swf' -- old version

    # ---
    def define_filename(self):
        self.filename = f'''swf.{self.run_id:06d}.{self.Nstf:06d}.stf'''

    # ---
    def define_dataset(self):
        self.dataset = f'''swf.{self.run_id:06d}.run'''  # Dataset name based on the run number
    # ---
    
    def metadata(self, start, end):
        md ={
                'run_id':       self.run_id,
                'state':        self.state,
                'substate':     self.substate,
                'filename':     self.filename,
                'start':        start.strftime(timeformat),
                'end':          end.strftime(timeformat)
            }
        return md



    # ---
    def mq_run_imminent_message(self):
        '''
        Create a message to be sent to MQ saying that the start is imminent.
        '''
        
        msg = {}
        
        msg['msg_type']     = 'run_imminent'
        msg['req_id']       = 1
        msg['run_id']       = self.run_id
        msg['timestamp']    = self.run_start_ts
        msg['dataset']      = self.dataset

        msg['run_conditions'] = {
                "beam_energy": "5 GeV",
                "magnetic_field": "1.5T",
                "detector_config": "physics",
                "bunch_structure": "216x216"
            }        
        return json.dumps(msg)


    # ---
    def mq_start_run_message(self):
        '''
        Create a message to be sent to MQ about the start of the run.
        This part will evolve as the development progresses, but for now it is a simple JSON message.
        '''
        msg = {}
        
        msg['msg_type']     = 'start_run'
        msg['req_id']       = 1
        msg['run_id']       = self.run_id
        msg['ts']           = self.run_start_ts
        
        return json.dumps(msg)
 
    # ---
    def mq_end_run_message(self):
        '''
        Create a message to be sent to MQ about the stop of the run.
        This part will evolve as the development progresses, but for now it is a simple JSON message.
        '''
        msg = {}
        ts = current_time()
        self.run_end        = ts
        msg['msg_type']     = 'end_run'
        msg['req_id']       = 1
        msg['run_id']       = self.run_id
        msg['ts']           = self.run_end
        
        return json.dumps(msg)
    
    # ---
    def mq_stf_message(self, md):
        '''
        Create a message to be sent to MQ about the STF creation.
        This part will evolve as the development progresses, but for now it is a simple JSON message.
        '''
        md['msg_type']  = 'stf_gen'
        md['req_id']    = 1
        return json.dumps(md)

    # ---
    def get_run_number(self):
        '''
        Get the next run number from the run monitor.
        This is a placeholder for now, to be implemented later.
        '''
        next_run_number = None
        
        #
        # We ask the monitor to provide the next run number, or if needed generate a random one for testing.
        # In the past, we used self.run_start_ts but the size of the integer quickly becomes a problem
        # Could also use uuid.uuid1(), but for now this is not optimal.
        #
        if self.test:
            next_run_number = random.randint(1, 1000)
        else:
            try:
                url = f"{self.monitor_url}/api/state/next-run-number/"
                response = self.api_session.post(url, timeout=10)
                response.raise_for_status()
            except Exception as e:                
                raise RuntimeError(f"Critical failure getting run number: {e}") from e
            data = response.json()
            if 'run_number' in data:
                next_run_number = data['run_number']
            else:
                raise RuntimeError(f"Critical failure getting run number, no run_number in response: {data}")

        return next_run_number
    
    # ---
    def send_heartbeat(self, status="OK"):
        '''
        Send a heartbeat message to the run monitor.
        '''
        
        if self.test: return
        
        try:
            payload = {
                "instance_name":    self.agent_name,
                "agent_type":       self.agent_type,
                "status":           status,
                "description":      f"DAQSIMULATOR agent {self.agent_name} is running",
                "workflow_enabled": False  # Enable this agent for workflow tracking
            }

            print(f"[HEARTBEAT] Sending heartbeat for {self.agent_name} to {self.monitor_url}/api/systemagents/heartbeat/")
            print(f"[HEARTBEAT] Payload: {payload}")
            
            url = f"{self.monitor_url}/api/systemagents/heartbeat/"
            response = self.api_session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            print(f"[HEARTBEAT] SUCCESS: Status {response.status_code}")
        except Exception as e:
            print(f"Warning: failure sending heartbeat: {e}")
            return
        
        data = response.json()
        if 'status' in data and data['status'] == 'ok':
            if self.verbose:
                print(f"Heartbeat sent successfully for run {self.run_id}")
        else:
            print(f"Warning: unexpected response from heartbeat: {data}")
            return
    
    
    ############################ For completeness ##############################
    # ---
    def __str__(self):
        return f'''DAQ Simulation: state={self.state}, substate={self.substate}, until={self.until}, clock={self.clock}, factor={self.factor}, low={self.low}, high={self.high}'''

    # ---
    def __repr__(self):
        return self.__str__()
    
    
    ############################################################################
    ########################### Core Simulation code ###########################
    ############################################################################
    # ---
    
    def start_run(self):
        '''
        Start the simulation run, create the SimPy environment and register the processes.
        This method is called to initialize the simulation environment and start the processes.

        The "run imminent" message is sent here, before the actual start of the run.
        The "start run" message is sent after that.

        NB. Folder for the run is created here, if destination is specified.
        NB. Dataset name is generated here, based on the run number.
        '''
        if self.verbose: print(f'''*** Starting the DAQ simulation run ***''')

        self.run_start_ts   = current_time()
        
        self.run_id = self.get_run_number()
        self.define_dataset() # define the dataset name ('dataset' attribute) based on the run number
        
        if self.destination: # Create the folder for the run, if it does not exist
            self.folder = f"{self.destination}/{self.dataset}"
            try:
                os.makedirs(self.folder, exist_ok=True)
            except:
                if self.verbose:
                    print(f"*** Error: could not create the output folder {self.folder}, exiting... ***")
                exit(-1)
            
            if self.verbose: print(f'''*** Created the output folder {self.folder} ***''')
        

        if self.sender:
            self.sender.send(destination='epictopic', body=self.mq_run_imminent_message(), headers={'persistent': 'true'})
            if self.verbose: print(f'''*** Sent MQ message that run {str(self.run_id)} is imminent ***''')

        
        # Create a real-time environment with the specified factor
        self.env = simpy.rt.RealtimeEnvironment(factor=self.factor, strict=False)
        
        # Register the schedule minder and the STF generator processes with the environment
        self.env.process(self.sched())          # the schedule minder
        self.env.process(self.stf_generator())  # the DAQ payload to process in each step
        
        if self.sender:
            self.sender.send(destination='epictopic', body=self.mq_start_run_message(), headers={'persistent': 'true'})
            if self.verbose: print(f'''*** Sent MQ message for start of run {str(self.run_id)} ***''')
    
        if not self.test:
            # Send heartbeat
            self.send_heartbeat()
    
    def end_run(self):
        '''
        End the simulation run, clean up resources and print the summary.
        This method is called to finalize the simulation and print the results.
        '''
        if self.sender:
            self.sender.send(destination='epictopic', body=self.mq_end_run_message(), headers={'persistent': 'true'})
            if self.verbose: print(f'''*** Sent MQ message for end of run {str(self.run_id)} ***''')
    
        if self.verbose:
            print(f'''*** Ending the DAQ simulation run ***''')
            print(f'''*** Total number of STFs generated: {self.Nstf} ***''')
  
        if not self.test:
            # Send heartbeat
            self.send_heartbeat()
    
    def run(self):
        self.start_run()  # Initialize the simulation environment and processes
        
        try:
            self.env.run(until=self.until)
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
            
        self.end_run()  # Finalize the simulation and print the results

    # ---
    def sched(self): # keeps track of the state changes as defined in the schedule
        while True:
            myT     = int(self.env.now)
            index = bisect.bisect_right(self.points, myT) - 1 # Find the index of the current schedule entry
            if index!=self.index:
                if index<len(self.schedule): # state/substateate transition
                    self.index=index
                    self.state=self.schedule[index]['state']
                    self.substate=self.schedule[index]['substate']
                else:
                    pass # past the last point, just keep rolling in the same state
            
            yield self.env.timeout(self.clock)
    
    # ---
    def stf_generator(self):
        '''
        - Generate STFs at random intervals.
        - Notify the downstream agents via MQ and/or write to file, with the path specified in the destination.
        - The STF filename is generated based on the current date, time, state, and substate.
        - The filename template: swf.20250625.<integer>.<state>.<substate>.stf

        The metadata is also generated and is used to sent to a message queue and/or written to a file.
        Currently it contains the following fields:
        - filename: the name of the STF file
        - start: the start time of the STF in YYYYMMDDHHMMSSffffff format
        - end: the end time of the STF in YYYYMMDDHHMMSSffffff format
        - state: the current state of the DAQ
        - substate: the current substate of the DAQ

        The last two fields are only present in the MQ messages, the preceding ones are written to the file.

        The STF generation is controlled by the low and high limits for the arrival time of the STF.
        It is done in real-time, with the time axis controlled by the SimPy environment.

        '''

        if self.verbose: print(f'''*** Starting the STF generator process ***''')
        # If the destination is not specified, do not write to file, and only send messages to MQ
        # If not writing files, these values will be placeholders in the MQ messages
        adler = 0
        size  = 0

        while True:
            self.define_filename() # define the filename for the current STF

            build_start = dt.now() # .strftime("%Y%m%d%H%M%S")
            stf_arrival = random.uniform(self.low, self.high)   # Time for next STF (random interval between the low/high limits)
            interval    = datetime.timedelta(seconds=stf_arrival)
            build_end   = build_start+interval

            md = self.metadata(build_start, build_end)

            # This is provisionl until we have a real STF file to write
            # For now, we just create a JSON message with the metadata
            # and send it to the message queue, if the sender is initialized
            data = json.dumps(md)
            
            if self.destination:
                dfilename = f"{self.folder}/{self.filename}"
                # Here we would write the STF to the file, and send a notification to a message queue
                with open(dfilename, 'w') as f:
                    f.write(data)
                    f.close()
                adler = calculate_adler32_from_file(dfilename) # Calculate the Adler-32 checksum of the file
                size  = get_file_size(dfilename)               # Get the size of the file in bytes
                if self.verbose: print(f'''*** Wrote STF to file {dfilename}, Adler-32 checksum: {adler}, size: {size} ***''')

            # Augment the metadata with the checksum and size, to be sent to MQ
            # The reason we are doing it here is that we need to have the file written
            # before we can calculate the checksum and size
            
            md['checksum']  = f'''ad:{str(adler)}'''  # Adler-32 checksum
            md['size']      = size
        
            if self.sender:
                self.sender.send(destination='epictopic', body=self.mq_stf_message(md), headers={'persistent': 'true'})
                if self.verbose: print(f'''*** Sent MQ message for STF {self.filename} ***''')

            self.Nstf+=1
            yield self.env.timeout(stf_arrival)



##################################################################################
# --- ATTIC ---
# Some code snippets kept here for reference, to be possibly used later
# SimPy:
# self.env.process(self.run()) # Set the callback to this class, for simpy        self.env.run(until=self.until)

# ts_now = datetime.datetime.now().timestamp()
# dt = datetime.now()
# seconds_since_epoch = dt.timestamp()
# print(int(seconds_since_epoch))

# self.sender.send(destination='epictopic', body=json.dumps(md), headers={'persistent': 'true'})

# formatted_date = build_end.strftime("%Y%m%d")             # ("%Y-%m-%d %H:%M:%S")
# formatted_time = build_end.strftime("%H%M%S")
# formatted_us   = build_end.strftime("%f")