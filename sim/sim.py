# foundation packages
import numpy as np
import simpy
import yaml

###########

class Monitor():
    ''' The Monitor class is used to record the time series of the parameters of choice,
        as the simulation is progressing through time steps.
    '''

    def __init__(self, size=0):
        ''' Initialize arrays for time series type of data
        '''

        self.buffer = np.zeros(size, dtype=float) # Current data volume in the buffer
