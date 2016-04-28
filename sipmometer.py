# web app for monitoring / controlling SiPM temperatures and gains
# intended for use at June 2016 g-2 calorimeter SLAC run
# Aaron Fienberg

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, emit

from time import sleep
from datetime import datetime
from threading import Thread

import numpy as np

app = Flask(__name__)
# app.debug = True
socketio = SocketIO(app, async_mode='eventlet')

# some global variables for keeping track of temp logging
current_file = None
logging_temps = False
running_data = []
log_thread = None
keep_logging = False

# temporary global until I actually use with real beagle board
temps = []


@app.route('/')
def home():
    return render_template('sipmgrid.html', sipm_numbers=range(54))


@app.route('/gaingrid')
def gain_grid():
    return render_template('gaingrid.html', sipm_numbers=range(54))


@app.route('/alltemps')
def all_temps():
    return render_template('alltemps.html')


@app.route('/sipm<int:sipm_num>')
def sipm_graph(sipm_num):
    if sipm_num >= 0 and sipm_num < 54:
        return render_template('singlesipm.html', num=sipm_num)
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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html'), 404


@socketio.on('logging?')
def reply_logging_status():
    emit('logging status', {'logging': logging_temps})


@socketio.on('temp plot')
def temp_plot(msg):
    data = [['time', 'temp']]
    # downsample to help with performance
    stepsize = len(running_data) // 100 if len(running_data) > 100 else 1
    for row in running_data[::stepsize]:
        data.append([row[0], row[msg['num'] + 1]])
    emit('plot ready', {'num': msg['num'], 'data': data})


@socketio.on('all temps')
def all_temps_plot():
    header = ['time']
    header.extend('sipm %i' % i for i in range(54))
    data = [header]
    # downsample to help with performance
    stepsize = len(running_data) // 100 if len(running_data) > 100 else 1
    for row in running_data[::stepsize]:
        data.append([element for element in row])
    emit('all temps ready', {'data': data})


@socketio.on('all gains')
def all_gains():
    for i in range(54):
        emit('sipm gain', {'gain': str(get_gain(i)), 'num': str(i)})


@socketio.on('single gain')
def single_gain(msg):
    num = int(msg['num'])
    emit('sipm gain', {'gain': str(get_gain(num)), 'num': str(num)})


def update_temps():
    while keep_logging:
        sleep(1)
        with open('temps/sipmtemps.txt', 'a') as file:
            measure_temps(file)


def measure_temps(file):
    with open('temps/sipmtemps.txt', 'a') as file:
        now = datetime.now()
        file.write('%02i/%02i/%02i' % (now.month, now.day, now.year))
        file.write(', %02i:%02i:%02i' % (now.hour, now.minute, now.second))
        running_data.append([])
        running_data[-1].append('%02i:%02i:%02i' %
                                (now.hour, now.minute, now.second))
        for i, temp in enumerate(temps):
            temps[i] = round(temp + np.random.uniform(-.1, .1), 2)
            file.write(', %.2f' % temps[i])
            socketio.emit(
                'sipm temp', {'temp': '%.2f' % temps[i], 'num': str(i)})
        file.write('\n')
    running_data[-1].extend(temps)


def get_gain(sipm_num):
    return 50


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
        now = datetime.now()
        current_file = 'temps/tempFile%02i_%02i_%02i_%02i:%02i:%02i.txt' % (
            now.month, now.day, now.year, now.hour, now.minute, now.second)
        with open(current_file, 'w') as file:
            file.write('date, time')
            del temps[:]
            for sipm_num in range(54):
                file.write(', sipm%i' % sipm_num)
                temps.append(round(np.random.uniform(25, 30), 2))
            measure_temps(file)
        log_thread = Thread(name='temp_updater', target=update_temps)
        keep_logging = True
        log_thread.start()


if __name__ == '__main__':
    start_logging()
    socketio.run(app)
