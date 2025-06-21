# foundation packages
import numpy as np
import simpy
import yaml
import datetime

from   datetime import datetime

# We'll use datetime to handle the time axis
# from datetime import datetime
# dt = datetime.strptime("2023-12-25 14:30:00", "%Y-%m-%d %H:%M:%S")

###########
dt_fmt = '%Y-%m-%d %H:%M:%S'

# ---
class Monitor():
    ''' The Monitor class is used to record the time series of the parameters of choice,
        as the simulation is progressing through time steps.
    '''

    def __init__(self, size=0):
        ''' Initialize arrays for time series type of data
        '''

        self.buffer = np.zeros(size, dtype=float) # Current data volume in the buffer

# ---
class Simulator:
    def __init__(self, schedule_f=None, verbose=False):
        self.schedule_f = schedule_f
        self.schedule   = None
        self.read_schedule()

        self.env = simpy.Environment(initial_time=self.initial_time)
        self.env.process(self.run()) # Set the callback to this class, for simpy

    def read_schedule(self):
        try:
            f = open(self.schedule_f, 'r')
        except:
            print(f'''Error opening the schedule file {self.schedule_f}, exiting...''')
            exit(-1)

        self.schedule = yaml.safe_load(f)
        entries = list(self.schedule.keys())

        first   = self.schedule[entries[0]]
        last    = self.schedule[entries[-1]]

        self.initial_time   = int(datetime.strptime(first['start'], dt_fmt).timestamp())
        self.until          = int(datetime.strptime(last['start'],  dt_fmt).timestamp())



# self.env.run(until=self.until)

    ############################## Simulation code #############################
    # ---
    def simulate(self):
        """ Steeting of the SimPy simulation process, relying on
            the 'run' method previous set in the SimPy environment"""
     
        self.env.run(until=self.until)

    def run(self):
        while True:
            myT     = int(self.env.now)
            print(myT)
            yield self.env.timeout(1)