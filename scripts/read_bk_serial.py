#!/usr/bin/python

SERIALS = ['BK PRECISION,9124,600164017687110004,V1.74',
           'BK PRECISION,9124,600164017687110014,V1.74']

import sys
import serial
import subprocess

def read_response(serial_port):
    response = ''
    while len(response) == 0 or response[-1] != '\n':
        new_char = serial_port.read(1)
        if new_char is '':
            return 'failed read'
        else:
            response += new_char
    return response


def main():
    if len(sys.argv) != 2:
        print 'usage: read_serial_bk.py <dev_file>'
        sys.exit(0)

    bk = serial.Serial('/dev/' + sys.argv[1], 4800, timeout=0.5)
    bk.write('*IDN?\n')
    resp = read_response(bk)
    print(resp[:-1])
    return


if __name__ == '__main__':
    main()

