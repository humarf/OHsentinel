#!/usr/bin/python
#:deploy:OHsentinel:/usr/local/share/OHsentinel

#standard imports
import sys
import logging
import os
import argparse
import pycurl
from urlparse import urlparse
from StringIO import StringIO 
import time
import socket

#custom imports
import OHcommons
import OHcustoms

#
#argument parser for OHsentinel
#
def set_arguments(changeargs = None, searchtypes=['product']):
	"init parser"
	def commandline_arg(bytestring):
		unicode_string = bytestring.decode(sys.getfilesystemencoding())
		return unicode_string

	parser = argparse.ArgumentParser(description = 'server tool to monitor openhome devices and integrate with openhab')
	parser.add_argument('-l', '--log', action = 'store', nargs = 1, help = 'set logging mode', \
		choices = ['file', 'screen', 'syslog', 'systemd'], default = ['screen'])
	parser.add_argument('--loglevel', action = 'store', nargs = 1, help = 'set logging level', \
		choices = ['debug', 'info', 'warning', 'error', 'critical'], default = ['info'])
	subparsers = parser.add_subparsers(dest='mode', help='select operating mode')
	
	"init subparser for searching"
	parser_search = subparsers.add_parser('openhab', help='search for devices')
	parser_search.add_argument('target', action = 'store', nargs = 1, \
		choices = searchtypes, default = ['product'],\
			help = 'specify device types to search for')
	group_search = parser_search.add_mutually_exclusive_group()
	group_search.add_argument('-u', '--uuid', action = 'store', nargs = 1, help = 'search for specific uuid')
	group_search.add_argument('-n', '--name', action = 'store', nargs = 1, help = 'search for specific name', type=commandline_arg)

	"init subparser for server mode"
	parser_search = subparsers.add_parser('server', help='server mode')

	if changeargs == None:
		args = parser.parse_args()
	else:
		args = parser.parse_args(changeargs)
	return args

def prepare_arguments(mode, name, uuid, extend = None):
	args_skeleton = []
	args_skeleton.append(mode)
	args_skeleton.extend(['product'])
	if uuid == None:
		args_skeleton.extend(['--name', name])
	else: 
		args_skeleton.extend(['--uuid', uuid])
	if extend != None:
		args_skeleton.extend(extend)
	return set_arguments(args_skeleton)

#
#subscription processing
#
def subscribe(action, name, baseurl, eventurl, callback, port, sid = ''):
	"subscribe to event url givend and return sid and time out"
	subscription = {}
	buffer = StringIO()
	locator = urlparse(baseurl)
	if action == 'subscribe':
		header = ['CALLBACK: <' + callback + ':' + port + '>', 'NT: upnp:event', 
			'TIMEOUT: Second-600', 'HOST:' + locator.netloc]
	elif action == 'renew':
		header = ['SID:' + sid, 'TIMEOUT: Second-600', 'HOST:' + locator.netloc]
	logging.debug('header : ' + str(header))
	c = pycurl.Curl()
	c.setopt(c.URL, baseurl + eventurl)
	c.setopt(c.HTTPHEADER, header)
	c.setopt(c.CUSTOMREQUEST, 'SUBSCRIBE')
	c.setopt(c.HEADERFUNCTION, buffer.write)
	try:
		c.perform()
		c.close()
		#logging.debug('Response: ' + buffer.getvalue())
		if '200 OK' in buffer.getvalue():
			logging.info('Subscribed to ' + name + ' on ' + baseurl + eventurl + '.')
			for line in buffer.getvalue().splitlines():
				if line != '':
					item = line.split(':')
					subscription[item[0].lower()] = line[len(item[0]) + 1:].strip()
			logging.debug('subscription response: ' + str(subscription))
			if action == 'subscribe':
				return subscription['sid'], subscription['timeout'].split('-')[1]
			else:
				return True
		else:
			raise ValueError('Could not subscribe ' + name + ' to ' + baseurl + eventurl + '.')
	except  Exception as er:
		logging.error(er)
		if action == 'subscribe':
			return None, None
		else:
			return False

