# foundation packages
import numpy as np
import simpy, yaml
import random
import datetime
import bisect
import json
from   datetime import datetime as dt

# ---
def current_time():
    ''' Returns the current time in a specific format for use in filenames and metadata. '''
    return dt.now().strftime("%Y%m%d%H%M%S%f")


###################################################################################
class Monitor():
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
        The class uses SimPy for event simulation and can be configured to run in real-time or accelerated time.'''
    def __init__(self,
                 schedule_f=None,
                 destination='',
                 until=None,
                 clock=1.0,
                 factor=1.0,
                 low=1.0,
                 high=2.0,
                 verbose=False,
                 sender=None):
        self.state      = None          # current state of the DAQ, undergoes changes in time
        self.substate   = None          # current substate of the DAQ, undergoes changes in time
        self.schedule_f = schedule_f    # filename, of the YAML definition of the schefule
        self.destination= destination   # folder for the output data, if empty do not write
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
        self.run_id     = ''            # to be filled later, the run name/number etc
        self.run_start  = ''            # the start time of the run, to be used in the metadata
        self.run_stop   = ''            # the stop time of the run, to be used in the metadata

        self.read_schedule()

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
    def metadata(self, filename, start, end):
        md ={
                'filename':     filename,
                'start':        start.strftime("%Y%m%d%H%M%S"),
                'end':          end.strftime("%Y%m%d%H%M%S"),
                'state':        self.state,
                'substate':     self.substate
            }
        return md

    # ---
    def mq_run_start_message(self):
        '''
        Create a message to be sent to MQ about the start of the run.
        This part will evolve as the development progresses, but for now it is a simple JSON message.
        '''
        msg = {}
        ts = current_time()
        self.run_id         = ts # Generate a unique run ID based on the current date and time
        self.run_start      = ts
        msg['msg_type']     = 'start_run'
        msg['req_id']       = 1
        msg['run_id']       = self.run_id
        msg['run_start']    = self.run_start
        
        return json.dumps(msg)
 
    # ---
    def mq_run_stop_message(self):
        '''
        Create a message to be sent to MQ about the stop of the run.
        This part will evolve as the development progresses, but for now it is a simple JSON message.
        '''
        msg = {}
        ts = current_time()
        self.run_stop      = ts
        msg['msg_type']    = 'stop_run'
        msg['req_id']      = 1
        msg['run_id']      = self.run_id
        msg['run_stop']    = self.run_stop
        
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
        '''
        if self.verbose: print(f'''*** Starting the DAQ simulation run ***''')
        
        # Create a real-time environment with the specified factor
        self.env = simpy.rt.RealtimeEnvironment(factor=self.factor, strict=False)
        
        # Register the schedule minder and the STF generator processes with the environment
        self.env.process(self.sched())          # the schedule minder
        self.env.process(self.stf_generator())  # the DAQ payload to process in each step
        
        print('---------------------------------------', self.mq_run_start_message())  # Print the start time
    
    def end_run(self):
        '''
        End the simulation run, clean up resources and print the summary.
        This method is called to finalize the simulation and print the results.
        '''
        print('---------------------------------------', self.mq_run_stop_message())  # Print the stop time
        if self.verbose:
            print(f'''*** Ending the DAQ simulation run ***''')
            print(f'''*** Total number of STFs generated: {self.Nstf} ***''')
  
    
    
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
        - start: the start time of the STF in YYYYMMDDHHMMSS format
        - end: the end time of the STF in YYYYMMDDHHMMSS format
        - state: the current state of the DAQ
        - substate: the current substate of the DAQ

        The last two fields are only present in the MQ messages, the preceding ones are written to the file.

        The STF generation is controlled by the low and high limits for the arrival time of the STF.
        It is done in real-time, with the time axis controlled by the SimPy environment.

        '''
        while True:

            build_start = dt.now() # .strftime("%Y%m%d%H%M%S")
            stf_arrival = random.uniform(self.low, self.high)   # Time for next STF (random interval between the low/high limits)
            interval    = datetime.timedelta(seconds=stf_arrival)
            build_end   = build_start+interval

            formatted_date = build_end.strftime("%Y%m%d")             # ("%Y-%m-%d %H:%M:%S")
            formatted_time = build_end.strftime("%H%M%S")

            # The filename template: swf.20250625.<integer>.<state>.<substateate>.stf
            filename = f'''swf.{formatted_date}.{formatted_time}.{self.state}.{self.substate}.stf'''

            md = self.metadata(filename, build_start, build_end)

            if self.destination:
                dfilename = f"{self.destination}/{filename}"
                # Here we would write the STF to the file, and send a notification to a message queue
                with open(dfilename, 'w') as f:
                    f.write(json.dumps(md))
                    f.close()
            if self.sender:
                self.sender.send(destination='epictopic', body=self.mq_stf_message(md), headers={'persistent': 'true'})
                if self.verbose: print(f'''*** Sent MQ message for STF {filename} ***''')
            self.Nstf+=1
            yield self.env.timeout(stf_arrival)



##################################################################################
# --- ATTIC ---
# import datetime
# from   datetime import datetime
# d8P7%d5S

# We'll use datetime to handle the time axis
# from datetime import datetime
# dt = datetime.strptime("2023-12-25 14:30:00", "%Y-%m-%d %H:%M:%S")

###########
# dt_fmt = '%Y-%m-%d %H:%M:%S'
        # points = list(self.schedule.keys())
        # if self.verbose: print(f'''The schedule read from file {self.schedule_f} contains {len(points)} points''')

        # for point in points:
        #     self.schedule[point]['ts'] = int(datetime.strptime(self.schedule[point]['start'], dt_fmt).timestamp())

        # first   = self.schedule[points[0]]
        # last    = self.schedule[points[-1]]

        # self.initial_time   = int(datetime.strptime(first['start'], dt_fmt).timestamp())
        # self.until          = int(datetime.strptime(last['start'],  dt_fmt).timestamp())

# SimPy:
# self.env.process(self.run()) # Set the callback to this class, for simpy        self.env.run(until=self.until)

# ts_now = datetime.datetime.now().timestamp()
# if self.verbose : print(f'''*** Initializing at {ts_now} ***''')

# Timestamp, if needed
# print(smltr.schedule)
# print(smltr.until)
# dt = datetime.now()
# seconds_since_epoch = dt.timestamp()
# print(int(seconds_since_epoch))

# self.sender.send(destination='epictopic', body=json.dumps(md), headers={'persistent': 'true'})