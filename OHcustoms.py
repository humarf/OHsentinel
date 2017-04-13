#!/usr/bin/python
#:deploy:OHsentinel:/usr/local/share/OHsentinel

#standard imports
import argparse
import sys
import logging
import itertools

#custom imports
import OHcommons

#
#argument parser for ohcli
#
def set_arguments(changeargs = None, searchtypes=['product']):
	"init parser"
	def commandline_arg(bytestring):
		unicode_string = bytestring.decode(sys.getfilesystemencoding())
		return unicode_string

	parser = argparse.ArgumentParser(description = 'command line tool to operate and search openhome devices')
	parser.add_argument('-l', '--log', action = 'store', nargs = 1, help = 'set logging mode', \
		choices = ['file', 'screen', 'syslog', 'systemd'], default = ['screen'])
	parser.add_argument('--loglevel', action = 'store', nargs = 1, help = 'set logging level', \
		choices = ['debug', 'info', 'warning', 'error', 'critical'], default = ['warning'])
	subparsers = parser.add_subparsers(dest='mode', help='select operating mode')

	"init subparser for searching"
	parser_search = subparsers.add_parser('search', help='search for devices')
	parser_search.add_argument('target', action = 'store', nargs = 1, \
		choices = searchtypes, default = ['product'],\
			help = 'specify device types to search for')
	group_search = parser_search.add_mutually_exclusive_group()
	group_search.add_argument('-u', '--uuid', action = 'store', nargs = 1, help = 'search for specific uuid')
	group_search.add_argument('-n', '--name', action = 'store', nargs = 1, help = 'search for specific name', type=commandline_arg)

	"init subparser for command"
	parser_command = subparsers.add_parser('command', help = 'issue command to OHdevice')
	group_command = parser_command.add_mutually_exclusive_group(required = True)
	group_command.add_argument('-u', '--uuid', action = 'store', nargs = 1, help = 'device uuid')
	group_command.add_argument('-n', '--name', action = 'store', nargs = 1, help = 'device name', type=commandline_arg)
	parser_command.add_argument('unit', action = 'store', nargs = 1, \
		help = 'select OHservice to operate', \
			choices = ['Info', 'Playlist', 'Product', 'Radio', 'Receiver', 'Time', 'Volume', 'Sender', 'Custom'])
	parser_command.add_argument('-t', '--target', action = 'store', nargs = 1, default = ['product'], \
		choices = ['product', 'sender'])
	parser_command.add_argument('-c', '--command', action = 'store', nargs = 1, \
		help = 'specify command', required = True)
	parser_command.add_argument('-i', '--input', action = 'store', nargs = '*', \
		help = 'give input parameters in form param=value')
	parser_command.add_argument('-o', '--output', action = 'store', nargs = '*', \
		help = 'specify output arguments if more than one')

	"init subparser for browsing device"
	parser_explore = subparsers.add_parser('explore', help='explore device')
	group_explore = parser_explore.add_mutually_exclusive_group(required = True)
	group_explore.add_argument('-u', '--uuid', action = 'store', nargs = 1, help = 'device uuid')
	group_explore.add_argument('-n', '--name', action = 'store', nargs = 1, \
		help = 'device name', type=commandline_arg)
	parser_explore.add_argument('-t', '--target', action = 'store', nargs = 1, default = ['product'], \
		choices = ['product', 'sender', 'all'])

	"init subparser for remote service"
	parser_remote = subparsers.add_parser('remote', help='send command to OHsentinel')
	parser_remote.add_argument('-r', '--remotecmd', action = 'store', nargs = 1, required = True, \
		help = 'command string to pass to OHsentinel', type = commandline_arg)

	if changeargs == None:
		args = parser.parse_args()
	else:
		args = parser.parse_args(changeargs)
	return args

