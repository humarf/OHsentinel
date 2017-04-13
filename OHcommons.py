#!/usr/bin/python
#:deploy:OHsentinel:/usr/local/share/OHsentinel

#standard imports
import sys
import socket
from lxml import etree
import pycurl 
from StringIO import StringIO 
from tabulate import tabulate
import logging
from urlparse import urlparse

#custom imports
import OHssdp

#
#  xml processing  
#
def xsl_transform(xml, xsl, parameter, modifier = ''):
	"transforms xml with specified parameter"
	parameter = "'" + parameter + "'"
	modifier = "'" + modifier + "'"
	logging.debug('Parameter: ' + parameter + ', modifier: ' + modifier)
	result = xsl(xml, action = parameter, type = modifier)
	logging.debug(result)
	return result

def xsl_prepare(xslidentifier, path):
	"prepares xsl transformation for further usage"
	xslfile = path + '/' + xslidentifier + '.xsl'
	logging.debug('loading ' + xslfile)
	read = etree.parse(xslfile)
	xslt = etree.XSLT(read)
	return xslt	

def xml_prepare(xmlidentifier, path, type = 'file'):
	"prepares xml file for further usage"
	if type == 'file':
		xmlfile = path + '/' + xmlidentifier + '.xml'
		logging.debug('loading file ' + xmlfile)
		xml = etree.parse(xmlfile)
	elif type == 'string':
		logging.debug('Metadata: ' + xmlidentifier)
		if xmlidentifier != '' and xmlidentifier != None:
			xml = etree.fromstring(xmlidentifier)
		else:
			xml = etree.fromstring('<?xml version="1.0" encoding="utf-8"?><none/>')
	else:
		logging.debug('loading url ' + xmlidentifier)
		xml = etree.parse(xmlidentifier)
	return xml

#
#  helper functions 
#
def enrich_response(description, xsl, location):
	"add missing properties"
	description['uuid'] = str(xsl_transform(description['xml'], xsl, 'uuid'))
	description['name'] = unicode(xsl_transform(description['xml'], xsl, 'friendlyName'))
	description['baseurl'] = str(xsl_transform(description['xml'], xsl, 'URL'))
	description['url'] = location
	if description['baseurl'] == '':
		locator = urlparse(location)
		description['baseurl'] = locator.scheme + '://' + locator.netloc
	if description['baseurl'][-1:] == '/': description['baseurl'] = description['baseurl'][:-1]
	description['devicetype'] = str(xsl_transform(description['xml'], xsl, 'devicetype'))
	return

def formatted_append(description, properties, url, width):
	"adds lines to properties dictionary if max column width is exceeded - for printout purposes only"
	max_lines = 5
	max_length = max(len(description['name']), len(description['uuid']), len(description['devicetype']), len(url))
	logging.debug('max length: ' + str(max_length))
	if max_length <= width:
		properties.append([description['uuid'], description['name'], url, description['baseurl'], description['devicetype']])
	else:
		i = 0
		while i * width < max_length and i <= max_lines:
			left = i * width
			right = (i + 1) * width
			logging.debug('i, left, right: ' + str(i) + ', ' + str(left) + ', ' + str(right))
			properties.append([description['uuid'][left:right], description['name'][left:right], \
				url[left:right], description['baseurl'][left:right], description['devicetype'][left:right]])
			i = i + 1
	return

