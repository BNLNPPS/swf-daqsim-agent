# foundation packages
import numpy as np
import simpy, yaml
import random
import datetime

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
    def __init__(self, schedule_f=None, until=60.0, factor=1.0, low=1.0, high=2.0, verbose=False):
        self.schedule_f = schedule_f
        self.verbose    = verbose
        self.until      = until
        self.factor     = factor
        self.low        = low
        self.high       = high
        self.points     = {}

        self.read_schedule()        #self.time_axis = None

    # ---
    def read_schedule(self):
        try:
            f = open(self.schedule_f, 'r') # to read YAML from
        except:
            print(f'''Error opening the schedule file {self.schedule_f}, exiting...''')
            exit(-1)

        self.schedule = yaml.safe_load(f)

        ts_now = datetime.datetime.now().timestamp()

        for point in self.schedule:
            # Example - duration: 0,0,0,1,0 # weeks, days, hours, minutes, seconds
            x = [int(p) for p in point['duration'].split(',')]
            print(x)

            interval = datetime.timedelta(weeks=x[0], days=x[1], hours=x[2], minutes=x[3], seconds=x[4])
            print(interval.total_seconds())


    # ---
    def get_time(self):
        """Get current simulation time formatted"""
        return f"{self.env.now:.1f}s"

    # self.env.run(until=self.until)

    ############################################################################
    ############################## Simulation code #############################
    # ---
    def run(self):
        while True:
            myT     = int(self.env.now)
            print(myT)
            yield self.env.timeout(1)
    
    # ---
    def simulate(self):
        # Create real-time environment (e.g. factor=0.1 means 10x speed, etc)
        self.env = simpy.rt.RealtimeEnvironment(factor=self.factor, strict=False)
        self.env.process(self.stf_generator()) # what callback to process in each step
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
            print(self.get_time())
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