#!/bin/bash

bkindex=0
moreiterations=1
while [ $moreiterations -eq 1 ]; do
    if [ ! -e /dev/bkoff$bkindex ]; then
	moreiterations=0
	echo "bknum=unrecognized$bkindex"
    else
	(( bkindex++ ))
    fi
done
