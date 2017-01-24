import mysql.connector
import json
import sys
from collections import OrderedDict

def main():
    if len(sys.argv) != 2:
        print('requires calo num')
        sys.exit(0)
    calo_num = None
    try:
       calo_num = int(sys.argv[1])       
    except ValueError:
        print('invalid calo num')
        sys.exit(0)
    cnx = mysql.connector.connect(user='gm2_reader', password='gm2_4_reader',
                                  host='fnalmysqldev.fnal.gov',
                                  database='gm2_calorimeter_db', port=3313)
    cursor=cnx.cursor()
    cursor.execute("SELECT calo_xtal_num, breakoutboard, sipm_id FROM gluing_progress WHERE calo_id=%i ORDER BY calo_xtal_num" % calo_num)
    sipm_map = OrderedDict()
    sipm_map['calo_num'] = calo_num
    for (xtal_num, bb, sid) in cursor:
        bb_nums = bb.split('-')
        board_num = int(bb_nums[0])
        chan_num = int(bb_nums[1])
        entry = OrderedDict()
        entry['board'] = board_num
        entry['chan'] = chan_num
        entry['sipm_id'] = sid
        sipm_map['sipm%i' % xtal_num] = entry
    with open('sipmMapping.json', 'w') as f:
        json.dump(sipm_map, f, indent=4, separators=(',', ': '))
    cursor.close()
    cursor=cnx.cursor()


if __name__ == '__main__':
    main()
