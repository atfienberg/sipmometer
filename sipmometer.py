
# web app for monitoring / controlling SiPM temperatures and gains
# intended for use at June 2016 g-2 calorimeter SLAC run
# Aaron Fienberg

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, make_response, request
from flask_socketio import SocketIO, emit
from collections import OrderedDict
from itertools import dropwhile
from reload_calo import reload_calo_settings
import json
import datetime
import psycopg2

import beagle_class

app = Flask(__name__)
app.debug = False

socketio = SocketIO(app, async_mode='eventlet')

# some global variables for keeping track of stuff
current_file = None
logging_temps = False
running_data = []
sample_datetimes = []

keep_logging = False
sipm_serials = [[] for i in range(24)]
# bkbeagle = beagle_class.Beagle('tcp://192.168.1.21:6669', timeout=400)
# sipmbeagle = beagle_class.Beagle('tcp://192.168.1.21:6669', timeout=100)

bkbeagles = [beagle_class.Beagle(
    'tcp://192.168.{}.21:6669'.format(i), timeout=400) for i in range(1, 25)]
sipmbeagles = [beagle_class.Beagle(
    'tcp://192.168.{}.21:6669'.format(i), timeout=100) for i in range(1, 25)]

# t0
bkbeagles += [beagle_class.Beagle('tcp://192.168.22.23:6669', timeout=400)]
sipmbeagles += [beagle_class.Beagle('tcp://192.168.22.23:6669', timeout=100)]

dbconf = None
with open('config/dbconnection.json', 'r') as f:
    dbconf = json.load(f)
cnx = psycopg2.connect(user=dbconf['user'], password=dbconf['password'],
                       host=dbconf['host'],
                       database=dbconf['dbname'], port=dbconf['port'])


def generate_calo_map(calo_num):
    cursor = cnx.cursor()
    cursor.execute(
        "SELECT calo_xtal_num, breakoutboard, sipm_id FROM calo_connection WHERE calo_id=%i ORDER BY calo_xtal_num" % calo_num)
    sipm_map = OrderedDict()
    sipm_map['calo_num'] = calo_num
    for (xtal_num, bb, sid) in cursor.fetchall():
        bb_nums = bb.split('-')
        board_num = int(bb_nums[0])
        chan_num = int(bb_nums[1])
        entry = OrderedDict()
        entry['board'] = board_num
        entry['chan'] = chan_num
        entry['sipm_id'] = sid
        sipm_map['sipm%i' % xtal_num] = entry
    cursor.close()
    return sipm_map

sipm_maps = [generate_calo_map(calo) for calo in range(1, 25)]
present_sipms = [True for i in range(54)]
sample_period = None

# prepare gain table
gain_table = [['gain setting', 'dB', 'amplitude ratio']]
for setting in range(81):
    dB = 26 - setting/4.0
    gain_table.append([setting, dB, round(10**(dB/20.0), 2)])

# temporary for slac
#all_temps_ignore = [0, 9, 18, 27, 36, 45]
all_temps_ignore = []


@app.route('/')
def root():
    return redirect('/calo23/temps')


@app.route('/calo<int:calo_num>/temps')
def temps(calo_num):
    if calo_num != 25:
        return render_template('sipmgrid.html', calo_num=calo_num, sipm_numbers=range(53, -1, -1), present_sipms=present_sipms, serials=sipm_serials[calo_num-1])
    else:
        return redirect('/calo25/bkcontrols')


@app.route('/calo<int:calo_num>/reload')
def reload_serials(calo_num):
    if calo_num != 25:
        sipm_maps[calo_num-1] = generate_calo_map(calo_num)
        fill_sipm_serials(calo_num-1)
        return redirect('/calo%s/temps' % calo_num)
    else:
        return redirect('/calo25/bkcontrols')


@app.route('/calo<int:calo_num>/gaingrid')
def gain_grid(calo_num):
    if calo_num != 25:
        return render_template('gaingrid.html', calo_num=calo_num, sipm_numbers=range(53, -1, -1), present_sipms=present_sipms, serials=sipm_serials[calo_num-1])
    else:
        return redirect('/calo25/bkcontrols')


@app.route('/calo<int:calo_num>/preview', methods=['POST'])
def preview_gains(calo_num):
    try:
        filestr = request.files['file'].read().decode('utf-8')
    except UnicodeDecodeError:
        return render_template('badfile.html', calo_num=calo_num)
    try:
        gain_map = json.loads(filestr)
    except:
        return render_template('badfile.html', calo_num=calo_num)
    file_present_sipms = [False for i in range(54)]
    new_gains = [0 for i in range(54)]
    for sipm_num in range(54):
        if 'sipm%i' % sipm_num in gain_map:
            file_present_sipms[sipm_num] = True
            new_gains[sipm_num] = gain_map['sipm%i' % sipm_num]
    return render_template('previewgains.html', calo_num=calo_num, sipm_numbers=range(53, -1, -1), present_sipms=file_present_sipms, gains=new_gains, filename=request.files['file'].filename)


