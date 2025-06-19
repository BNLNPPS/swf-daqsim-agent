# foundation packages
import numpy as np
import simpy
import yaml


# We'll use datetime to handle the time axis
# from datetime import datetime
# dt = datetime.strptime("2023-12-25 14:30:00", "%Y-%m-%d %H:%M:%S")

###########

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

    def read_schedule(self):
        try:
            f = open(self.schedule_f, 'r')
        except:
            print(f'''Error opening the schedule file {self.schedule_f}, exiting...''')
            exit(0)

        self.schedule = yaml.safe_load(f)
        print(type(self.schedule))

