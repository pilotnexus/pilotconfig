#!/bin/sh
python3 -m grpc_tools.protoc -I../pilotbuildserver/protos --python_out=./pilot/grpc_gen --grpc_python_out=./pilot/grpc_gen ../pilotbuildserver/protos/pilotbuild.proto