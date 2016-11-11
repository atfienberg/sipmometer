# for communicating with the zmq broker on the beagle board
# to read/set sipm gains/temps
# all functions return results as strings

import zmq

# need lock to make sure zmq send, recv commands are executed in correct sequence
from threading import Lock

CTXT = zmq.Context()

class Beagle:
    def __init__(self, connection_addr, timeout=200):
        self.connection_addr = connection_addr
        self.timeout = timeout
        self.open_sock()
        self.socklock = Lock()

    def open_sock(self):
        self.socket = CTXT.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
        self.socket.connect(self.connection_addr)
        
    def issue_command(self, command):
        with self.socklock:
            self.socket.send_string(command)
            try:
                return self.socket.recv().decode('utf8')
            except zmq.error.Again:
                self.socket.close()
                self.open_sock()
                return 'timeout'

    def read_temp(self, board_num, chan_num):
        return self.issue_command("board %i chan %i temp" % (board_num, chan_num))

    def read_gain(self, board_num, chan_num):
        return self.issue_command("board %i chan %i gain" % (board_num, chan_num))

    def set_gain(self, board_num, chan_num, gain):
        return self.issue_command("board %i chan %i gain %i" % (board_num, chan_num, gain))

    def read_pga(self, board_num, chan_num):
        return self.issue_command('board %i chan %i mem' % (board_num, chan_num))

    def bk_output_stat(self, bk_num):
        return self.issue_command('bk %i read output' % bk_num)

    def bk_read_voltage(self, bk_num):
        return self.issue_command('bk %i read voltage' % bk_num)

    def bk_read_currlim(self, bk_num):
        return self.issue_command('bk %i read current' % bk_num)

    def bk_measure_voltage(self, bk_num):
        return self.issue_command('bk %i measure voltage' % bk_num)

    def bk_measure_current(self, bk_num):
        return self.issue_command('bk %i measure current' % bk_num)

    def bk_power_on(self, bk_num):
        return self.issue_command('bk %i power on' % bk_num)

    def bk_power_off(self, bk_num):
        return self.issue_command('bk %i power off' % bk_num)

    def bk_set_voltage(self, bk_num, voltage):
        return self.issue_command('bk %i set voltage %f' % (bk_num, voltage))

    def bk_set_currlim(self, bk_num, current):
        return self.issue_command('bk %i set current %f' % (bk_num, current))

def main():
    b = Beagle('tcp://192.168.1.22:6669')
    print(b.read_temp(10))
    print(b.read_gain(10))
    print(b.set_gain(10, 50))


if __name__ == "__main__":
    main()
