#!/usr/bin/env bash
WORKDIR=$PWD
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
echo $DIR
echo $WORKDIR
cd $DIR
python3 -m pilot.pilot "$@" --workdir=$WORKDIR
cd $WORKDIR