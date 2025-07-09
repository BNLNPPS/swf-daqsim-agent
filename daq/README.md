# DAQSIM - the "DAQ Simulation" package

## The purpose

The DAQSIM package operates as the starting point for the overall
streaming workflow testbed, which includes data distribution and processing
elements. As the starting point, DAQSIM generates the simulated data and metadata.
Currently there is no useable payload to be put into files, so the files only
contain short bits of metadata.

Another part of the DAQSIM functionality is...


## The core of the simulator

        - Generate STFs at random intervals.
        - Notify the downstream agents via MQ and/or write to file, with the path specified in the destination.
        - The STF filename is generated based on the current date, time, state, and substate.
        - The filename template: swf.20250625.<integer>.<state>.<substate>.stf

        The metadata is also generated and is used to sent to a message queue and/or written to a file.
        Currently it contains the following fields:
        - filename: the name of the STF file
        - start: the start time of the STF in YYYYMMDDHHMMSS format
        - end: the end time of the STF in YYYYMMDDHHMMSS format
        - state: the current state of the DAQ
        - substate: the current substate of the DAQ

        The last two fields are only present in the MQ messages, the preceding ones are written to the file.

        The STF generation is controlled by the low and high limits for the arrival time of the STF.
        It is done in real-time, with the time axis controlled by the SimPy environment.
    


## States, substates

This is copied here (and will be re-synced as needed) from Torre's Google Doc.

### States
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

### Substates
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