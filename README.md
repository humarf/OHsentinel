# OHsentinel
command line interface to openhome devices and openhab integration

Inspired from upcmd this is a python and xsl based command line interface to openhome devices. It provides three levels of integration:

- direct command line interface to OHdevices
- a server script that registers to OHdevices and fetches events that can be forwarded to openhab items
- pushing command strings to server script to be forwarded from service script to OHdevice (faster because no intital upnp dialog is needed)

For installation instructions please refer to the [wiki](https://github.com/humarf/OHsentinel/wiki/Home#installation).
