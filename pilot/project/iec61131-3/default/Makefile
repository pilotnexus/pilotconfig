all: plc build

help:
	@echo "make fw ...... Build Firmware code"
	@echo "make plc ..... Build PLC code"
	@echo "make build ... Compile firmware"

fw-local:
	docker run -v ${PWD}/fwbase:/out pilotbuild:1.0.0 build --module1 o8 --module3 fpga --plcenable

fw:
	pilot setup --node 192.168.101.78 --source ./fwbase

plc:
	pilot build --source ./fwbase/stm/ --config .pilotfwconfig.json test.st motors.c motors.h

build:
	$(MAKE) -C ./out plc

program:
	sshpass -p raspberry scp
	sshpass -p raspberry scp ./out/stm.bin pi@192.168.101.78:/tmp/pilot/
	sshpass -p raspberry scp ./out/VARIABLES.csv pi@192.168.101.78:/tmp/pilot/