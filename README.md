=================
Pilot Config Tool
=================

Prerequisites:
`sudo apt-get install libssl-dev libffi-dev`

Install locally on the Single Board Computer (Raspberry Pi or Google Coral):
`sudo -H pip3 install pilot-config`

Upgrade:
`sudo -H pip3 install --upgrade pilot-config`

Run:
`sudo pilot setup`
to setup your system or
`pilot setup --node [IP] --user [user] --password [password]`
to setup the firmware remotely
