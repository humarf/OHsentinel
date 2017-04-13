#!/usr/bin/python
#:deploy:OHsentinel:/usr/local/bin

#standard imports
import sys
import ConfigParser
import logging
import os

#custom imports
if os.path.isdir("/usr/local/share/OHsentinel"):
	 sys.path.append("/usr/local/share/OHsentinel")
elif os.path.isdir("/usr/share/OHsentinel"):
	sys.path.append("/usr/share/OHsentinel")
try:
	import OHcommons
	import OHssdp
	import OHcustoms
except:
	print 'Could not import OHcli modules. Please check /usr/local/share/OHsentinel and /usr/share/OHsentinel. lxml and tabulate are also required.'
	sys.exit(4)

def init():
	"reading config and parameters"
	config = {}
	devices = {}
	if True:#try:
		conf = ConfigParser.ConfigParser()
		if os.path.isfile('/etc/OHsentinel.conf'):
			conf.read('/etc/OHsentinel.conf')
		else:
			conf.read('./OHsentinel.conf')
	else:#except:
		print 'Could not read config file'
		sys.exit(1)
	if conf.has_section('OHproduct'):
		for item in conf.items('OHproduct'):
			devices['product', item[0]] = item[1]
	if conf.has_section('OHsender'):
		for item in conf.items('OHsender'):
			devices['sender', item[0]] = item[1]
	if conf.has_section('OHradio'):
		config['stations'] = conf.get('OHradio', 'stations').split(',')
	if conf.has_section('fakeradio'):
		for station in conf.items('fakeradio'):
			config['fakeradio', station[0]] = station[1]
	if conf.has_option('resources', 'xmlpath'):
		config['xmlpath'] = conf.get('resources', 'xmlpath')
	else: config['xmlpath'] = '/usr/local/share/OHsentinel/xml'
	if conf.has_option('resources', 'xslpath'):
		config['xslpath'] = conf.get('resources', 'xslpath')
	else: config['xslpath'] = '/usr/local/share/OHsentinel/xsl'
	if conf.has_option('resources', 'logfile'):
		config['logfile'] = conf.get('resources', 'logfile')
	else:
		config['logfile'] = './OHsentinel.log'
	if conf.has_option('resources', 'cmdport'):
		config['cmdport'] = conf.get('resources', 'cmdport')
	else:
		config['cmdport'] = 8891
	if conf.has_option('resources', 'remote'):
		config['remote'] = conf.get('resources', 'remote')
	else:
		config['remote'] = 'http://localhost'
	if conf.has_option('misc', 'xmltagdelimiter'):
		config['xmltagdelimiter'] = conf.get('misc', 'xmltagdelimiter')
	else: config['xmltagdelimiter'] = ';;'
	if conf.has_option('misc', 'maxcolumnwidth'):
		config['maxcolumnwidth'] = conf.getint('misc', 'maxcolumnwidth')
	if conf.has_option('misc', 'standardtags'):
		config['standardtags'] = conf.get('misc', 'standardtags')
	config['searchstring', 'product'] =  "urn:av-openhome-org:service:Product:1"
	config['searchstring', 'sender'] =  "urn:av-openhome-org:service:Sender:1"
	config['searchstring', 'all'] = "ssdp:all"
	config['searchtypes'] = ['product', 'sender', 'all']
	if conf.has_section('customsearch'):
		for st in conf.items('customsearch'):
			config['searchstring', st[0]] = st[1]
			config['searchtypes'].append(st[0])

	"parse arguments"
	args = OHcustoms.set_arguments(None, config['searchtypes'])

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
		log_handler.setFormatter(logging.Formatter('OHsentinel - cli: %(levelname)s - %(message)s'))
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

	logging.debug('Used configuration: ' + str(config))
	logging.debug('Known devices: ' + str(devices))
	return args, config, devices

args, config, devices = init()
logging.debug(args)
if args.mode == 'search':
	OHcommons.search(args, devices, config)
elif args.mode == 'command':
	if args.unit[0] == 'Custom':
		"Process command in custom unit"
		OHcustoms.command(args, devices, config)
	else:
		"Process standard command"
		OHcommons.command(args, devices, config)
elif args.mode == 'explore':
	OHcommons.explore(args, devices, config)
elif args.mode == 'remote':
	OHcommons.remote(args, devices, config)
