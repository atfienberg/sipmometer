# Reload a calo or all calos PGA and bias settings to what they were
# at a given run, or the most recent run.
#
# This information is retrieved from ODB saved in the MC1 postgresql database
#
# Aaron Fienberg
# April 2017

import psycopg2
import sys
import json
from beagle_class import Beagle


def reload_single_calo(odb, calo_num):
    if not 0 < calo_num < 25:
        print('invalid calo num: {}'.format(calo_num))
        sys.exit(0)
    beagle_comm = Beagle('tcp://192.168.{}.21:6669'.format(calo_num))
    hardware_dir = odb['Equipment']['CaloSC{:02d}'.format(calo_num)][
        'Hardware']
    failure = False

    for odb_key in hardware_dir:
        old_vals = hardware_dir[odb_key]
        if odb_key.startswith('BK'):
            bk_num = int(odb_key.replace('BK', ''))
            set_pt = float(old_vals['Voltage Set Point (V)'])
            reply = beagle_comm.bk_set_voltage(bk_num, set_pt)
            if float(reply) != set_pt:
                print('failed voltage set for {0}, got reply {1}'.format(
                    odb_key, reply))
                failure = True

        elif odb_key.startswith('SiPM'):
            sipm_num = int(odb_key.replace('SiPM', ''))
            board_num = int(old_vals['Breakout Board Number'])
            chan_num = int(old_vals['Breakout Board Channel'])-1
            gain = int(old_vals['Gain'])
            reply = beagle_comm.set_gain(board_num, chan_num, gain)
            if int(reply) != gain:
                print('failed gain setting for {0}, got reply {1}'.format(
                    odb_key, reply))
                failure = True

    return 'success' if not failure else 'failure'


def get_most_recent_run(cnx):
    cursor = cnx.cursor()
    cursor.execute(
        'SELECT run_num FROM gm2daq_odb ORDER BY run_num DESC LIMIT 1')
    run_num = next(cursor)[0]
    cursor.close()
    return run_num


def get_odb(cnx, run_num):
    cursor = cnx.cursor()
    cursor.execute(
        'SELECT json_data FROM gm2daq_odb WHERE run_num={}'.format(run_num))
    odb = None
    try:
        odb = next(cursor)[0]
    except StopIteration:
        print('run {} is not in the database!'.format(run_num))
    cursor.close()

    if odb is not None:
        return odb
    sys.exit(0)


def reload_calo_settings(calo, run_num):
    '''calo can be an integer, or 'all' for all calos
    run_num can be an integer or 'last' for most recent'''
    dbconf = None
    with open('config/dbconnection.json', 'r') as conf_file:
        dbconf = json.load(conf_file)

    cnx = psycopg2.connect(user=dbconf['user'], host=dbconf['host'],
                           database=dbconf['dbname'], port=dbconf['port'])

    if run_num == 'last':
        run_num = get_most_recent_run(cnx)
        print('most recent run in DB: {}'.format(run_num))

    # make sure run_num is an int (exception thrown here otherwise)
    run_num = int(run_num)

    odb = get_odb(cnx, run_num)
    cnx.close()

    calo_nums = None
    if calo == 'all':
        calo_nums = range(1, 25)
    else:
        calo_nums = [int(calo)]

    success = True
    for calo_num in calo_nums:
        if reload_single_calo(odb, calo_num) == 'success':
            fstr = 'successfully reloaded settings from run {0} for calo {1}'
            print(fstr.format(
                run_num, calo_num))            
        else:
            success = False
    
    return 'success' if success else 'failed, try script manually for details'

def main():
    if len(sys.argv) < 3:
        print(
            'Usage: reload_calo.py [calo_num] [run_num] '
            + ' (calo_num can be all to do all calos,'
            + ' run_num can be last to use the latest run)')
        sys.exit(0)
    reload_calo_settings(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
