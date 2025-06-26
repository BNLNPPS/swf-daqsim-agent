#! /usr/bin/env python
#############################################

import os
import sys
from   sys import exit
import argparse
import datetime

##############################################
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose",  action='store_true',    help="Verbose mode")
parser.add_argument("-s", "--schedule", type=str,               help='Path to the schedule (YAML)', default='')

parser.add_argument("-f", "--factor",   type=float,             help='Time factor',                 default=1.0)
parser.add_argument("-u", "--until",    type=float,             help='The "until" time limit, if undefined will run till end of schedule', required=False, nargs='?')
parser.add_argument("-c", "--clock",    type=float,             help='Schedular clock (granularity in seconds)', default=1.0)

parser.add_argument("-L", "--low",      type=float,             help='The "low" time limit on STF production',  default=1.0)
parser.add_argument("-H", "--high",     type=float,             help='The "high" time limit on STF production', default=2.0)

args        = parser.parse_args()
verbose     = args.verbose
schedule    = args.schedule
factor      = args.factor
until       = args.until
clock       = args.clock

low         = args.low
high        = args.high

# ---
daqsim_path=''
try:
    daqsim_path=os.environ['DAQSIM_PATH']
    if verbose: print(f'''*** The DAQSIM_PATH is defined in the environment: {daqsim_path}, will be added to sys.path ***''')
    sys.path.append(daqsim_path)
except:
    if verbose: print('*** The variable DAQSIM_PATH is undefined, will rely on PYTHONPATH and ../ ***')
    daqsim_path = '../'
    sys.path.append(daqsim_path)  # Add parent to path, to enable running locally (also for data)

if verbose:         print(f'''*** Set the Python path: {sys.path} ***''')
if schedule=='':    schedule    = daqsim_path + "config/schedule-rt.yml"
if verbose:
    print(f'''*** Schedule description file path: {schedule} ***''')
    print(f'''*** Simulation time factor: {factor} ***''')

# ---
# Python path is set, import the sim package:
from  sim import *

daq = DAQ(schedule_f = schedule, until = until, clock = clock, factor = factor, low = low, high = high, verbose = verbose)
daq.simulate()

print('---')
if verbose: print(f'''*** Completed at {daq.get_time()}. Number of STFs generated: {daq.Nstf} ***''')


