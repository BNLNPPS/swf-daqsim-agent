import os, sys
def setenv(verbose) -> None:
    print('*** Setting up environment variables for the DAQ simulator... ***')
    SWF_COMMON_LIB_PATH = ''
    MQ_COMMS_PATH       = ''
    DAQSIM_PATH         = ''

    try:
        SWF_COMMON_LIB_PATH = os.environ['SWF_COMMON_LIB_PATH']
        if verbose: print(f'''*** The SWF_COMMON_LIB_PATH is defined in the environment: {SWF_COMMON_LIB_PATH}, will be added to sys.path ***''')
        if SWF_COMMON_LIB_PATH not in sys.path: sys.path.append(SWF_COMMON_LIB_PATH)
        src_path = SWF_COMMON_LIB_PATH + '/src/swf_common_lib'
        if src_path not in sys.path:
            sys.path.append(src_path)
            if verbose: print(f'''*** Added {src_path} to sys.path ***''')
        else:
            if verbose: print(f'''*** {src_path} is already in sys.path ***''')
    except:
        if verbose: print('*** The variable SWF_COMMON_LIB_PATH is undefined, will rely on PYTHONPATH ***')

    try:
        MQ_COMMS_PATH = os.environ['MQ_COMMS_PATH']
        if verbose: print(f'''*** The MQ_COMMS_PATH is defined in the environment: {MQ_COMMS_PATH}, will be added to sys.path ***''')
        if MQ_COMMS_PATH not in sys.path: sys.path.append(MQ_COMMS_PATH)
    except:
        if verbose: print('*** The variable MQ_COMMS_PATH is undefined, will rely on PYTHONPATH ***')

    try:
        DAQSIM_PATH=os.environ['DAQSIM_PATH']
        if verbose: print(f'''*** The DAQSIM_PATH is defined in the environment: {DAQSIM_PATH}, will be added to sys.path ***''')
        sys.path.append(DAQSIM_PATH)
    except:
        if verbose: print('*** The variable DAQSIM_PATH is undefined, will rely on PYTHONPATH and ../ ***')
        DAQSIM_PATH = '../'  # Add parent to path, to enable running locally (also for data)
        sys.path.append(DAQSIM_PATH)
        
        
    if verbose: print('*** Environment variables for the DAQ simulator are set up. ***')
    return None

