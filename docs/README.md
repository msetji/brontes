# Welcome to the Brontes Documentation

## API Guide

### Component

A component represents a specific item within a facility. This can include building parts such as windows, doors, HVAC units, or any other equipment.

### Device

The Devices API is based upon the BACnet protocol. A device represents a controller on the buildings network.
By facilitating direct communication with equipment, sensors, and actuators, each Device plays a pivotal role in the real-time monitoring and control of physical systems.
A Device is usually related directly to a single component, but there can be cases when a device relates to multiple components.

### Point

A point represents a single data source - this can be a sensor reading, a command, a status, or any piece of information that can be monitored or controlled via the network.
If points come from the Building Automation System they will be directly related to a Device.
Points will always need to be related to a Component.
