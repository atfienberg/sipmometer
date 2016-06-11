# web app for monitoring / controlling SiPM temperatures and gains
# intended for use at June 2016 g-2 calorimeter SLAC run
# Aaron Fienberg

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, make_response, request, url_for
from flask_socketio import SocketIO, emit

from time import sleep
from datetime import datetime, timedelta
from threading import Thread, Lock
from collections import OrderedDict
from bisect import bisect_left

import numpy as np

import serial
import json
import subprocess

import beagle_class

app = Flask(__name__)
# app.debug = True     

socketio = SocketIO(app, async_mode='eventlet')

# some global variables for keeping track of stuff
current_file = None
logging_temps = False
running_data = []
sample_datetimes = []
log_thread = None
keep_logging = False
bks = []
bk_lock = Lock()
sipm_serials = []
beagles = [beagle_class.Beagle('tcp://192.168.1.22:6669',100),beagle_class.Beagle('tcp://192.168.1.23:6669',100)]

sipm_map = None
with open('sipmMapping.json') as json_file:
    sipm_map = json.load(json_file)
present_sipms = []
for i in range(54):
    present_sipms.append(True if 'sipm%i' % i in sipm_map else False)


# prepare gain table
gain_table = [['gain setting', 'dB', 'amplitude ratio']]
for setting in range(81):
	dB = 26 - setting/4.0
	gain_table.append([setting, dB, round(10**(dB/20.0),2)])

# temporary for slac
all_temps_ignore = [0, 9, 16, 18, 27, 36, 45]

@app.route('/')
def home():
    return render_template('sipmgrid.html', sipm_numbers=range(53,-1,-1), present_sipms=present_sipms, serials=sipm_serials)


@app.route('/gaingrid')
def gain_grid():
	return render_template('gaingrid.html', sipm_numbers=range(53, -1, -1), present_sipms=present_sipms, serials=sipm_serials)


@app.route('/preview', methods=['POST'])
def preview_gains():
	filestr = request.files['file'].read().decode('utf-8')
	try:
		gain_map = json.loads(filestr)
	except:
		return render_template('badfile.html')
	file_present_sipms = [False for i in range(54)]
	new_gains = [0 for i in range(54)]
	for sipm_num in range(54):
		if 'sipm%i' % sipm_num in gain_map:
			file_present_sipms[sipm_num] = True
			new_gains[sipm_num] = gain_map['sipm%i' % sipm_num]
	return render_template('previewgains.html', sipm_numbers=range(53,-1,-1), present_sipms=file_present_sipms, gains=new_gains, filename=request.files['file'].filename)


@app.route('/alltemps')
def all_temps():
    return render_template('alltemps.html')


@app.route('/sipm<int:sipm_num>')
def sipm_graph(sipm_num):
    return sipm_graph_next(sipm_num, 'next')


@app.route('/sipm<int:sipm_num>_<string:next_str>')
def sipm_graph_next(sipm_num, next_str):
    if sipm_num >= 0 and sipm_num < 54:
        if 'sipm%i' % sipm_num in sipm_map:
            return render_template('singlesipm.html', num=sipm_num, serial=sipm_serials[sipm_num])
        elif next_str == 'next':
            return redirect(url_for('sipm_graph_next', sipm_num=sipm_num+1, next_str=next_str))
        else:
            return redirect(url_for('sipm_graph_next', sipm_num=sipm_num-1, next_str=next_str))
    else:
        return render_template('notfound.html')


@app.route('/stopLogging')
def stop_logging():
    global logging_temps
    if logging_temps:
        kill_logger()
        logging_temps = False
    return render_template('loggingstopped.html')


@app.route('/restartLogging')
def restart_logging():
    global logging_temps
    logging_temps = False
    start_logging()
    return redirect(url_for('home'))


