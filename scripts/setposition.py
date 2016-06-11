#!/usr/bin/python

from serial import Serial
import sys

def main():
    if len(sys.argv) != 2:
        print('requires one argument, the filter position')      
        sys.exit(1)
    filterwheel = Serial('/dev/filterwheel', 115200, timeout=0.1)
    filterwheel.write('pos=%i\r' % int(sys.argv[1]))
    filterwheel.close()

if __name__ == "__main__":
    main()
