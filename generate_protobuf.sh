#!/bin/sh

# pilotbuild protos
python3 -m grpc_tools.protoc -I../pilotbuildserver/protos --python_out=./pilot/grpc_gen --grpc_python_out=./pilot/grpc_gen ../pilotbuildserver/protos/pilotbuild.proto

# pilotd protos
python3 -m grpc_tools.protoc -I../pilotd/api/protos --python_out=./pilot/grpc_gen --grpc_python_out=./pilot/grpc_gen ../pilotd/api/protos/pilot_api.proto