import json
from collections import OrderedDict

def main():
	smap = None
	with open('sipmMapping.json', 'r') as f:
		smap = json.load(f)
	newSmap = OrderedDict()
	for i in xrange(54):
		key = 'sipm%i' % i
		val = smap[key]
		board = val / 16
		chan = val % 16
		newVal = {};
		newVal['board'] = board
		newVal['chan'] = chan
		newSmap[key] = newVal
	with open('newMapping.json', 'w') as f:
		json.dump(newSmap, f, indent=4, separators=(',', ': '), sort_keys=True)

if __name__ == '__main__':
	main()