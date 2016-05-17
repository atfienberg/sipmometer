#!/bin/bash

if [[ $# -eq 2 ]]; then
    echo -ne "OUTP:STAT $2\n" > "/dev/bk$1"
fi