#
#custom functions
#
def didl_parse(xml, xmlpath, xslpath, delimiter, standardtags, tags = None, returnresult = None):
	"retrieving audio tags from response xml"
	didl_xml = OHcommons.xml_prepare(xml, xmlpath, 'string')
	didl_xsl = OHcommons.xsl_prepare('didl', xslpath)
	returnstring = None
	if tags == None:
		for tag in standardtags.split(','):
			tagvalue = OHcommons.xsl_transform(didl_xml, didl_xsl, tag)
			if str(tagvalue) == '': tagvalue = '-'
			if returnstring == None:
				returnstring = str(tagvalue)
			else:
				returnstring = returnstring + delimiter + str(tagvalue)
	else:
		for tag in tags:
			tagvalue = OHcommons.xsl_transform(didl_xml, didl_xsl, tag)
			if returnstring == None:
				returnstring = str(tagvalue)
			else:
				returnstring = returnstring + delimiter + str(tagvalue)
	if returnresult == None:
		print returnstring
		return
	else:
		return returnstring

def prepare_arguments(args, unit, extend, uuid = None):
	args_skeleton = []
	args_skeleton.append(args.mode)
	if uuid == None:
		if args.uuid == None: args_skeleton.extend(['--name', args.name[0]])
		else: args_skeleton.extend(['--uuid', args.uuid[0]])
		args_skeleton.extend(['--target', 'product', unit, '-c'])
		args_skeleton.extend(extend)
		return set_arguments(args_skeleton)
	else:
		args_skeleton.extend(['--uuid', uuid])
		args_skeleton.extend(['--target', 'sender', unit, '-c'])
		args_skeleton.extend(extend)
		return set_arguments(args_skeleton)
