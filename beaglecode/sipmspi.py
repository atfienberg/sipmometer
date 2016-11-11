import Adafruit_BBIO.GPIO as GPIO
from spidev import SpiDev
import time

# chip select map
# 0: nc
# 1: pga
# 2: temp
# 3: mem

CHIP_MAP = { "nc": 0, "pga": 1, "temp": 2, "mem": 3 }

class SipmSPI:
	def __init__(self, spinum, sipmpins, chippins):			
		self.spi = SpiDev(spinum, 0)
		self.spi.mode = 3
		self.spi.max_speed_hz = 1000000

		self.sipmpins = ['P9_%i' % num for num in sipmpins]			
		self.chippins = ['P9_%i' % num for num in chippins]
		for pin in self.sipmpins + self.chippins:
			GPIO.setup(pin, GPIO.OUT)
			GPIO.output(pin, GPIO.LOW)

	def select_sipm(self, sipm_number):
		for idx, pin_name in enumerate(self.sipmpins):
			if (sipm_number >> idx & 0x1):
				GPIO.output(pin_name, GPIO.HIGH)
			else:
				GPIO.output(pin_name, GPIO.LOW)
        #print("sipm %d selected" % sipm_number)

	def chip_select(self, key):
		chip_num = CHIP_MAP[key]
		for idx, pin_name in enumerate(self.chippins):
			if (chip_num >> idx & 0x1):
				GPIO.output(pin_name, GPIO.HIGH)
			else:
				GPIO.output(pin_name, GPIO.LOW)

	def reset_temperature(self):
		self.spi.xfer2([0xff, 0xff, 0xff, 0xff])
		#self.spi.xfer2([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
		#time.sleep(0.2)
		
		res = self.spi.xfer2([0x40, 0x00]) # read status register
		print("status: 0x%02x" % res[1])

		res = self.spi.xfer2([0x48, 0x00]) # read config register
		print("status: 0x%02x" % res[1])

		res = self.spi.xfer2([0x58, 0x00]) # read ID register
		print("status: 0x%02x" % res[1])

	def setup_temperature(self):
		self.spi.xfer2([0x08, 0x80])
#		time.sleep(0.2)

	def read_temperature(self):
		res = self.spi.xfer2([0x50, 0x00, 0x00])
		#temp = (res[1] << 5 | res[2] >> 3) / 16.0
		temp = (res[1] << 8 | res[2]) / 128.0
		#print("temp: %f deg C" % temp)
		return str(temp)

	def read_gain(self):
		res = self.spi.xfer2([0x83, 0x00])
		gain_read = res[1]
		#print("old gain readout: %d = %f dB" % (gain_read, 26 - gain_read / 4.0))
		return str(gain_read)

	def set_gain(self, gain_value):
		res = self.spi.xfer2([0x03, gain_value])
		res = self.spi.xfer2([0x83, 0x00])
		gain_read = res[1]
		return str(gain_read)

	def check_eeprom_status(self):
		res = self.spi.xfer2([0x05, 0x00])
		print("eeprom status 0x%02x\n" % res[1])

	def read_eeprom_page(self, page):
		page <<= 4
		cmd = [0x03, page] + [0 for i in range(16)]
		res = self.spi.xfer2(cmd)
		int_array = res[2:]
		#utf8 safety
		chr_array = [ ' ' if i==255 else chr(i) for i in int_array]
		print(''.join(chr_array))

	def write_eeprom_page(self, page, msg):
		page <<= 4
		#enable write latch
		self.spi.xfer2([0x06])
		self.check_eeprom_status()
		#write page
		cmd = [0x02, page] + msg
		res = self.spi.xfer2(cmd)
#		print(res)
		self.check_eeprom_status()
		return res

#GPIO.cleanup()
#self.spi.close()


if __name__ == "__main__":

	#sipm_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
	#sipm_list = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	#sipm_list = [8,9,8,9,8,9,8,9,8,9,8,9,8,9,8,9,8,9,8]
	#sipm_list = [9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9]
	#sipm_list = [8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8]
	#sipm_list = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
	sipm_list = [5,6]
	sspi = SipmSPI(1, chippins=[11, 12, 13, 14], sipmpins=[15, 16])
	for sipm in sipm_list:
		print("\n")
		sspi.select_sipm(sipm)
		sspi.chip_select("mem")
		# #check_eeprom_status()
		# #write_eeprom_page(1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
		print(sspi.read_eeprom_page(1))
		time.sleep(0.1)
		sspi.chip_select("pga")
		print(sspi.read_gain())
		print(sspi.set_gain(50))
		time.sleep(0.1)
		sspi.chip_select("temp")
		#reset_temperature()
		#setup_temperature()
		print sspi.read_temperature()
		time.sleep(0.2)

'''
	for step in range(30000):
		temp_readout = []
		for sipm in sipm_list:
			select_sipm(sipm)
			tmp = read_temperature()
			temp_readout.append(tmp)
	
		temp_string = ["%.3f "%(i) for i in temp_readout]
		dump_string = datetime.datetime.now().isoformat() + " "
		dump_string += "".join(temp_string)
		print dump_string	
		time.sleep(20.0)
'''

