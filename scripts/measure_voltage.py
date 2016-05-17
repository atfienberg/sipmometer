#!/usr/bin/python

import sys
import serial
from read_bk_serial import read_response

def main():
    if len(sys.argv) != 2:
        print('usage: read_voltage.py <bknum>')
        sys.exit(1)
    bk = serial.Serial('/dev/bk'+sys.argv[1], 4800, timeout=0.5)
    bk.write('MEAS:VOLT?\n')
    print(read_response(bk)[:-1])
    

if __name__ == '__main__':
    main()
