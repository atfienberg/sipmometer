#!/bin/bash

if [[ $# -eq 2 ]]; then
    echo -ne "SOUR:VOLT $2\n" > "/dev/bk$1"
fi
