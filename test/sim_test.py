#! /usr/bin/env python
#######################################################################
# The script for the unit test of the simulator
#######################################################################

import os
import sys
from   sys import exit
import argparse
import datetime

##############################################
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose",  action='store_true',    help="Verbose mode")
parser.add_argument("-s", "--schedule", type=str,               help='Path to the schedule (YAML)', default='')

args        = parser.parse_args()
verbose     = args.verbose
schedule    = args.schedule

# ---
daqsim_path=''
try:
    daqsim_path=os.environ['DAQSIM_PATH']
    if verbose: print(f'''The DAQSIM_PATH is defined in the environment: {daqsim_path}, will be added to sys.path''')
    sys.path.append(daqsim_path)
except:
    if verbose: print('The variable DAQSIM_PATH is undefined, will rely on PYTHONPATH and ../')
    daqsim_path = '../'
    sys.path.append(daqsim_path)  # Add parent to path, to enable running locally (also for data)

if verbose:         print(f'''Set the Python path: {sys.path}''')
if schedule=='':    schedule    = daqsim_path + "config/schedule-rt.yml"
if verbose:         print(f'''Schedule description file path: {schedule}''')

# ---
from   sim import *

smltr = Simulator(schedule_f = schedule, verbose=verbose)
# smltr.simulate()
print('---')
# print(smltr.schedule)
# print(smltr.until)
# dt = datetime.now()
# seconds_since_epoch = dt.timestamp()
# print(int(seconds_since_epoch))

