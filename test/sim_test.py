#! /usr/bin/env python

#############################################

import os, argparse, datetime, sys
from   sys import exit

# ---

def func(to_print):
    print(to_print) # a simple function to process received messages
# ---
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose",  action='store_true',    help="Verbose mode")

parser.add_argument("-S", "--send",     action='store_true',    help="Send messages to MQ",                     default=False)
parser.add_argument("-R", "--receive",  action='store_true',    help="Receive messages from MQ",                default=False)

parser.add_argument("-s", "--schedule", type=str,               help='Path to the schedule (YAML)',             default='')

parser.add_argument("-f", "--factor",   type=float,             help='Time factor',                             default=1.0)
parser.add_argument("-u", "--until",    type=float,             help='The limit, if undefined: end of schedule',default=None) #  required=False, nargs='?')
parser.add_argument("-c", "--clock",    type=float,             help='Scheduler clock freq(seconds)',           default=1.0)

parser.add_argument("-d", "--dest",     type=str,               help='Path to the destination folder, if empty do not output data',  default='')

parser.add_argument("-L", "--low",      type=float,             help='The "low" time limit on STF production',  default=1.0)
parser.add_argument("-H", "--high",     type=float,             help='The "high" time limit on STF production', default=2.0)

args        = parser.parse_args()
verbose     = args.verbose

send        = args.send
receive     = args.receive

if verbose: print(f'''*** Verbose mode is set to {verbose} ***''')
if verbose: print(f'''*** Send mode is set to {send}, receive more set to {receive} ***''')

schedule    = args.schedule
dest        = args.dest

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
      
if schedule=='':    schedule    = daqsim_path + "/config/schedule-rt.yml"
if verbose:
    print(f'''*** Set the Python path: {sys.path} ***''')
    print(f'''*** Schedule description file path: {schedule} ***''')
    if dest=='':
        print(f'''*** No output destination is set, will not write data ***''')
    else:  
        print(f'''*** Output destination is set to: {dest} ***''')

    print(f'''*** Simulation time factor: {factor} ***''')

# ---
try:
    from daq import *
    if verbose:
        print(f'''*** PYTHONPATH contains the daq package, will use it ***''')
except:
    print('*** Failed to load the daq package from PYTHONPATH, exiting...***')
    exit(-1)


sndr = None
rcvr = None

if send:
    try:
        from comms import Sender
        if verbose: print(f'''*** Successfuly imported the Senderfrom comms ***''')
    except:
        print('*** Failed to import the Sender from comms, exiting...***')
        exit(-1)

    try:
        sndr = Sender(verbose=verbose)
        sndr.connect()
        if verbose: print(f'''*** Successfully instantiated and connected the Sender, will send messages to MQ ***''')
    except:
        print('*** Failed to instantiate the Sender, exiting...***')
        exit(-1)


if receive:
    try:
        from comms import Receiver
        if verbose: print(f'''*** Successfully imported the Receiver from comms ***''')
    except:
        print('*** Failed to import the Receiver from comms, exiting...***')
        exit(-1)
    
    try:
        rcvr = Receiver(verbose=verbose, processor=func) # a function to process received messages
        rcvr.connect()
        if verbose: print(f'''*** Successfully instantiated and connected the Receiver, will receive messages from MQ ***''')
    except:
        print('*** Failed to instantiate the Receiver, exiting...***')
        exit(-1)

# ---
daq = DAQ(schedule_f    = schedule,
          destination   = dest,
          until         = until,
          clock         = clock,
          factor        = factor,
          low           = low,
          high          = high,
          verbose       = verbose,
          sender        = sndr
          )

daq.run()

print('---')
if verbose:
    print(f'''*** Completed at {daq.get_time()}. Number of STFs generated: {daq.Nstf} ***''')
    print(f'''*** Disconnecting MQ communications ***''')

if send:
    if sndr:
        sndr.disconnect()
if receive:
    if rcvr:
        rcvr.disconnect()

print('---')


