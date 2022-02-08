# CHANGELOG

## 2.2.4
Improved help moustache model data (slot, module (zero based slot number) and tty/tty1/tty2 is now available for --usage help)
## 2.2.0
Login methodology changed. If no parameter is specified, a key file is used. A password can be provided with '--password' or '-p'. If the password after this parameter is ommitted, it will be prompted safely (without displaying it)
## 2.0.9
bugfix: fix when modules are specified directly
## 2.0.8
added --module parameter to get help for modules (description, pinout, usage)
## 2.0.7
specific firmware version can now be specified with the --fw-version parameter
## 2.0.6
added reset command, increased watchdog_timeout default to 100ms (to not interrupt EEPROM writes)
## 2.0.5
prompt reboot when drivers are build locally & installed
## 2.0.4
removed unnecessary tkinter import

## 2.0.2
If the pilot driver has no compiled version in the package repository you can now opt-in to build and install it locally.
Works only on the Raspberry Pi.

## 2.0.1
First version that uses the GRPC build server instead of the old (GraphQL)


