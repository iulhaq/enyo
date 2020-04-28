#!/bin/bash

ping -q -w1 -c1 130.57.66.6

if [[ $? -eq 0 ]]; then
        echo "Online"
else
        echo "Offline"
fi
