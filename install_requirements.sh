#!/bin/bash

sudo apt update && \
sudo apt -y install \
   can-utils \
   ffmpeg \
   iproute2 \
   python3-pip \
   python3-pyside \
   python3.5  && \
sudo pip3 install --upgrade pip && \
sudo pip3 install \
   pyvit \
   sphinx_rtd_theme