def service_explore(unit, command, description, xslpath, xmlpath, svc_mode):
	"read basic data from service.xml and build data structure"
	service = {}
	xsl = xsl_prepare('description', xslpath)
	service['namespace'] = str(xsl_transform(description['xml'], xsl, 'service_type', unit))
	service['controlurl'] = str(xsl_transform(description['xml'], xsl, 'controlURL', service['namespace']))
	if service['controlurl'] == '':
		logging.error('Service ' + unit + ' not supported.')
		sys.exit(5)
	service_xml = xml_prepare(description['baseurl'] + str(xsl_transform(description['xml'], \
			xsl, 'service_description', service['namespace'])), xmlpath, 'url')
	service_xsl = xsl_prepare('service', xslpath)
	service['actions'] = str(xsl_transform(service_xml, service_xsl, 'list_actions'))[:-1].split(',')
	if svc_mode == 'cli':
		if command in service['actions']:
			service[command, 'in'] = str(xsl_transform(service_xml, service_xsl, 'in', command))[:-1].split(',')
			service[command, 'out'] = str(xsl_transform(service_xml, service_xsl, 'out', command))[:-1].split(',')
		else:
			logging.error('Command ' + command + ' not supported. In unit ' + unit + ' choose from ' +\
				str(service['actions']) + '.')
			sys.exit(5)
	else:
		for cmd in service['actions']:
			service[cmd, 'in'] = str(xsl_transform(service_xml, service_xsl, 'in', cmd))[:-1].split(',')
			service[cmd, 'out'] = str(xsl_transform(service_xml, service_xsl, 'out', cmd))[:-1].split(',')
	logging.debug('service: ' + str(service))
	return service

#
# soap communication 
#
def send_soap(baseurl, cmdurl, cmdxml, cmd):
	"send soap datagram, parse response and return"
	header = ["Content-Type: text/xml", 'SOAPACTION: ' + '"' + cmd + '"']
	logging.debug('Header: ' + str(header))
	buffer = StringIO()
	buffer_header = StringIO()
	c = pycurl.Curl()
	logging.debug('url: ' + baseurl + str(cmdurl))
	c.setopt(c.URL, baseurl + str(cmdurl))
	c.setopt(c.WRITEDATA, buffer)
	c.setopt(c.HTTPHEADER, header)
	c.setopt(c.HEADERFUNCTION, buffer_header.write)
	c.setopt(c.POST, 1)
	c.setopt(c.POSTFIELDS, etree.tostring(cmdxml))
	logging.debug(etree.tostring(cmdxml))
	c.perform()
	c.close()
	resultxml = etree.fromstring(buffer.getvalue())
	logging.debug('ResponseHeader: ' + buffer_header.getvalue())
	logging.debug('Response: ' + buffer.getvalue())
	return resultxml


#
# operating modes 
#
def search(args, devices, config, keep_going = False):
	"search for devices and return a list or xml"
	description = {}
	searchname = ''
	searchuuid = ''
	xsl = xsl_prepare('description', config['xslpath'])
	properties = [['uuid','name','description', 'baseURL', 'device type']]
	if args.name != None:
		searchname = args.name[0]
		logging.debug('Try to resolve ' + searchname + ' from config ...')
		if (args.target[0], searchname) in devices.keys():
			searchuuid = devices[args.target[0], searchname]
			logging.debug(searchname + ' resolved to: ' + searchuuid)
		else:
			logging.debug(searchname + ' could not be resolved')
	if args.uuid != None:
		searchuuid = args.uuid[0]
	if searchuuid == '':
		responses = OHssdp.discover(config['searchstring', args.target[0]], '')
		for response in responses:
			try:
				logging.debug('---begin description---')
				logging.debug('location')
				logging.debug(response.location)
				logging.debug('service')
				logging.debug(response.st)
				description['xml'] = xml_prepare(response.location, config['xslpath'], 'url')
				enrich_response(description, xsl, response.location)
				if searchname != '':
					logging.debug('compare ' + searchname + ' to ' + description['name'])
					if searchname == description['name']:
						logging.debug(searchname + ' found')
						if args.mode != 'search': return description
						else: properties.append([description['uuid'], description['name'], response.location, description['baseurl'], description['devicetype']])
						logging.debug('---end description---')
						break
					else:
						description = {}
						logging.debug('---end description---')
				else:
					formatted_append(description, properties, response.location, config['maxcolumnwidth'])
					description = {}
					logging.debug('---end description---')
			except:
				logging.error('Could not describe ' + response.location + '.')
				logging.debug('---end description---')
		if args.mode != 'search': return None
		print tabulate(properties, headers = 'firstrow')
	else:
		response = OHssdp.discover(config['searchstring', args.target[0]], searchuuid)
		if response != None:
			description['xml'] = xml_prepare(response.location, config['xslpath'], 'url')
			enrich_response(description, xsl, response.location)
			if args.mode == 'search':
				properties.append([description['uuid'], description['name'], response.location, description['baseurl'], description['devicetype']])
				print tabulate(properties, headers = 'firstrow')
			else:
				return description
		else:
			if keep_going: 
				logging.info(searchuuid + ' not found.')
				return None
			else:
				logging.error(searchuuid + ' not found.')
				sys.exit(3)
	return

