# The ActiveMQ communications

## Environment variables

MQ_USER and MQ_PASSWD environment variables nees to be set
for the package to work.

MQ_HOST and MQ_CAFILE have default values in the code.

## Classes

The _Sender_ and _Receiver_ classes inherit their common
functionality from the _Messenger_, the base class. They can
be instantiated separately as needed and are agnostic with
regards to the logic of the simulation.