#
#custom command
#
def command(args, devices, config, description = None):
	if args.command[0] in ['Current', 'Fakeradio', 'NextRadiostation', 'Radiostation', 'SetSender', \
		'SourceText', 'Status', 'ToggleMute', 'TogglePlay', 'TrackParse']:
		"Process custom commands"
		logging.debug('Running custom command ' + args.command[0])
		customcommand = True
		if args.command[0] == 'TrackParse':
			"TrackParse"
			tags = args.output
			args = prepare_arguments(args, 'Info', [ 'Track', '-o', 'Metadata'])
			result = OHcommons.command(args, devices, config, customcommand, description)
			didl_parse(result, config['xmlpath'], config['xslpath'], \
				config['xmltagdelimiter'], config['standardtags'], tags)
		elif args.command[0] == 'TogglePlay':
			"TogglePlay"
			args = prepare_arguments(args, 'Playlist', ['TransportState'])
			result = OHcommons.command(args, devices, config, customcommand, description)
			logging.debug('-----')
			if result in ['Paused', 'Stopped']:
				args = prepare_arguments(args, 'Playlist', ['Play'])
			elif result == 'Playing':
				args = prepare_arguments(args, 'Playlist', ['Pause'])
			OHcommons.command(args, devices, config, customcommand, description)
		elif args.command[0] in ['SourceText', 'Radiostation', 'NextRadiostation']:
			"SourceText Radiostation and NextRadiostation"
			args_backup = args
			args = prepare_arguments(args, 'Product', ['SourceIndex', '-o', 'Value'])
			source_id = OHcommons.command(args, devices, config, customcommand, description)
			logging.debug('-----')
			if args_backup.command[0] == 'SourceText': 
				args = prepare_arguments(args, 'Product', ['Source', '-i', 'Index=' + source_id, '-o', 'Name'])
				source = OHcommons.command(args, devices, config, customcommand, description)
				print source
				return
			elif args_backup.command[0] == 'Radiostation':
				if source_id != '1':
					args = prepare_arguments(args, 'Product', ['SetSourceIndexByName', '-i', 'Value=Radio'])
					OHcommons.command(args, devices, config, False, description)
				args = prepare_arguments(args, 'Radio', ['SetId', '-i', args_backup.input[0], 'Uri='])
				OHcommons.command(args, devices, config, False, description)
				args = prepare_arguments(args, 'Radio', ['Play'])
				OHcommons.command(args, devices, config, False, description)
			elif args_backup.command[0] == 'NextRadiostation':
				args = prepare_arguments(args, 'Radio', ['Id', '-o', 'Value'])
				station = OHcommons.command(args, devices, config, customcommand, description)
				logging.debug('Current Station: ' + station)
				args = prepare_arguments(args, 'Radio', ['TransportState', '-o', 'Value'])
				state = OHcommons.command(args, devices, config, customcommand, description)
				if source_id != '1':
					args = prepare_arguments(args, 'Product', ['SetSourceIndexByName', '-i', 'Value=Radio'])
				if station == '0':
					OHcommons.command(args, devices, config, False, description)
					args = prepare_arguments(args, 'Radio', ['SetId', '-i', 'Value=1', 'Uri='])
					OHcommons.command(args, devices, config, False, description)
				else:
					if source_id == '1' and state == 'Playing':
						ind = config['stations'].index(station)
						if len(config['stations']) <= ind + 1:
							newstation = config['stations'][0]
						else:
							newstation = config['stations'][ind +1]
							logging.debug('Next Station: ' + newstation)
						args = prepare_arguments(args, 'Radio', ['SetId', '-i', 'Value=' + newstation, 'Uri='])
						OHcommons.command(args, devices, config, False, description)
						args = prepare_arguments(args, 'Radio', ['Play'])
						OHcommons.command(args, devices, config, False, description)
					else:
						args = prepare_arguments(args, 'Radio', ['Play'])
						OHcommons.command(args, devices, config, False, description)
		elif args.command[0] == 'ToggleMute':
			"Switch Mute on and off"
			args = prepare_arguments(args, 'Volume', ['Mute', '-o', 'Value'])
			result = OHcommons.command(args, devices, config, customcommand, description)
			if result == '1':
				args = prepare_arguments(args, 'Volume', ['SetMute', '-i', 'Value=0'])
				OHcommons.command(args, devices, config, customcommand, description)
			else:
				args = prepare_arguments(args, 'Volume', ['SetMute', '-i', 'Value=1'])
				OHcommons.command(args, devices, config, customcommand, description)
			logging.debug('-----')
		elif args.command[0] == 'Status':
			"return modified transport state"
			args = prepare_arguments(args, 'Playlist', ['TransportState', '-o', 'Value'])
			result = OHcommons.command(args, devices, config, customcommand, description)
			if result == 'Playing':
				print 'Play'
			elif result == 'Paused':
				print 'Pause'
			else:
				print 'Stop'
			logging.debug('-----')
		elif args.command[0] == 'Fakeradio':
			"emulate Radio Interface"
			customxml = config['fakeradio', args.input[0].split('=')[1]]
			args = prepare_arguments(args, 'Playlist', ['DeleteAll'])
			OHcommons.command(args, devices, config, customcommand, description)
			args = prepare_arguments(args, 'Playlist', ['Insert'])
			OHcommons.command(args, devices, config, customcommand, description, customxml)
			args = prepare_arguments(args, 'Playlist', ['Play'])
			OHcommons.command(args, devices, config, customcommand, description)
			logging.debug('-----')
		elif args.command[0] == 'SetSender':
			ipt = args.input[0].split('=')
			if ipt[0] == 'uuid':
				uuid = ipt[1]
			elif ipt[0] == 'name':
				logging.debug('Try to resolve ' + ipt[1])
				uuid = devices['sender', ipt[1]]
			args_backup = args
			logging.debug(uuid)
			"add current ds to sender group specified by uuid or name"
			args = prepare_arguments(args, 'Sender', ['Metadata', '-o', 'Value'], uuid)
			metadata = OHcommons.command(args, devices, config, customcommand)
			Uri = didl_parse(metadata, config['xmlpath'], config['xslpath'], \
				config['xmltagdelimiter'], config['standardtags'], ['Uri'], 'returnresult')
			args = prepare_arguments(args_backup, 'Receiver', \
				['SetSender', '-i', 'Uri=' + Uri, 'Metadata=' + metadata])
			print args
			OHcommons.command(args, devices, config, customcommand, description)
			args = prepare_arguments(args, 'Receiver', ['Play'])
			OHcommons.command(args, devices, config, customcommand, description)
	else:
		logging.error('Custom command ' + args.command[0] + ' is not supported.')
		sys.exit(5)
	return

def openhab_format(state_var, unit, value, config):
	if state_var == 'TransportState':
		if str(value) == 'Playing': return 'Play'
		elif str(value) == 'Paused': return 'Pause'
		else: return 'Stop'
	elif state_var == 'Metadata':
		if value == '':
			for tag in config['standardtags'].split(','):
				value = value + '-' + config['xmltagdelimiter']
			return value
		return didl_parse(value, config['xmlpath'], config['xslpath'], \
				config['xmltagdelimiter'], config['standardtags'], None, 'returnresult')
	else: return value


