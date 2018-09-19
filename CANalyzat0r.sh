#!/bin/bash

# The dir of the start script (this file)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR/src
python3 CANalyzat0r.py
