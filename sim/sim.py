# foundation packages
import numpy as np
import simpy, yaml
import random
import datetime
import bisect

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
    def __init__(self, schedule_f=None, until=60.0, clock=1.0, factor=1.0, low=1.0, high=2.0, verbose=False):
        self.schedule_f = schedule_f    # filename
        self.schedule   = None          # the actual schefule dict, to be filled later
        self.verbose    = verbose
        self.until      = until         # total duration of the sim
        self.clock      = clock         # scheduler clock
        self.factor     = factor        # real-time scaling factor
        self.low        = low           # low limit on the STF prod time
        self.high       = high          # high limit on same
        self.points     = []            # state switch points

        self.read_schedule()

    # ---
    def read_schedule(self):
        try:
            f = open(self.schedule_f, 'r') # to read YAML from
        except:
            print(f'''Error opening the schedule file {self.schedule_f}, exiting...''')
            exit(-1)

        self.schedule = yaml.safe_load(f)

        # Start populating the array of scheduling points:
        self.points.append(0.0)
        current = 0.0
        for point in self.schedule:
            # Example - duration: 0,0,0,1,0 # weeks, days, hours, minutes, seconds
            x = [int(p) for p in point['duration'].split(',')]
            interval = datetime.timedelta(weeks=x[0], days=x[1], hours=x[2], minutes=x[3], seconds=x[4])
            if self.verbose: print(point['mode'], interval.total_seconds())
            current+=interval.total_seconds()
            self.points.append(current)

        print(self.points)
    # ---
    def get_time(self):
        """Get current simulation time formatted"""
        return f"{self.env.now:.1f}s"

    ############################################################################
    ############################## Simulation code #############################
    # ---
    def sched(self): # keeps track of the state as defined in the schedule
        while True:
            myT     = int(self.env.now)
    
            # Find the index
            index = bisect.bisect_right(self.points, myT)
            print('sched', myT, index)
            yield self.env.timeout(self.clock)
    
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
    # Data is generated here:
    # a) generate
    # b) send a message to inform various gents downstream
    #
    def stf_generator(self):
        '''
        Generate STFs arriving at random intervals
        '''
        while True:
      
            # Wait for next STF (random interval between the low and high limits)
            next_arrival = random.uniform(self.low, self.high)
            # print(self.get_time())
            yield self.env.timeout(next_arrival)



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