#!/usr/bin/python

from serial import Serial

def read_response(serial_port):
    response = ''
    while len(response) == 0 or response[-1] != '>':
        new_char = serial_port.read(1)
        if new_char is '':
            return 'failed read'
        else:
            response += new_char
    return response


def main():
    filterwheel = Serial('/dev/filterwheel', 115200, timeout=0.1)
    filterwheel.write('pos?\r')
    r = read_response(filterwheel)
    print(r[r.find('?'):r.find('>')])


if __name__ == "__main__":
    main()