def subscription_handler(descriptions, available_devices, config, units_used, state_vars):
	'initialize subscriptions for all available devices'
	timeouts = []
	for device in available_devices:
		logging.info('Processing ' + device + ' ...')
		if device in units_used.keys():
			for unit in units_used[device]:
				xsl = OHcommons.xsl_prepare('description', config['xslpath'])
				result = OHcommons.xsl_transform(descriptions[device]['xml'], xsl, 'event_url', unit[0])
				if str(result) != '': unit.append(descriptions[device]['baseurl'] + str(result))
				sid, timeout = subscribe('subscribe', device, descriptions[device]['baseurl'], str(result), \
					config['callback'], config['port'])
				if timeout != None:
					timeouts.append(int(timeout))
				if sid != None:
					unit.append(sid)
		logging.info('Processing ' + device + ' finished.')
	logging.debug('units: ' + str(units_used))
	try:
		timeout = min(timeouts) / 2
	except:
		timeout = 300
	logging.debug('timeout: ' + str(timeout))
	logging.info('Initial device search and subscription done. Entering serice loop ...')
	while True:
		for counter in xrange(1, 10):
			time.sleep(int(timeout / 10))
			if config['message'] == 'newdevice':
				config['message'] = ''
				break
		while config['message'] != '':
			logging.info('Subscription handler blocked (' + config['message'] + '). Waiting ...')
			if config['message'] == 'subscription':
				logging.warning('Subscription is blocking itself. Removing block.')
				config['message'] = ''
			if config['message'] == 'newdevice':
				config['message'] = ''
				break
			time.sleep(10)
		config['message'] = 'subscription'
		for device in available_devices:
			logging.info('Processing ' + device + ' ...')
			if device in units_used.keys():
				for unit in units_used[device]:
					if len(unit) > 1:
						if subscribe('renew', device, unit[1], '', '', config['port'], unit[2]):
							logging.info('Subscription for ' + device + ' event url ' + unit[1] + ' renewed.')
						else:
							del unit[1:]
							logging.info('Subscription for ' + device + ' failed. Deleting sid from list.')
					else:
						xsl = OHcommons.xsl_prepare('description', config['xslpath'])
						result = OHcommons.xsl_transform(descriptions[device]['xml'], xsl, 'event_url', unit[0])
						if str(result) != '': unit.append(descriptions[device]['baseurl'] + str(result))
						sid, timeout = subscribe('subscribe', device, descriptions[device]['baseurl'], str(result), \
							config['callback'], config['port'])
						if timeout != None:
							timeouts.append(int(timeout))
						if sid != None:
							unit.append(sid)
			logging.info('Processing ' + device + ' finished.')
			timeouts = list(set(timeouts))
			try:
				timeout = min(timeouts) / 2
			except:
				timeout = 300
			logging.debug('timeout: ' + str(timeout))
		logging.info('Subscription loop done. Timeout: ' + str(timeout) + '.')
		config['message'] = ''
	return

def search(config, devices):
	'search all products in config given and return descriptions'
	available_devices = []
	descriptions = {}
	for product, device in devices:
		if product == 'product':
			logging.debug('search for device: ' + device + ' ' + devices[product, device])
			args = prepare_arguments('openhab', device, devices[product, device])
			logging.debug(args)
			keep_going = True
			result = OHcommons.search(args, devices, config, keep_going)
			if result != None:
				descriptions[device] = result
				available_devices.append(device)
	logging.info('Devices found: ' + str(available_devices) + '.')
	return descriptions, available_devices

def device_handler(config, devices, descriptions, available_devices, units_used):
	logging.info('Device handler started. Entering service loop ...')
	while True:
		time.sleep(60)
		while config['message'] != '':
			logging.info('Device handler blocked (' + config['message'] + '). Waiting ...')
			if config['message'] == 'device':
				logging.warning('Device is blocking itself. Removing block.')
				config['message'] = ''
			time.sleep(10)
		config['message'] = 'device'
		for product, device in devices:
			if product == 'product':
				logging.debug('search for device: ' + device + ' ' + devices[product, device])
				args = prepare_arguments('openhab', device, devices[product, device])
				logging.debug(args)
				keep_going = True
				result = OHcommons.search(args, devices, config, keep_going)
				if result != None:
					if device not in available_devices:
						descriptions[device] = result
						available_devices.append(device)
						logging.info('New device ' + device + ' added to list of available devices.')
						config['message'] = 'newdevice'
				else:
					if device in available_devices:
						available_devices.remove(device)
						logging.info('Device ' + device + ' now offline. Deleting from list of available devices.')
						if device in units_used.keys():
							for unit in units_used[device]:
								try:
									logging.info('Delete subscription for ' + device + ' and event url ' + unit[1] + '.')
									del unit[1:]
								except:
									logging.warning('Subscription for ' + device + ' was already deleted.')
						del descriptions[device]
		logging.info('Service loop done. Available devices: ' + str(available_devices) + '.')
		if config['message'] == 'device': config['message'] = ''
	return

