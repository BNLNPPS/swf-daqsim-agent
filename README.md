# ePIC streaming computing testbed: the DAQ agent simulator

---

## Disclaimer

The _comms_ part is currently work in progress, it's a stub not ready for real use.

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

```
swf.20250625.<integer>.<state>.<substate>.stf
```

Regarding the Python dependencies, they are captured in the _requirements_ file in this repository.

---

## The Simulation

At the time of writing, the prototype aimulation driver script *sim_test.py* is located in the
folder **test**. It has equipped with a comprehensive set of CLI options. The "--help"
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

Please see the README in the **daq** package folder.


## Communications

This agent is using ActieMQ to send notifications to the swf-data-agent and other elements of the test bed.
The Python package _stomp-py_ needs to be installed in the current version of this interface.
Credentials are provided via the environment variables defined for this purpose.




