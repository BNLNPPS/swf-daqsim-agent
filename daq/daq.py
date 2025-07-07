# foundation packages
import numpy as np
import simpy, yaml
import random
import datetime
import bisect
import json
from   datetime import datetime as dt
# from   .comms import Messenger   

###################################################################################
class Monitor():
    ''' The Monitor class is used to record the time series of the parameters of choice,
        as the simulation is progressing through time steps.
    '''

    def __init__(self, size=0):
        '''
        Initialize arrays for time series type of data
        '''

        self.buffer = np.zeros(size, dtype=float) # Current data volume in the buffer

###################################################################################
class DAQ:
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
        self.subst      = None          # current substate of the DAQ, undergoes changes in time
        self.schedule_f = schedule_f    # filename, of the YAML definition of the schefule
        self.destination= destination   # folder for the output data, if empty do not write
        self.schedule   = None          # the actual schedule (a dictionary), to be filled later
        self.index      = 0             # current index into the schedule
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

        self.read_schedule()

    # ---
    def read_schedule(self):
        try:
            f = open(self.schedule_f, 'r') # to read YAML from
        except:
            print(f'''Error opening the schedule file {self.schedule_f}, exiting...''')
            exit(-1)

        self.schedule = yaml.safe_load(f)
        
        current = 0.0 # the origin: start populating the array of scheduling points
        self.points.append(current)

        for point in self.schedule: # span example: 0,0,0,1,0 - weeks, days, hours, minutes, seconds
            x = [int(p) for p in point['span'].split(',')]
            interval = datetime.timedelta(weeks=x[0], days=x[1], hours=x[2], minutes=x[3], seconds=x[4])
            if self.verbose: print(f'''*** {point['state']}, {interval.total_seconds()}s ***''')
            current+=interval.total_seconds()
            self.points.append(current)

        self.state = self.schedule[0]['state']
        self.subst = self.schedule[0]['subst']
        self.end   = self.points[-1]

        if self.verbose: print(f'''*** The end of the defined schedule is at {self.end}s ***''')
        if self.until is None:
            if self.verbose: print(f'''*** Will stop simulation at the end of schedle defined in {self.schedule_f} ***''')
            self.until = self.end
        else:
            if self.verbose: print(f'''*** Will run simulation until {self.until}s per command line options***''')

    # ---
    def get_time(self):
        """Get current simulation time formatted"""
        return f"{self.env.now:.1f}s"


    # ---
    def metadata(self, filename, start, end):
        md ={
                'filename': filename,
                'start':    start.strftime("%Y%m%d%H%M%S"),
                'end':      end.strftime("%Y%m%d%H%M%S"),
                'state':    self.state,
                'subst':    self.subst
            }
        return md

    
    ############################################################################
    ########################### Core Simulation code ###########################
    # ---
    def simulate(self):
        # Create real-time environment (e.g. factor=0.1 means 10x speed, etc)
        self.env = simpy.rt.RealtimeEnvironment(factor=self.factor, strict=False)
        self.env.process(self.sched()) # the schedule minder
        self.env.process(self.stf_generator()) # the DAQ payload to process in each step
        try:
            self.env.run(until=self.until)
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")

    # ---
    def sched(self): # keeps track of the state changes as defined in the schedule
        while True:
            myT     = int(self.env.now)
            index = bisect.bisect_right(self.points, myT) - 1 # Find the index of the current schedule entry
            if index!=self.index:
                if index<len(self.schedule): # state/substate transition
                    self.index=index
                    self.state=self.schedule[index]['state']
                    self.subst=self.schedule[index]['subst']
                else:
                    pass # past the last point, just keep rolling

            # if self.verbose: print(f'''*** Time: {myT}, index: {index}, state: {self.state}, substate: {self.subst} ''')

            yield self.env.timeout(self.clock)
    
    # ---
    # 
    # Data is generated here:
    # a) generate
    # b) send a message to inform various gents downstream
    #
    def stf_generator(self):
        '''
        Generate STFs arriving at random intervals
        '''
        while True:

            build_start = dt.now() # .strftime("%Y%m%d%H%M%S")
            stf_arrival = random.uniform(self.low, self.high)   # Time for next STF (random interval between the low/high limits)
            interval    = datetime.timedelta(seconds=stf_arrival)
            build_end   = build_start+interval

            formatted_date = build_end.strftime("%Y%m%d")             # ("%Y-%m-%d %H:%M:%S")
            formatted_time = build_end.strftime("%H%M%S")

            # The filename template: swf.20250625.<integer>.<state>.<substate>.stf
            filename = f'''swf.{formatted_date}.{formatted_time}.{self.state}.{self.subst}.stf'''

            md = self.metadata(filename, build_start, build_end)

            if self.destination:
                dfilename = f"{self.destination}/{filename}"
                # Here we would write the STF to the file, and send a notification to a message queue
                with open(dfilename, 'w') as f:
                    f.write(json.dumps(md))
                    f.close()
            if self.sender:
                self.sender.send(body=json.dumps(md))
                # self.sender.send(destination='epictopic', body=json.dumps(md), headers={'persistent': 'true'})
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