def command(args, devices, config, fakecommand = False, description = None, customxml = None):
	def command_prepare(action, command, namespace, cmdxml = None, argument = '', value = ''):
		"create and prepare payload of soap telegram"
		if cmdxml == None:
			cmdxml = xml_prepare('OHCommand', config['xmlpath'])
		cmdxsl = xsl_prepare('OHCommand', config['xslpath'])
		action = "'" + action + "'"
		command = "'" + command + "'"
		namespace = "'" + namespace + "'"
		argument = "'" + argument + "'"
		value = "'" + value + "'"
		cmdxml = cmdxsl(cmdxml, action = action, command = command, namespace = namespace, argument = argument, value = value)
		return cmdxml

	"send a command to OHdevice and return results to stout"
	if description == None:
		svc_mode = 'cli'
		description = search(args, devices, config)
	if description != None:
		svc_mode = 'server'
		
		"prepare command"
		logging.debug('device and description found')
		unit = args.unit[0]
		command = args.command[0]
		logging.debug('unit: ' + unit + ', command: ' + command)
		if unit not in description.keys():
			logging.info("Enrich service " + unit + ".")
			description[unit] = service_explore(unit, command, description, config['xslpath'], config['xmlpath'], svc_mode)
			service = description[unit]
		else:
			logging.info("Service " + unit + " already parsed.")
			service = description[unit]
		if customxml == None:
			cmdxml = command_prepare('create', command, service['namespace'])
			
			"validate arguments"
			if args.input != None:
				for argument in args.input:
					argval = argument.split('=')
					if argval[0] in service[command, 'in']:
						cmdxml = command_prepare('append', command, service['namespace'], \
							cmdxml, argval[0], argument[len(argval[0]) + 1:])
					else: 
						logging.error('For command ' + command + ' input ' + argument + \
						' not supported. Choose from ' + str(service[command, 'in']) + '.')
						sys.exit(5)
			if service[command, 'in'] != None:
				parsedargs = []
				if args.input != None:
					for argument in args.input:
						parsedargs.append(argument.split('=')[0])
				if service[command, 'in'] != None and service[command, 'in'] != ['']:
					for argument in service[command, 'in']:
						if argument in parsedargs:
							logging.debug(argument + ' given')
						else:
							logging.error('Input ' + argument + ' missing. Specify ' + str(service[command, 'in']) + '.')
							sys.exit(5)
		else:
			"use custom xml -> no further validation or processing on xml"
			cmdxml = xml_prepare(customxml, config['xmlpath'])
		"send command"
		result_xml = send_soap(description['baseurl'], service['controlurl'], \
			cmdxml, service['namespace'] + '#' + command)

		"process response"
		if args.output != None:
			if args.output[0] == 'xml': 
				print etree.tostring(result_xml)
				return
		response_xsl = xsl_prepare('OHResponse', config['xslpath'])
		if len(service[command, 'out']) == 1:
			defaultout = str(xsl_transform(result_xml, response_xsl, service[command, 'out'][0], 'string'))
			if fakecommand:
				return defaultout
			else:
				if defaultout != '': print defaultout
		else:
			if args.output != None:
				returnstring = None
				for state in args.output:
					if state in service[command, 'out']:
						value = xsl_transform(result_xml, response_xsl, state, 'string')
						if len(service[command, 'out']) == 1 or len(args.output) == 1:
							returnstring = str(value)
						else:
							if returnstring == None:
								returnstring = state + '=' + str(value)
							else:
								returnstring = returnstring + ' ' + state + '=' + str(value)
						if fakecommand:
							return returnstring
						else:
							print returnstring
					else:
						logging.error('Output ' + state + ' not supported. Choose from ' + \
							str(service[command, 'out']) + '.')
						sys.exit(5)
	else:
		logging.error('Device not found.')
		sys.exit(3)
	return

