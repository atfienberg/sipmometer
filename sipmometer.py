import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from time import sleep
from datetime import datetime
from threading import Thread

import numpy as np

app = Flask(__name__)
# app.debug = True
socketio = SocketIO(app, async_mode='eventlet')

temps = []

running_data = []


def update_temps():
    while True:
        sleep(1)
        with open('temps/sipmtemps.txt', 'a') as file:
            now = datetime.now()
            file.write('%02i/%02i/%02i' % (now.month, now.day, now.year))
            file.write(', %02i:%02i:%02i' % (now.hour, now.minute, now.second))
            running_data.append([])
            running_data[-1].append('%02i:%02i:%02i' % (now.hour, now.minute, now.second))
            for i, temp in enumerate(temps):
                temps[i] = round(temp + np.random.uniform(-.1, .1), 2)
                file.write(', %.2f' % temps[i])
                socketio.emit(
                    'sipm temp', {'temp': '%.2f' % temps[i], 'num': str(i)})
            file.write('\n')
        running_data[-1].extend(temps)


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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error404.html'), 404


@socketio.on('temp plot')
def temp_plot(msg):
    data = [['time', 'temp']]
    for row in running_data:
        data.append([row[0], row[msg['num'] + 1]])
    emit('plot ready', {'num': msg['num'], 'data': data})


@socketio.on('all temps')
def all_temps_plot():
    header = ['time']
    header.extend('sipm %i' % i for i in xrange(54))
    data = [header]
    for row in running_data:
        data.append([element for element in row])
    emit('all temps ready', {'data': data})

@socketio.on('all gains')
def all_gains():
	for i in xrange(54):
		emit('sipm gain', {'gain': str(get_gain(i)), 'num' : str(i)})

@socketio.on('single gain')
def single_gain(msg):
	num = int(msg['num'])
	emit('sipm gain', {'gain': str(get_gain(num)), 'num' : str(num)})

def get_gain(sipm_num):
	return 50

if __name__ == '__main__':
    with open('temps/sipmtemps.txt', 'w') as file:
        file.write('date, time')
        for sipm_num in range(54):
            file.write(', sipm%i' % sipm_num)
            temps.append(round(np.random.uniform(20, 50), 2))
        file.write('\n')
        now = datetime.now()
        file.write('%02i/%02i/%02i' % (now.month, now.day, now.year))
        file.write(', %02i:%02i:%02i' % (now.hour, now.minute, now.second))
        file.write(''.join(', %.2f' % temp for temp in temps))
        running_data.append([])
        file.write('\n')
    	running_data[-1].append('%02i:%02i:%02i' % (now.hour, now.minute, now.second))
    running_data[-1].extend(temps)

    t = Thread(name='temp_updater', target=update_temps)

    t.start()
    socketio.run(app)
