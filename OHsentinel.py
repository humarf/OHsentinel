#!/usr/bin/python
#:deploy:OHsentinel:/usr/local/bin

#standard imports
import sys
from ConfigParser import ConfigParser
import logging
import logging.handlers
import os
import os.path
import thread
import socket
import time

#custom imports
if os.path.isdir("/usr/local/share/OHsentinel"):
	 sys.path.append("/usr/local/share/OHsentinel")
elif os.path.isdir("/usr/share/OHsentinel"):
	sys.path.append("/usr/share/OHsentinel")
try:
	import OHcommons
	import OHcustoms
	import OHserver
except:
	print('Could not import OHsentinel modules. Please check /usr/local/share/OHsentinel and /usr/share/OHsentinel. lxml and tabulate are also required.')
	sys.exit(4)

def init():
	class CaseConfigParser(ConfigParser):
		def optionxform(self, optionstr):
			return optionstr

	"read command line arguments"
	args = OHserver.set_arguments()

	"reading config and parameters"
	config = {}
	devices = {}
	state_vars = {}
	units_used = {}
	try:
		conf = CaseConfigParser()
		if os.path.isfile('/etc/OHsentinel.conf'):
			conf.read('/etc/OHsentinel.conf')
		else:
			conf.read('./OHsentinel.conf')
	except:
		print 'Could not read config file'
		sys.exit(1)
	if conf.has_option('resources', 'xmlpath'):
		config['xmlpath'] = conf.get('resources', 'xmlpath')
	else: config['xmlpath'] = '/usr/local/share/ohcli/xml'
	if conf.has_option('resources', 'xslpath'):
		config['xslpath'] = conf.get('resources', 'xslpath')
	else: config['xslpath'] = '/usr/local/share/ohcli/xsl'
	if conf.has_option('resources', 'logfile'):
		config['logfile'] = conf.get('resources', 'logfile')
	else:
		config['logfile'] = './OHsentinel.log'
	if conf.has_option('resources', 'openhab'):
		config['openhab'] = conf.get('resources', 'openhab')
	else:
		logging.error('No openhab url defined.')
	if conf.has_option('resources', 'callback'):
		config['callback'] = conf.get('resources', 'callback')
	else:
		config['callback'] = 'http://localhost'
	if conf.has_option('resources', 'port'):
		config['port'] = conf.get('resources', 'port')
	else:
		config['port'] = 8890
	if conf.has_option('resources', 'cmdport'):
		config['cmdport'] = conf.get('resources', 'cmdport')
	else:
		config['cmdport'] = 8891
	if conf.has_section('OHradio'):
		config['stations'] = conf.get('OHradio', 'stations').split(',')
	if conf.has_section('fakeradio'):
		for station in conf.items('fakeradio'):
			config['fakeradio', station[0]] = station[1]
	if conf.has_option('misc', 'xmltagdelimiter'):
		config['xmltagdelimiter'] = conf.get('misc', 'xmltagdelimiter')
	else: config['xmltagdelimiter'] = ';;'
	if conf.has_option('misc', 'standardtags'):
		config['standardtags'] = conf.get('misc', 'standardtags')
	if conf.has_section('OHsender'):
		for item in conf.items('OHsender'):
			devices['sender', item[0]] = item[1]
	if conf.has_section('OHproduct'):
		for item in conf.items('OHproduct'):
			devices['product', item[0]] = item[1]
	for device in devices.keys():
		if conf.has_section(device[1]):
			units_used[device[1]] = []
			state_vars[device[1]] = []
			for item in conf.items(device[1]):
				state_vars[device[1]].append(map(str.strip, item[1].split(',')))
				if [item[1].split(',')[1].strip()] not in units_used[device[1]]:
					units_used[device[1]].append([item[1].split(',')[1].strip()])
	config['searchstring', 'product'] =  "urn:av-openhome-org:service:Product:1"
	config['searchstring', 'sender'] =  "urn:av-openhome-org:service:Sender:1"
	config['message'] = ''

	"setup logging"
	numeric_level = getattr(logging, args.loglevel[0].upper(), None)
	if args.log == ["screen"]:
		logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')
		logging.debug('logging started')
	elif args.log == ["file"]:
		log_handler = logging.handlers.WatchedFileHandler(config['logfile'])
		log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
		logger = logging.getLogger()
		logger.setLevel(numeric_level)
		logger.addHandler(log_handler)
		logging.debug('logging started')
	elif args.log == ["syslog"]:
		log_handler = logging.handlers.SysLogHandler(address = '/dev/log')
		log_handler.setFormatter(logging.Formatter('OHsentinel - %(levelname)s - %(message)s'))
		logger = logging.getLogger()
		logger.setLevel(numeric_level)
		logger.addHandler(log_handler)
		logging.debug('logging started')
	elif args.log == ["systemd"]:
		from systemd.journal import JournalHandler
		logger = logging.getLogger()
		logger.setLevel(numeric_level)
		logger.addHandler(JournalHandler(SYSLOG_IDENTIFIER='OHsentinel'))
		logging.debug('logging started')

	logging.debug('Config: ' + str(config))
	logging.debug('Devices: ' + str(devices))
	logging.debug('State Variables: ' + str(state_vars))
	logging.debug('Units used: ' + str(units_used))
	return config, devices, state_vars, units_used, args

message = ''
config, devices, state_vars, units_used, args = init()
descriptions, available_devices = OHserver.search(config, devices)
thread.start_new_thread( OHserver.subscription_handler, (descriptions, available_devices, config, units_used, state_vars))
thread.start_new_thread(OHserver.device_handler, (config, devices, descriptions, \
	available_devices, units_used))
thread.start_new_thread(OHserver.command_handler, (config, devices, descriptions, \
	available_devices))

#
#event receiver
#
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.settimeout(600)
sock.bind(('',int(config['port'])))
sock.listen(5)
logging.debug("event socket is set up")

while True:
	header, notification = OHserver.listen2port(sock)
	if header != None and notification != None:
		for device in available_devices:
			if device in units_used.keys():
				for unit in units_used[device]:
					if 'sid' in header.keys():
						if header['sid'] in unit:
							named_vars = OHserver.parse_event(notification, 'var_list', '', config['xslpath'])
							if named_vars[-1:] == ',': named_vars = named_vars[:-1]
							named_vars = named_vars.split(',')
							for state_var in state_vars[device]:
								logging.debug('referred variables: ' + str(named_vars)+ '; to process: ' + state_var[0])
								if state_var[0] in named_vars:
									value = OHserver.parse_event(notification, 'value', state_var[0], config['xslpath'])
									value = OHcustoms.openhab_format(state_var[0], state_var[1], str(value), config)
									OHserver.send2openhab(state_var[2], str(value), config['openhab'])
					else: logging.error('Received message without sid.')
	else:
		if header != None: logging.warning('Received None as body - skipping. Header: ' + str(header) + '.')
		else: logging.warning('Received None as header and body - skipping.')