def explore(args, devices, config):
		description = search(args, devices, config)
		xsl = xsl_prepare('description', config['xslpath'])
		service_list = str(xsl_transform(description['xml'], xsl, 'service_list'))[:-1].split(',')
		attributes = str(xsl_transform(description['xml'], xsl, 'attribute_list'))[:-1].split(',')
		output = [['Device exploration', '', '', '', '']]
		output.append(['##PROPERTY', '##VALUE'])
		for attribute in attributes:
			split = attribute.split('=')
			print len(split[1])
			if len(split[1]) < config['maxcolumnwidth']:
				output.append([split[0], split[1]])
			else:
				output.append([split[0], split[1][0:config['maxcolumnwidth']]])
				output.append(['', split[1][config['maxcolumnwidth'] :]])
		if len(description['url']) < config['maxcolumnwidth']:
			output.append(['description xml:', description['url']])
		else:
			output.append(['description xml:', description['url'][0:config['maxcolumnwidth']]])
			output.append(['', description['url'][config['maxcolumnwidth']:]])
		output.append(['baseURL:', description['baseurl']])
		output.append(['', ''])
		for service in service_list:
			servicetype, serviceurl = service.split('=')
			output.append(['##SERVICE', '##NAME', '##PROPERTY', '##VALUE'])
			output.append(['',servicetype, 'description url', serviceurl])
			output.append(['', '', 'command url', str(xsl_transform(description['xml'], xsl, 'controlURL', servicetype))])
			output.append(['', '', 'event url', str(xsl_transform(description['xml'], xsl, 'event_url', servicetype))])
			xml = xml_prepare(description['baseurl'] + serviceurl, config['xmlpath'], 'url')
			svc_xsl = xsl_prepare('service', config['xslpath'])
			actions = str(xsl_transform(xml, svc_xsl, 'list_actions'))[:-1].split(',')
			output.append(['', ''])
			output.append(['', '##ACTION', '##ARGUMENTS', '##RELATED STATE VARIABLES'])
			for action in actions:
				args_vars_in = str(xsl_transform(xml, svc_xsl, 'in_state_var', action))[:-1].split(',')
				args_vars_out = str(xsl_transform(xml, svc_xsl, 'out_state_var', action))[:-1].split(',')
				if len(args_vars_in) > 0 and args_vars_in != ['']: 
					output.append(['', action, '##IN', '##RELATED STATE VAR'])
					for arg_var in args_vars_in:
						split = arg_var.split('=')
						line = ['', '', split[0], split[1]]
						output.append(line)
				else: output.append(['', action, '##IN - NO PARAMETERS'])
				if len(args_vars_out) > 0 and args_vars_out != ['']: 
					output.append(['', '', '##OUT', '##RELATED STATE VAR'])
					for arg_var in args_vars_out:
						split = arg_var.split('=')
						line = ['', '', split[0], split[1]]
						output.append(line)
				else: output.append(['', '', '##OUT - NO PARAMETERS'])
			output.append(['', ''])
			output.append(['', '##STATE VARIABLES', '##SEND EVENTS', '##DATA TYPE'])
			state_vars = str(xsl_transform(xml, svc_xsl, 'list_variables', 'explore'))[:-1].split(',')
			for state_var in state_vars:
				split = state_var.split('=')
				line = ['']
				for element in split:
					line.append(element)
				output.append(line)
			output.append(['', ''])
		print tabulate(output, headers = 'firstrow')
		return

def remote(args, devices, config):
	"send command to Ohsentinel instance"
	logging.debug('send command to ' + config['remote'] + ':' + config['cmdport'])
	buffer = StringIO()
	buffer_header = StringIO()
	c = pycurl.Curl()
	c.setopt(c.URL, config['remote'] + ':' + config['cmdport'])
	c.setopt(c.WRITEDATA, buffer)
	c.setopt(c.HEADERFUNCTION, buffer_header.write)
	c.setopt(c.POST, 1)
	c.setopt(c.POSTFIELDS, args.remotecmd[0])
	c.perform()
	c.close()
	logging.debug('Response header: ' + buffer_header.getvalue())
	return