@app.route('/calo<int:calo_num>/sipm<int:sipm_num>')
def sipm_graph(calo_num, sipm_num):
    if present_sipms[sipm_num]:
        return render_template('singlesipm.html', calo_num=calo_num, num=sipm_num, serial=sipm_serials[calo_num-1][sipm_num])
    else:
        return render_template('notfound.html', calo_num=calo_num)


@app.route('/calo<int:calo_num>/sipm<int:sipm_num>_<string:next_str>')
def sipm_graph_next(calo_num, sipm_num, next_str):
    if sipm_num >= 0 and sipm_num < 54:
        if next_str == 'next':
            try:
                sipm_num = next(
                    dropwhile(lambda i: i <= sipm_num or not present_sipms[i], range(sipm_num, 54)))
            except StopIteration:
                return render_template('notfound.html', calo_num=calo_num)
            return redirect('/calo%i/sipm%i' % (calo_num, sipm_num))
        elif next_str == 'prev':
            try:
                sipm_num = next(
                    dropwhile(lambda i: i >= sipm_num or not present_sipms[i], range(sipm_num, -1, -1)))
            except StopIteration:
                render_template('notfound.html', calo_num=calo_num)
            return redirect('/calo%i/sipm%i' % (calo_num, sipm_num))
    else:
        return render_template('notfound.html', calo_num=calo_num)


