#!/bin/sh
python3 -m grpc_tools.protoc -I../pilotbuildserver/protos --python_out=./pilot/grpc --grpc_python_out=./pilot/grpc ../pilotbuildserver/protos/pilotbuild.proto