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

This is copied here (and will be re-synced as needed) from Torre's Google Doc.
Kept here to have it close to the code:

#### States
* no_beam
   * Collider not operating
* beam
   * Collider operating
* run
   * Physics running
* calib
   * Dedicated calibration period
* test
   * Testing, debugging
   * Any substates can be present during test

#### Substates
* not_ready
   * detector not ready for physics datataking
   * occurs during states: no_beam, beam, calib
* ready
   * collider and detector ready for physics, but not declared as good for physics
   * when declared good for physics, transitions from beam/ready to run/physics
   * occurs during states: beam
* physics
   * collider and detector declared good for physics
   * if collider or detector drop out of good for physics, state transitions out of ‘run’ to ‘beam’ (or ‘off’ as appropriate)
   * occurs during states: run
* standby
   * collider and detector still good for physics, but standing by, not physics datataking (dead time!)
   * occurs during states: run
* lumi
   * detector, machine data that is input to luminosity calculations
   * occurs during states: beam, run
* eic
   * machine data, machine configuration
   * occurs during states: all
* epic
   * detector configuration, data
   * occurs during states: all
* daq
   * info, config transmitted from DAQ
   * occurs during states: all
* calib
   * a catch-all for a great many calib data types, we can start small
   * occurs during states: all (assuming there are cases where calib data is taken during beam on)





