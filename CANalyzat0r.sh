#!/bin/bash

set -o pipefail

export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export QT_X11_NO_MITSHM=1

# The dir of the start script (this file)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR/src

# Smoketest requested?
if [ "$1" = "smoketest" ]; then
    ARGS="$1"
fi

# Run the application using the virtual environment
PIPENV_PIPFILE=$DIR/pipenv/Pipfile pipenv run python3 CANalyzat0r.py "$ARGS"
