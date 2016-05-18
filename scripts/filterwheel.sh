#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo takes exactly one argument
elif [[ $1 -ge 1 && $1 -le 6 ]]; then 
    stty -F /dev/filterwheel 115200
    echo -n -e "pos=$1\r" > /dev/filterwheel 
else
    echo 'invalid setting'
fi
