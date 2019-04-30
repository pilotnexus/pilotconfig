=================
Pilot Config Tool
=================

Install:
`sudo -H pip3 install pilot-config`

If install fails building the cryptography library (something along the lines of `failed with error code 1 in /tmp/pip-build-q1l8fonw/cryptography/`, run `sudo apt-get install libssl-dev` and try again (use `sudo yum install openssl-devel` on Fedora, CentOS or RHEL).

Upgrade:
`sudo -H pip3 install --upgrade pilot-config`

Run:
`pilot setup`
to setup your system

**************************************************
Run docker container for custom firmware build
**************************************************

Run the following command from the project directory (containing the .pilotfwconfig.json and the st file)

`docker run -v $PWD/fwbase/stm:/src -v $PWD:/files pilotplc:latest` /files/file.st

Note: the /files/ must be added, even if the file is in the current directory because of the dir mapping