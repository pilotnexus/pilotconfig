# Pilot Config Tool

Configuration tool for the Pilot Automation Platform

This tool configures the firmware for your Pilot Mainboard and attached modules. You need at least a supported single board computer (SBC, currently Raspberry Pi and Google Coral are supported) and a Pilot Mainboard attached to it.

There are two options:
- Install pilot-config locally on the SBC
- Install pilot-config on a PC that can access the SBC via SSH
 
## Installation
`sudo pip3 install pilot-config`

## Upgrade
`sudo pip3 install --upgrade pilot-config`

## Run locally (on the single board computer)
`sudo pilot setup`

## Run remotely
`pilot setup --node [IP] --user [user] --password [password]`

[IP]       = hostname or IP address of your SBC
[user]     = SSH username
[password] = SSH password 


## Infos when regerating Protos

If `generate_protobuf.sh` is run, the import in `grpc_gen/pilotbuild_pb2_grpc.py` is not generated correctly.
You need to change the import in line 5 to:
``` python
from . import pilotbuild_pb2 as pilotbuild__pb2
```