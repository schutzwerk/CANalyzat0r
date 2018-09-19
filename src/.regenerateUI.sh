#!/bin/bash

# This script can be used to regenerate the main GUI and its resources
# after editing them

cd ui && pyside-uic mainWindow.ui > mainWindow.py && cd -
pyside-rcc -py3 -o res_rc.py res.qrc
