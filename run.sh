#!/bin/bash

rm /tmp/ryu*

export PYTHONPATH=$PYTHONPATH:$(pwd)

ryu-manager --observe-links ijoin.py