def parse_event(text, action, state_var, path):
	xml = OHcommons.xml_prepare(text, '', 'string')
	xsl = OHcommons.xsl_prepare('OHevent', path)
	result = OHcommons.xsl_transform(xml, xsl, action, state_var)
	return str(result)

def send2openhab(item, value, url):
	url = url + '/rest/items/' + item + '/state'
	header = ['Content-Type: text/plain']
	logging.debug('Header: ' + str(header))
	logging.info('Updating item ' + item + ' to ' + value)
	buffer = StringIO()
	c = pycurl.Curl()
	c.setopt(c.URL, url)
	c.setopt(c.HTTPHEADER, header)
	c.setopt(c.CUSTOMREQUEST, 'PUT')
	c.setopt(c.POST, 1)
	c.setopt(c.POSTFIELDS, value)
	c.setopt(c.HEADERFUNCTION, buffer.write)
	c.perform()
	c.close()
	logging.debug('Response: ' + buffer.getvalue())
	if 'HTTP/1.1 200 OK' in buffer.getvalue():
		logging.debug('openhab successful: ' + item + '=' + value)
	else:
		logging.error('Sending value ' + value + ' to openhab item ' + item + ' not successful.')
	return

def wait_message_completion(notification, length, connection):
	for i in xrange(1, 10):
		time.sleep(0.1)
		notification = notification + connection.recv(length - len(notification))
		logging.info('message delayed')
		if len(notification) >= length: break
	return notification

def listen2port(sock):
	notification = ''
	header_str = ''
	length_str = ''

	try:
		conn, addr =  sock.accept()
		logging.debug("incoming connection")
		conn.setblocking(1)
		i = 1
		while True: 
			char = conn.recv(1)
			header_str = header_str + char
			i = i + 1
			if '\r\n\r\n' in header_str:
				break
			if i == 999: 
				logging.error( 'header missed')
				break
		header = {}
		for line in header_str.splitlines():
			if line == '': continue
			fields = line.split(':')
			try:
				header[fields[0].lower()] = line[len(fields[0]) + 1:].strip()
			except:
				pass
		logging.debug('raw header: ' + header_str)
		logging.debug('parsed header: ' + str(header))
		if 'content-length' in header.keys():
			length = int(header['content-length'])
			logging.debug('content length given: ' + header['content-length'])
			notification = conn.recv(length)
			if len(notification) < length:
				notification = wait_message_completion(notification, length, conn)
		elif 'transfer-encoding' in header.keys():
			if header['transfer-encoding'] == 'chunked':
				logging.debug('content is chunked')
				length = -1
				while length != 0:
					'read data chunk wise'
					length_str = ''
					char = ' '
					while ord(char) != 10:
						'reading chunk size'
						char = conn.recv(1)
						length_str = length_str + char 
					length_str = length_str.strip(' \t\n\r')
					length = int(length_str, 16)
					logging.debug('length: 0x' + length_str + '=' + str(length))
					notification = notification + conn.recv(length)
					if len(notification) < length:
						notification = wait_message_completion(notification, length, conn)

					'eat CRNL finishing the chunk'
					conn.recv(2)
				logging.debug('last chunk signaled')
			else:
				logging.error('cannot handle transfer-encoding: ' + header['transfer-encoding'])
		else:
			logging.error('neither content-length nor transfer-encoding defined')
		conn.sendall(r'''HTTP/1.1 200 OK
Content-Type: text/plain

''')
		conn.close()
		if len(notification) < length: 
			raise ValueError('Event message incomplete, not handling event.')
			notification = ''
		return header, notification
	except Exception as er:
		logging.error(er)
		return None, None


def command_handler(config, devices, descriptions, available_devices):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.settimeout(600)
	sock.bind(('',int(config['cmdport'])))
	sock.listen(5)
	logging.debug("command socket is set up")
	
	while True:
		header, command = listen2port(sock)
		if command != None:
			logging.info('Command received: ' + command)
			args_command = command.split(' ')
			if args_command[0] == 'command':
				try:
					args = OHcustoms.set_arguments(args_command)
					unit = args.unit[0]
					name = args.name[0]
					if name in available_devices:
						if unit != 'Custom':
							OHcommons.command(args, devices, config, False, descriptions[name])
						else:
							OHcustoms.command(args, devices, config, descriptions[name])
					else:
						logging.warning('Command for device ' + name + ' received but not available - skipping.')
				except Exception as er:
					logging.error(er)
			else:
				logging.warning('Message received was no command - skipping.')
		else:
			if header != None: logging.warning('Received None as body - skipping. Header: ' + str(header))
			else: logging.warning('Received None as header and body - skipping.')
