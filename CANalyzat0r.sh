#!/bin/bash

set -o pipefail

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# The dir of the start script (this file)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the application using the virtual environment
cd $DIR/src

# Smoketest requested?
if [ "$1" = "smoketest" ]; then
    ARGS="$1"
fi

PIPENV_PIPFILE=$DIR/pipenv/Pipfile pipenv run python3 CANalyzat0r.py "$ARGS"
