#! /usr/bin/env python
#############################################
import os, argparse, datetime, sys
from   sys import exit
from   pathlib import Path

###################### Main code
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose",  action='store_true',    help="Verbose mode")
parser.add_argument("-t", "--tst",      action='store_true',    help="Test mode")
parser.add_argument("-e", "--envtest",  action='store_true',    help="Test the environment variables and exit", default=False)
parser.add_argument("-M", "--monitor",  action='store_true',    help="Get run number from run monitor",         default=False)

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
tst         = args.tst
envtest     = args.envtest
monitor     = args.monitor

send        = args.send
receive     = args.receive

if verbose: print(f'''*** Verbose: {verbose}, Test: {tst}, Send: {send}, Monitor: {monitor} ***''')

schedule    = args.schedule
dest        = args.dest

factor      = args.factor
until       = args.until
clock       = args.clock

low         = args.low
high        = args.high

# ---


if verbose: print('*** Setting up environment variables for the DAQ simulator... ***')
SWF_COMMON_LIB_PATH = ''
# DAQSIM_PATH         = ''

try:
    SWF_COMMON_LIB_PATH = os.environ['SWF_COMMON_LIB_PATH']
    if verbose: print(f'''*** The SWF_COMMON_LIB_PATH is defined in the environment: {SWF_COMMON_LIB_PATH}, will be added to sys.path ***''')
    if SWF_COMMON_LIB_PATH not in sys.path: sys.path.append(SWF_COMMON_LIB_PATH)
    src_path = SWF_COMMON_LIB_PATH + '/src/swf_common_lib'
    if src_path not in sys.path:
        sys.path.append(src_path)
    else:
        if verbose: print(f'''*** {src_path} is already in sys.path ***''')
except:
    if verbose: print('*** The variable SWF_COMMON_LIB_PATH is undefined, will rely on PYTHONPATH ***')



# Get the absolute path of the current file
current_path = Path(__file__).resolve()

# Get the directory above one containing the current file
top_directory = current_path.parent.parent
print(f"Top directory: {top_directory}")

if top_directory not in sys.path:
    sys.path.append(str(top_directory))
    if verbose: print(f'''*** Added {top_directory} to sys.path ***''')
else:
    if verbose: print(f'''*** {top_directory} is already in sys.path ***''')

        
if verbose:         print('*** Environment variables for the DAQ simulator are set up. ***')
if schedule=='':    schedule    = DAQSIM_PATH + "/config/schedule-rt.yml"

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
        print(f'''*** Imported the daq package from PYTHONPATH ***''')
except:
    print('*** Failed to import the daq package from PYTHONPATH, exiting...***')
    exit(-1)


from rest_logging import setup_rest_logging

if envtest:
    print('*** Main environment variables have been tested, exiting... ***')
    exit(0) 

# ---
daq = DAQ(schedule_f    = schedule,
          destination   = dest,
          until         = until,
          clock         = clock,
          factor        = factor,
          low           = low,
          high          = high,
          verbose       = verbose,
          test          = tst)

daq.run()

if verbose:
    print(f'''*** Completed at {daq.get_simpy_time()}. Number of STFs generated: {daq.Nstf} ***''')


# from set_environment import setenv # This will setup the Python environment

# # Helper functions
# # ---
# def func(to_print):
#     print(to_print) # for MQ: a simple function to process received messages

# # ---
# def get_sender_and_receiver(verbose, func): # if needed, setup the sender and receiver
#     sndr = None
#     rcvr = None

#     try:
#         from mq_comms import Sender
#         if verbose: print(f'''*** Successfuly imported the Sender from mq_comms ***''')
#     except:
#         print('*** Failed to import the Sender from mq_comms, exiting...***')
#         exit(-1)

#     try:
#         sndr = Sender(verbose=verbose)
#         if verbose: print(f'''*** Successfully instantiated the Sender ***''')
#         sndr.connect()
#         if verbose: print(f'''*** Successfully connected the Sender to MQ ***''')
#     except:
#         print('*** Failed to instantiate the Sender, exiting...***')
#         exit(-1)


#     try:
#         from mq_comms import Receiver
#         if verbose: print(f'''*** Successfully imported the Receiver from comms ***''')
#     except:
#         print('*** Failed to import the Receiver from comms, exiting...***')
#         exit(-1)
    
#     try:
#         rcvr = Receiver(verbose=verbose, processor=func) # a function to process received messages
#         rcvr.connect()
#         if verbose: print(f'''*** Successfully instantiated and connected the Receiver, will receive messages from MQ ***''')
#     except:
#         print('*** Failed to instantiate the Receiver, exiting...***')
#         exit(-1)

#     return sndr, rcvr