@app.route('/calo<int:calo_num>/gainfile_<string:filename>')
def deliver_gain_file(calo_num, filename):
    gain_dict = OrderedDict()
    gain_dict[
        'what'] = 'sipm gain settings saved for calo %i, from SiPMometer' % calo_num
    gain_dict['when'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(54):
        if present_sipms[i]:
            gain_dict['sipm%i' % i] = int(get_gain(calo_num - 1, i))
    response = make_response(
        json.dumps(gain_dict, indent=4, separators=(',', ': ')))
    if not filename.endswith('.json'):
        filename += '.json'
    response.headers[
        'Content-Disposition'] = "attachment; filename=%s" % filename
    return response


@app.route('/calo<int:calo_num>/gaintable')
def gaintable(calo_num):
    return render_template('gaintable.html', calo_num=calo_num, table=gain_table)


@app.route('/calo<int:calo_num>/bkcontrols')
def bkcontrols(calo_num):
    if (calo_num != 25):
        return render_template('bkcontrols.html', calo_num=calo_num, bks=range(1, 5))
    else:
        return render_template('bkcontrols.html', calo_num=calo_num, bks=range(1, 2))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('notfound.html', calo_num=1), 40


@socketio.on('all gains')
def all_gains(msg):
    calo = msg['calo'] - 1
    for i in range(54):
        if 'sipm%i' % i in sipm_maps[calo]:
            emit('sipm gain', {'gain': get_gain(
                calo, i), 'num': str(i), 'calo': calo+1})


@socketio.on('all temps')
def all_temps(msg):
    calo = msg['calo'] - 1
    for i in range(54):
        if 'sipm%i' % i in sipm_maps[calo]:
            emit('sipm temp', {'temp': get_temp(
                calo, i), 'num': str(i), 'calo': calo+1})


@socketio.on('single gain')
def single_gain(msg):
    num = int(msg['num'])
    calo = int(msg['calo']) - 1
    if 'sipm%i' % num in sipm_maps[calo]:
        emit('sipm values', {'gain': get_gain(calo, num), 'temp': get_temp(
            calo, num), 'num': num, 'calo': calo+1})


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
    try:
        calo = int(msg['calo']) - 1
    except ValueError:
        return
    if present_sipms[sipm_num]:
        set_gain(calo, sipm_num, new_gain)
        emit('sipm values', {'gain': get_gain(calo, sipm_num), 'temp': get_temp(
            calo, sipm_num), 'num': sipm_num, 'calo': calo+1})


@socketio.on('set all gains')
def set_all_gains(msg):
    calo = msg['calo'] - 1
    try:
        new_gain = int(msg['new_gain'])
    except ValueError:
        return
    for sipm_num in range(54):
        if present_sipms[sipm_num]:
            set_gain(calo, sipm_num, new_gain)
            emit('sipm gain', {'gain': get_gain(
                calo, sipm_num), 'num': sipm_num, 'calo': calo+1})


@socketio.on('set these gains')
def set_these_gains(msg):
    calo = msg['calo'] - 1
    gain_dict = msg['gains']
    for sipm_num in range(54):
        if present_sipms[sipm_num] and 'sipm%i' % sipm_num in gain_dict:
            set_gain(calo, sipm_num, int(gain_dict['sipm%i' % sipm_num]))


@socketio.on('bk status')
def bk_status(msg):
    calo = msg['calo'] - 1
    last_bk = 2 if calo == 24 else 5
    for bk in range(1, last_bk):
        if bk is not None:
            emit('bk status', query_bk_status(calo, bk), broadcast=True)


@socketio.on('caen status')
def caen_status():
    emit('caen status', query_caen_status(), broadcast=True)


@socketio.on('new voltage pt')
def new_voltage_pt(msg):
    bk = int(msg['num'])
    calo = int(msg['calo']) - 1
    new_setting = None
    try:
        new_setting = float(msg['new setting'])
    except ValueError:
        return
    if bk is not None and 0.0 <= new_setting <= 72.0 and 0 <= calo <= 24:
        bkbeagles[calo].bk_set_voltage(bk, float(msg['new setting']))
        emit('bk status', query_bk_status(calo, bk))


@socketio.on('new caen voltage')
def new_caen_volt(msg):
    chan = int(msg['chan'])
    new_setting = None
    try:
        new_setting = float(msg['new setting'])
    except ValueError:
        return
    sipmbeagles[24].arbitrary_command(
        'caenHV setvolt {0} {1:.1f}'.format(chan, new_setting))
    emit('caen status', query_caen_status())


@socketio.on('toggle bk power')
def toggle_bk_power(msg):
    bk = int(msg['num'])
    calo = int(msg['calo']) - 1
    if bk is not None and 0 <= calo <= 23:
        if msg['on']:
            bkbeagles[calo].bk_power_on(bk)
        else:
            bkbeagles[calo].bk_power_off(bk)
            emit('bk status', query_bk_status(calo, bk))


@socketio.on('toggle caen power')
def toggle_caen_power(msg):
    chan = int(msg['chan'])
    if msg['on']:
        sipmbeagles[24].arbitrary_command('caenHV turnon {}'.format(chan))
    else:
        sipmbeagles[24].arbitrary_command('caenHV turnoff {}'.format(chan))
    emit('caen status', query_caen_status())


@socketio.on('reload calo settings')
def reload_handler(msg):
    response = 'failed'
    try:
        response = reload_calo_settings(msg['calo'], msg['run'])
    except ValueError:
        pass
    emit('reload response', response)


def query_bk_status(calo, bk):
    status = {'num': str(bk), 'calo': calo+1}
    status['outstat'] = bkbeagles[calo].bk_output_stat(bk)
    status['voltage'] = bkbeagles[calo].bk_read_voltage(bk)
    status['current'] = bkbeagles[calo].bk_read_currlim(bk)
    status['measvolt'] = bkbeagles[calo].bk_measure_voltage(bk)
    status['meascurr'] = bkbeagles[calo].bk_measure_current(bk)
    return status


def query_caen_status():
    caen_beagle = sipmbeagles[24]
    status_list = []
    for chan in range(4):
        status = {}
        try:
            status_bits = int(caen_beagle.arbitrary_command(
                'caenHV stat {}'.format(chan)))
        except ValueError:
            status_bits = 0
        status['outstat'] = status_bits % 2
        status['voltage'] = caen_beagle.arbitrary_command(
            'caenHV readvolt {}'.format(chan))
        status['meascurr'] = caen_beagle.arbitrary_command(
            'caenHV readcurr {}'.format(chan))
        status_list.append(status)
    return status_list


def get_gain(calo, sipm_num):
    if present_sipms[sipm_num]:
        sipm_dict = sipm_maps[calo]['sipm%i' % sipm_num]
        board_num = sipm_dict['board']
        chan_num = sipm_dict['chan'] - 1
        try:
            return sipmbeagles[calo].read_gain(board_num, chan_num)
        except IndexError:
            return None


def get_temp(calo, sipm_num):
    if present_sipms[sipm_num]:
        sipm_dict = sipm_maps[calo]['sipm%i' % sipm_num]
        board_num = sipm_dict['board']
        chan_num = sipm_dict['chan'] - 1
        try:
            return sipmbeagles[calo].read_temp(board_num, chan_num)
        except IndexError:
            return None


def set_gain(calo, sipm_num, new_gain):
    if present_sipms[sipm_num] and (0 <= new_gain <= 80):
        sipm_dict = sipm_maps[calo]['sipm%i' % sipm_num]
        board_num = sipm_dict['board']
        chan_num = sipm_dict['chan'] - 1
        try:
            return sipmbeagles[calo].set_gain(board_num, chan_num, new_gain)
        except IndexError:
            return None


def fill_sipm_serials(calo_num):
    del sipm_serials[calo_num][:]
    for sipm_num in range(54):
        if present_sipms[sipm_num]:
            sipm_dict = sipm_maps[calo_num]['sipm%i' % sipm_num]
            board_num = sipm_dict['board']
            chan_num = sipm_dict['chan'] - 1
            serial = sipmbeagles[calo_num].read_mem(board_num, chan_num)
            try:
                sipm_serials[calo_num].append(int(serial.split()[0]))
            except:
                sipm_serials[calo_num].append(None)
        else:
            sipm_serials[calo_num].append(None)


if __name__ == '__main__':
    for calo in range(24):
        sipm_serials[calo] = ['unitialized' for i in range(54)]
    socketio.run(app, host='0.0.0.0')