@app.route('/gainfile_<string:filename>')
def deliver_gain_file(filename):
    gain_dict = OrderedDict()
    for i in range(54):
        if present_sipms[i]:
            gain_dict['sipm%i' % i] = int(get_gain(i))
    response = make_response(json.dumps(gain_dict, indent=4, separators=(',', ': ')));
    if not filename.endswith('.json'):
        filename += '.json'
    response.headers['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


@app.route('/gaintable')
def gaintable():
	return render_template('gaintable.html', table=gain_table)


@app.route('/bkcontrols')
def bkcontrols():
    return render_template('bkcontrols.html', bks=[i for i, j in enumerate(bks) if j is not None])


@app.route('/findbks')
def findbks():
    open_bks()
    return redirect(url_for('bkcontrols'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('notfound.html'), 404


@socketio.on('logging?')
def reply_logging_status():
    emit('logging status', {'logging': logging_temps})


@socketio.on('temp plot')
def temp_plot(msg):
    if len(running_data) < 2:
        return
    if msg['num'] in all_temps_ignore:
        return
    start_index = get_start_index(msg)
    data = [['time', 'temp', 'plus', 'minus']]
    # downsample to help with performance
    plot_data = running_data[start_index:]
    stepsize = len(plot_data) // 100 if len(plot_data) > 100 else 1
    plus = plot_data[-1][msg['num']+1] + 0.3
    minus = plot_data[-1][msg['num']+1] - 0.3
    for row in plot_data[::stepsize]:
        data.append([row[0], row[msg['num'] + 1], plus, minus])
    emit('plot ready', {'num': msg['num'], 'data': data})


@socketio.on('all temps')
def all_temps_plot(msg):
    if len(running_data) < 2:
        return
    start_index = get_start_index(msg)
    header = ['time']
    header.extend('sipm %i' % i for i in range(54) if 'sipm%i' % i in sipm_map and i not in all_temps_ignore)
    data = [header]
    # downsample to help with performance
    plot_data = running_data[start_index:]
    stepsize = len(plot_data) // 100 if len(plot_data) > 100 else 1
    for row in plot_data[::stepsize]:
        data.append([element for element in row if element != 'no sipm'])

    max_index = next((i for i, val in enumerate(running_data[-1][1:]) if val != 'no sipm')) + 1
    min_index = max_index
    
    for index, val in enumerate(plot_data[-1]):
        if val != 'no sipm' and index != 0:
            if val > plot_data[-1][max_index]:
                max_index = index
            if val < plot_data[-1][min_index]:
                min_index = index
    avgdata = [['time', 'average temp', 'sipm%i' %
                (max_index - 1), 'sipm%i' % (min_index - 1)]]
    for row in plot_data[::stepsize]:
        numeric_row = [element for element in row if element != 'no sipm']
        avgdata.append([row[0], np.sum(numeric_row[1:]) /
                        (len(numeric_row)-1), row[max_index], row[min_index]])
    emit('all temps ready', {'data': data, 'avgdata': avgdata})


@socketio.on('all gains')
def all_gains():
    for i in range(54):
        if 'sipm%i' % i in sipm_map:
            emit('sipm gain', {'gain': get_gain(i), 'num': str(i)})


@socketio.on('single gain')
def single_gain(msg):
    num = int(msg['num'])
    if 'sipm%i' % num in sipm_map:
        emit('sipm gain', {'gain': get_gain(num), 'num': num})


@socketio.on('set gain')
def set_gain_callback(msg):
    try:
        sipm_num = int(msg['num'])
    except ValueError:
        return
    try:
        new_gain = int(msg['new_gain'])
    except ValueError:
        return
    if present_sipms[sipm_num]:
        set_gain(sipm_num, new_gain)
        emit('sipm gain', {'gain': get_gain(sipm_num), 'num': sipm_num})


@socketio.on('set all gains')
def set_all_gains(msg):
    try:
        new_gain = int(msg['new_gain'])
    except ValueError:
        return
    for sipm_num in range(54):
        if present_sipms[sipm_num]:
            set_gain(sipm_num, new_gain)
            emit('sipm gain', {'gain': get_gain(sipm_num), 'num': sipm_num})


@socketio.on('set these gains')
def set_these_gains(msg):
	for sipm_num in range(54):
		if present_sipms[sipm_num] and 'sipm%i' % sipm_num in msg:
			set_gain(sipm_num, int(msg['sipm%i' % sipm_num]))


@socketio.on('bk status')
def bk_status():
    with bk_lock:
        for num, bk in enumerate(bks):
            if bk is not None:
                emit('bk status', query_bk_status(bk, num), broadcast=True)


@socketio.on('new voltage pt')
def new_voltage_pt(msg):
    with bk_lock:
        bk = bks[int(msg['num'])]
        if bk is not None:
            write_string = 'SOUR:VOLT %.3f\n' % float(msg['new setting'])
            bk.write(write_string.encode('utf-8'))
            subprocess.call(['./setBiasODB', str(msg['num']+1), str(msg['new setting'])])
            emit('bk status', query_bk_status(bk, int(msg['num'])))

@socketio.on('toggle bk power')
def toggle_bk_power(msg):
    with bk_lock:
        bk = bks[int(msg['num'])]
        if bk is not None:
            if msg['on']:
                bk.write(b'OUTP:STAT 1\n')
            else:
                bk.write(b'OUTP:STAT 0\n')
                emit('bk status', query_bk_status(bk, int(msg['num'])))


def query_bk_status(bk, num):
    status = {'num' : str(num)}
    bk.write(b'OUTP:STAT?\n')
    status['outstat'] = read_response(bk)
    bk.write(b'SOUR:VOLT?\n')
    status['voltage'] = read_response(bk)
    bk.write(b'SOUR:CURR?\n')
    status['current'] = read_response(bk)
    bk.write(b'MEAS:VOLT?\n')
    status['measvolt'] = read_response(bk)
    bk.write(b'MEAS:CURR?\n')
    status['meascurr'] = read_response(bk)
    return status


def get_start_index(msg):
    try:
        hours = float(msg['hours'])
        hours = hours if hours > 0 else None
    except ValueError:
        hours = None
    start_index = 0
    if hours is not None:
        target_time = datetime.now() - timedelta(hours=hours)
        start_index = bisect_left(sample_datetimes, target_time)
    return start_index if start_index < len(running_data) else 0


def update_temps():
    while keep_logging:
        sleep(10)
        measure_temps()


def measure_temps():
    with open(current_file, 'a') as file:
        now = datetime.now()
        sample_datetimes.append(now)
        file.write('%02i/%02i/%02i' % (now.month, now.day, now.year))
        file.write(', %02i:%02i:%02i' % (now.hour, now.minute, now.second))
        running_data.append([])
        running_data[-1].append('%02i:%02i:%02i' %
                                (now.hour, now.minute, now.second))
        temps = []
        for i in range(54):
            try:
                map_num = sipm_map['sipm%i' % i]
                beagle_num = map_num // 32
                channel_num = map_num % 32
                temps.append(float(beagles[beagle_num].read_temp(channel_num)) if present_sipms[i] and i not in all_temps_ignore else 'no sipm')
            except (ValueError, KeyError):
                temps.append('no sipm')
        for i, temp in enumerate(temps):
            if temp != 'no sipm':
                file.write(', %.2f' % temps[i])
                socketio.emit(
                    'sipm temp', {'temp': '%.2f' % temps[i], 'num': str(i)})
        file.write('\n')
    running_data[-1].extend(temps)


def get_gain(sipm_num):
    if present_sipms[sipm_num]:
        map_num = sipm_map['sipm%i' % sipm_num]
        beagle_num = map_num // 32
        channel_num = map_num % 32
        return beagles[beagle_num].read_gain(channel_num)


def set_gain(sipm_num, new_gain):
    if present_sipms[sipm_num] and (0 <= new_gain <= 80):
        map_num = sipm_map['sipm%i' % sipm_num]
        beagle_num = map_num // 32
        channel_num = map_num % 32
        return beagles[beagle_num].set_gain(channel_num, new_gain)

def kill_logger():
    global keep_logging, log_thread
    keep_logging = False
    if log_thread is not None and log_thread.is_alive():
        log_thread.join()


def start_logging():
    global logging_temps, log_thread, current_file, keep_logging
    if not logging_temps:
        logging_temps = True
        kill_logger()
        del running_data[:]
        del sample_datetimes[:]
        now = datetime.now()
        current_file = 'temps/tempFile%02i_%02i_%02i_%02i:%02i:%02i.txt' % (
            now.month, now.day, now.year, now.hour, now.minute, now.second)
        with open(current_file, 'w') as file:
            file.write('date, time')
            for sipm_num in range(54):
                if 'sipm%i' % sipm_num in sipm_map and sipm_num not in all_temps_ignore:
                    file.write(', sipm%i' % sipm_num)
            file.write('\n')
            measure_temps()
        log_thread = Thread(name='temp_updater', target=update_temps)
        keep_logging = True
        log_thread.start()


def read_response(serial_port):
    response = ''
    while len(response) == 0 or response[-1] != '\n':
        new_char = (serial_port.read(1)).decode("utf-8")
        if new_char == '':
            return 'failed read'
        else:
            response += new_char
    return response[:-1]


def open_bks():
    with bk_lock:
        for bk in bks:
            try:
                bk.close()
            except:
                pass
        del bks[:]
        for num in range(4):
            try:
                bks.append(serial.Serial('/dev/bk%i' % (num + 1), 4800, timeout=0.5))
            except:
                bks.append(None)
            if bks[num] is not None:
                bks[num].write(b'SOUR:CURR 0.005\n')


def fill_sipm_serials():
    del sipm_serials[:]
    for sipm_num in range(54):
        if present_sipms[sipm_num]:
            map_num = sipm_map['sipm%i' % sipm_num]
            beagle_num = map_num // 32
            channel_num = map_num % 32
            serial = beagles[beagle_num].read_pga(channel_num)
            try:
                sipm_serials.append(int(serial.split()[0]))
            except:
                sipm_serials.append(None)
        else:
            sipm_serials.append(None)


if __name__ == '__main__':
    open_bks()
    fill_sipm_serials()
    socketio.run(app)
