# ePIC streaming computing testbed: the DAQ agent simulator

---

## About
* __Work Title__: _swf-daqsim-agent_
* __Purpose__: To simulate the state machine of the ePIC DAQ, including its components interacting
with the data management, prompt processing and ast monitoring systems.
* __Tools__: We use _SimPy_ which appears to be well suited for the task. It's a discrete event
simulation framework written in Python.

In terms of interaction with other components, the two principal modes taking
place simultaneously are:

* Mock-up data representing the STF files
* Messages sent to other agents via MQ, to trigger the overall orchestration
of data distribution and processing.

The working version of the file names is as follows:

```bash
# Integers in this notation are:
# run date: YYYYMMDD
# time to a second precision: hhmmss
# microseconds for the same timestamp
swf.<integer>.<integer>.<integer>.<state>.<substate>.stf
# Example:
swf.20250914.185727.197966.run.physics.stf
```

Regarding the Python dependencies, they are captured in the _requirements_ file in this repository.

---

## The Simulation

The simulation driver script is located in the _simulator_ folder.
```bash 
./simulator/daq_simulator.py
```

It is equipped with a comprehensive set of CLI options. The "--help"
option will output the available parameters.

### Time handling

We make use of the real time features of SimPy. The default time unit is 1.0s, i.e.
that's what will determine the speed of actual execution that includes a variety of
delays and timeouts defined in the units of time. There is a way to speed up the
simulation or slow it down, by introducing a time scaling factor. In this package,
the time "starts" when the main simulation class is instantiated, corresponding
to 0.0 on the time axis.

### The Schedule

The critical part of the simulation is the process of state transitions in the DAQ.
For simulation purposes, we define "schedule" as a list of points on the timeline,
with assigned states (and possibly sub-states to be added later). The points are
defined as tuples of **(weeks, days, hours, minutes, seconds)** for ease of human interaction
but internally these data are converted to seconds (as floats). A dedicated method
in the simulator class keeps watch of the states and actuates transitions.

### States and Substates

Please see the README in the **daq** package folder:
https://github.com/BNLNPPS/swf-daqsim-agent/tree/main/daq#states-substates

## Communications

This agent is using _ActieMQ_ to send notifications to the swf-data-agent and other elements of the test bed.
The Python package _stomp-py_ needs to be installed to support the current version of this interface.

**For the ActiveMQ communications to work, the following evironment variables need to be set**
* MQ_PASSWD
* MQ_USER
* MQ_CAFILE


There are two types of messages: the run status messages (imminent/start/end),
and STF generation messages, notifying the system that a STF has been created.

### Run Status Messages

These messages carry the unique run ID and the timestamp. In current design, we opted for using
the string representing the start of the run timestamp as its unique ID, for better readbility.
This is an acceptable solution because in all realistic scenarios the run manager is always
a singleton.

Examples:

```json
{"msg_type": "start_run", "req_id": 1, "run_id": 20250914185722, "ts": "20250914185722"}
```

The timestamp convention is **%Y%m%d%H%M%S**. This is different from the timestamp format
in the STF message (below) which needs more granularity.

### STF Generation Message

The STF generation message carries an attribute specifying the run ID, to simplify
accounting and adata management procedures. It also contains attributes relevant
to data handling downstream, such as the checksum (_adler32_) and size, in bytes.

The format of the messages sent out to MQ by the simulator is illustrated in
the following example:

```json
{"run_id": 20250914185722, "state": "no_beam", "substate": "calib", "filename": "swf.20250914.185724.767135.no_beam.calib.stf", "start": "20250914185722420185", "end": "20250914185724767135", "checksum": "ad:3915264619", "size": 191, "msg_type": "stf_gen", "req_id": 1}
```

The last two elements in this dictionary are added on top of the metadata generated
for each simulated STF file, so the content above these trailing two is identical
between the metadata and the MQ message.

The file metadata is formed using this piece of Python code, presented here to elucidate
the metadata format. This is from a method of the generator:

```python
md ={
    'run_id':       self.run_id,
    'state':        self.state,
    'substate':     self.substate,
    'filename':     filename,
    'start':        start.strftime("%Y%m%d%H%M%S%f"),
    'end':          end.strftime("%Y%m%d%H%M%S%f")
}
```

The _start_ and _end_ attributes relate to the start of the STF generation and its end.
Microsecond precision is used to avoid overlaps and clashes.


