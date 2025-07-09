#! /usr/bin/env python

#############################################

import os, argparse, sys, json, uuid
from sys import exit
from time import sleep

# --- PanDA counters ---
panda_success_count = 0
panda_fail_count = 0

# --- Message counter ---
message_received_count = 0

# --- PanDA submission helper ---
def submit_panda_job(stf_json):
    global panda_success_count, panda_fail_count
    from pandaclient import PrunScript, panda_api

    unique_id = str(uuid.uuid4())
    filename = stf_json.get("filename", "unknown")

    out_ds_name = f"user.eumaka.{filename}.{unique_id}"
    unique_taskname = f"stf_task_{filename}_{unique_id}"

    exec_str = f"./my_script.sh '{json.dumps(stf_json)}'"

    PANDA_AUTH_VO = os.getenv('PANDA_AUTH_VO')
    if not PANDA_AUTH_VO:
        print("Error: PANDA_AUTH_VO is not set.")
        panda_fail_count += 1
        return

    prun_args = [
        "--exec", exec_str,
        "--outDS", out_ds_name,
        "--nJobs", "1",
        "--vo", "wlcg",
        "--site", "BNL_PanDA_1",
        "--prodSourceLabel", "managed",
        "--workingGroup", PANDA_AUTH_VO,
        "--noBuild",
        "--outputs", "myout.txt"
    ]

    if verbose:
        print(f"[DEBUG] Using exec: {exec_str}")
        print(f"[DEBUG] Running prun from current directory: {os.getcwd()}")

    print(f"[INFO] Starting PanDA submission for STF: {filename}")
    try:
        params = PrunScript.main(True, prun_args)
        params['taskName'] = unique_taskname

        if verbose:
            print(f"[DEBUG] Submission params:\n{json.dumps(params, indent=2)}")

        c = panda_api.get_api()
        status, result_tuple = c.submit_task(params)

        if status == 0:
            jedi_task_id = result_tuple[2]
            monitor_url = os.getenv('PANDAMON_URL', 'https://pandamon01.sdcc.bnl.gov')
            print(f"✅ Submitted! JediTaskID: {jedi_task_id}")
            print(f"🔗 {monitor_url}/task/{jedi_task_id}/")
            panda_success_count += 1
        else:
            print(f"❌ Submission failed. Status: {status}, Message: {result_tuple}")
            panda_fail_count += 1

    except Exception as e:
        print(f"[ERROR] Exception during PanDA submission: {e}")
        panda_fail_count += 1


# ---
message_started = False

def func(to_print):
    global message_started, message_received_count
    if not message_started:
        # Comment when it starts receiving files/messages
        print('*** Started receiving messages from MQ ***')
        message_started = True
    message_received_count += 1
    print(to_print) # a simple function to process received messages
    if submit_panda:
        try:
            stf_json = json.loads(to_print)
            submit_panda_job(stf_json)
        except Exception as e:
            print(f"[ERROR] Failed to submit PanDA job: {e}")

# ---
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose",  action='store_true', help="Verbose mode")
parser.add_argument("--submit-panda",   action='store_true', help="Submit STF jobs to PanDA", default=False)

args = parser.parse_args()
verbose = args.verbose
submit_panda = args.submit_panda

if verbose: print(f'''*** Verbose mode is set to {verbose} ***''')

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

if verbose:
    print(f'''*** Set the Python path: {sys.path} ***''')

# ---
try:
    from daq import *
    if verbose:
        print(f'''*** PYTHONPATH contains the daq package, will use it ***''')
except:
    print('*** Failed to load the daq package from PYTHONPATH, exiting...***')
    exit(-1)


rcvr = None

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
    print('*** No messages received yet. Waiting... ***')
except:
    print('*** Failed to instantiate the Receiver, exiting...***')
    exit(-1)

# ---
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    print("\nExiting…")
    rcvr.disconnect()

print('---')
print(f'''*** Total messages received: {message_received_count} ***''')
if verbose and submit_panda:
    print(f'''*** PanDA jobs submitted successfully: {panda_success_count} ***''')
    print(f'''*** PanDA jobs failed: {panda_fail_count} ***''')
print('---')

exit(0)
