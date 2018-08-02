=================
Pilot Config Tool
=================

Install:
`sudo -H pip3 install pilot-config`

Upgrade:
`sudo -H pip3 install --upgrade pilot-config`

Run:
`pilot setup`
to setup your system

**************************************************
Run docker container for custom firmware build
**************************************************

Run the following command from the project directory (containing the config.json and the st file)

`docker run -v $PWD/fwbase/stm:/src -v $PWD:/files pilotplc:latest` /files/file.st

Note: the /files/ must be added, even if the file is in the current directory because of the dir mapping