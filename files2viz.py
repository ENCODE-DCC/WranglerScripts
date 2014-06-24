#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Take a list of ENCODE files and visualize them'''

import requests
import json
import sys, os.path

EPILOG = '''Examples:

'''

'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}

def get_ENCODE(obj_id):
	'''GET an ENCODE object as JSON and return as dict'''
	if obj_id.rfind('?') == -1:
		url = ENCODED_SERVER+obj_id+'?limit=all'
	else:
		url = ENCODED_SERVER+obj_id+'&limit=all'
	if DEBUG:
		print "DEBUG: GET %s" %(url)
	response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
	if DEBUG:
		print "DEBUG: GET RESPONSE code %s" %(response.status_code)
		try:
			if response.json():
				print "DEBUG: GET RESPONSE JSON"
				print json.dumps(response.json(), indent=4, separators=(',', ': '))
		except:
			print "DEBUG: GET RESPONSE text %s" %(response.text)
	if not response.status_code == 200:
		print >> sys.stderr, response.text
	return response.json()

def processkeys(args):

	keysf = open(args.keyfile,'r')
	keys_json_string = keysf.read()
	keysf.close()
	keys = json.loads(keys_json_string)
	key_dict = keys[args.key]
	global AUTHID
	global AUTHPW
	global ENCODED_SERVER
	if not args.authid:
		AUTHID = key_dict['key']
	else:
		AUTHID = args.authid
	if not args.authpw:
		AUTHPW = key_dict['secret']
	else:
		AUTHPW = args.authpw
	if not args.server:
		ENCODED_SERVER = key_dict['server']
	else:
		ENCODED_SERVER = args.server
	if not ENCODED_SERVER.endswith("/"):
		ENCODED_SERVER += "/"

def flat_one(JSON_obj):
	try:
		return [JSON_obj[identifier] for identifier in \
					['accession', 'name', 'email', 'title', 'uuid', 'href'] \
					if identifier in JSON_obj][0]
	except:
		return JSON_obj

def flat_ENCODE(JSON_obj):
	flat_obj = {}
	for key in JSON_obj:
		if isinstance(JSON_obj[key], dict):
			flat_obj.update({key:flat_one(JSON_obj[key])})
		elif isinstance(JSON_obj[key], list) and JSON_obj[key] != [] and isinstance(JSON_obj[key][0], dict):
			newlist = []
			for obj in JSON_obj[key]:
				newlist.append(flat_one(obj))
			flat_obj.update({key:newlist})
		else:
			flat_obj.update({key:JSON_obj[key]})
	return flat_obj

def pprint_ENCODE(JSON_obj):
	if ('type' in JSON_obj) and (JSON_obj['type'] == "object"):
		print json.dumps(JSON_obj['properties'], sort_keys=True, indent=4, separators=(',', ': '))
	else:
		print json.dumps(flat_ENCODE(JSON_obj), sort_keys=True, indent=4, separators=(',', ': '))

def files2viz(files_to_visualize):
	if DEBUG:
		print "Visualizing"
		print files_to_visualize

	from trackhub import Hub, GenomesFile, Genome, TrackDb, Track
	from trackhub.upload import upload_hub
	HUBHOST = 'http://cherry-vm45.stanford.edu'
	HUBDIR = 'trackhubs'
	USER = 'jseth'
	URLBASE = os.path.join(HUBHOST, HUBDIR)
	EDWBASE = 'http://encodedcc.sdsc.edu/warehouse'
	GENOME = 'hg19'

	hub = Hub(
		hub='Selected_ENCODE_Tracks',
		short_label='Selected_ENCODE_Tracks_short',
		long_label='Selected_ENCODE_Tracks_long',
		email='jseth@stanford.edu')

	genomes_file = GenomesFile()
	genome = Genome(GENOME)
	trackdb = TrackDb()

	for accession in files_to_visualize:
		file_obj = get_ENCODE(accession)
		if DEBUG:
			print file_obj
		if file_obj['file_format'] == 'bigWig':
			track = Track(
				name=accession,
				url=os.path.join(EDWBASE, str(file_obj['download_path'])),
				tracktype='bigWig',
				short_label=accession,
				long_label=accession,
				color='128,0,0',
				visibility='full')
			trackdb.add_tracks([track])

	genome.add_trackdb(trackdb)
	genomes_file.add_genome(genome)
	hub.add_genomes_file(genomes_file)

	results=hub.render()
	if DEBUG:
		print hub
		print '...'
		print genomes_file
		print '...'
		print genome
		print '...'
		print trackdb
	#upload_hub(hub=hub, host=HUBHOST, user=USER) #doesn't seem to work
	import subprocess
	subprocess.call("cd .. && rsync -r trackhub jseth@cherry-vm45.stanford.edu:/www/html/trackhubs", shell=True)
	import webbrowser
	hubfile = str(hub.hub) + '.hub.txt'
	UCSC_url = 'http://genome.ucsc.edu/cgi-bin/hgTracks?udcTimeout=1&db=hg19' + \
				'&hubUrl=' + os.path.join(HUBHOST,HUBDIR,'trackhub',hubfile) #  + \
				#'&hsS_doLoadUrl=submit' + '&hgS_loadUrlName=' + os.path.join(HUBHOST,HUBDIR,'trackhub','session.txt')
	print UCSC_url
	webbrowser.open(UCSC_url)

def main():

	import argparse
	parser = argparse.ArgumentParser(
	    description=__doc__, epilog=EPILOG,
	    formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument('files', metavar='ENCFF', nargs='*',
		default=None,
		help="File(s) to visualize by ENCODE file accession, (default or '-': take list of files from stdin)")
	parser.add_argument('--infile', '-i', metavar='file', nargs='*',
		help="File(s) containing a (possibly multi-line) whitspace-delimited list of ENCODE file accessions")
	parser.add_argument('--server',
		help="Full URL of the server.")
	parser.add_argument('--key',
		default='default',
		help="The keypair identifier from the keyfile.  Default is --key=default")
	parser.add_argument('--keyfile',
		default=os.path.expanduser("~/keypairs.json"),
		help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
	parser.add_argument('--authid',
		help="The HTTP auth ID.")
	parser.add_argument('--authpw',
		help="The HTTP auth PW.")
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")

	args = parser.parse_args()

	processkeys(args)

	global DEBUG
	DEBUG = args.debug

	if args.infile == None:
		infilenames = []
	else:
		infilenames = args.infile
	if args.files == '-':
		infilenames.append('-')
	if infilenames != []:
		import fileinput
		ENCODE_files = []
		for line in fileinput.input(infilenames):
			ENCODE_files.extend(line.split())
	else:
		ENCODE_files = args.files

	result = files2viz(ENCODE_files)

if __name__ == '__main__':
	main()
