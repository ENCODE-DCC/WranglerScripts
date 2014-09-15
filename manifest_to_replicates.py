#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Take a manifest-file-like csv and create replicate objects if they don't exist'''
EPILOG = '''NOTE: Input file must contain exactly 1 header row.  So delete the line with ##validateManifest version 1.7.
Example:
	cat validated.txt | %(prog)s --key www --dry-run
'''

import requests, json, jsonschema
import sys, os.path, pdb, codecs
import logging
from urlparse import urlsplit, urlunsplit
import csv

HEADERS = {'content-type': 'application/json'}

def get_ENCODE(obj_id):
	'''GET an ENCODE object as JSON and return as dict
	'''
	url = SERVER+obj_id+'?limit=all&frame=embedded'
	#url = SERVER+obj_id
	if DEBUG_ON:
		print "DEBUG: GET %s" %(url)
	response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
	if DEBUG_ON:
		print "DEBUG: GET RESPONSE code %s" %(response.status_code)
		try:
			if response.json():
				print "DEBUG: GET RESPONSE JSON"
				print json.dumps(response.json(), indent=4, separators=(',', ': '))
		except:
			print "DEBUG: GET RESPONSE text %s" %(response.text)
	if not response.status_code == requests.codes.ok:
		response.raise_for_status()
	return response.json()

def patch_ENCODE(obj_id, patch_input):
	'''PATCH an existing ENCODE object and return the response JSON
	'''
	if isinstance(patch_input, dict):
	    json_payload = json.dumps(patch_input)
	elif isinstance(patch_input, basestring):
		json_payload = patch_input
	else:
		print >> sys.stderr, 'Datatype to patch is not string or dict.'
	url = SERVER+obj_id
	if DEBUG_ON:
		print "DEBUG: PATCH URL : %s" %(url)
		print "DEBUG: PATCH data: %s" %(json_payload)
	response = requests.patch(url, auth=(AUTHID, AUTHPW), data=json_payload, headers=HEADERS)
	if DEBUG_ON:
		print "DEBUG: PATCH RESPONSE"
		print json.dumps(response.json(), indent=4, separators=(',', ': '))	
	if not response.status_code == 200:
	    print >> sys.stderr, response.text
	return response.json()

def replace_ENCODE(obj_id, put_input):
	'''PUT an existing ENCODE object and return the response JSON
	'''
	if isinstance(put_input, dict):
	    json_payload = json.dumps(put_input)
	elif isinstance(put_input, basestring):
		json_payload = put_input
	else:
		print >> sys.stderr, 'Datatype to put is not string or dict.'
	url = SERVER+obj_id
	if DEBUG_ON:
		print "DEBUG: PUT URL : %s" %(url)
		print "DEBUG: PUT data: %s" %(json_payload)
	response = requests.put(url, auth=(AUTHID, AUTHPW), data=json_payload, headers=HEADERS)
	if DEBUG_ON:
		print "DEBUG: PUT RESPONSE"
		print json.dumps(response.json(), indent=4, separators=(',', ': '))	
	if not response.status_code == 200:
		print >> sys.stderr, response.text
	print response.text
	return response.json()

def new_ENCODE(collection_id, post_input):
	'''POST an ENCODE object as JSON and return the response JSON
	'''
	if isinstance(post_input, dict):
	    json_payload = json.dumps(post_input)
	elif isinstance(post_input, basestring):
		json_payload = post_input
	else:
		print >> sys.stderr, 'Datatype to post is not string or dict.'
	if DEBUG_ON:
		print "DEBUG: SERVER = %s" %(SERVER)
		print "DEBUG: collection = %s" %(collection_id)
	url = SERVER+collection_id
	if DEBUG_ON:
		print "DEBUG: POST URL : %s" %(url)
		print "DEBUG: POST data:"
		print json.dumps(post_input, sort_keys=True, indent=4, separators=(',', ': '))
	response = requests.post(url, auth=(AUTHID, AUTHPW), headers=HEADERS, data=json_payload)
	if DEBUG_ON:
		print "DEBUG: POST RESPONSE"
		print json.dumps(response.json(), indent=4, separators=(',', ': '))	
	if not response.status_code == 201:
		print >> sys.stderr, response.text
	print "Return object:"
	print json.dumps(response.json(), sort_keys=True, indent=4, separators=(',', ': '))
	return response.json()

def flat_one(JSON_obj):
	return [JSON_obj[identifier] for identifier in \
				['accession', 'name', 'email', 'title', 'uuid', 'href','download'] \
				if identifier in JSON_obj][0]

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

def main():

	import argparse
	parser = argparse.ArgumentParser(
	    description=__doc__, epilog=EPILOG,
	    formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument('--infile', '-i',
	help="Input file.")
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
	parser.add_argument('--dry-run',
		default=False,
		action='store_true',
		help="Report what would be done, but don't do it.")
	parser.add_argument('--post',
		default=False,
		action='store_true',
		help="Write changes to the database.")
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")
	args = parser.parse_args()

	global DEBUG_ON
	DEBUG_ON = args.debug

	global DRY_RUN
	DRY_RUN = args.dry_run
	global POST
	POST = args.post

	keysf = open(args.keyfile,'r')
	keys_json_string = keysf.read()
	keysf.close()
	keys = json.loads(keys_json_string)
	key_dict = keys[args.key]
	global AUTHID
	global AUTHPW
	global SERVER
	if not args.authid:
		AUTHID = key_dict['key']
	else:
		AUTHID = args.authid
	if not args.authpw:
		AUTHPW = key_dict['secret']
	else:
		AUTHPW = args.authpw
	if not args.server:
		SERVER = key_dict['server']
	else:
		SERVER = args.server
	if not SERVER.endswith("/"):
		SERVER += "/"

	with open(args.infile,'r') as infile:
		'''sniff could never figure out the dialect
		print infile.readline()
		infile.seek(0)
		dialect = csv.Sniffer().sniff(infile.readline())
		infile.seek(0)
		manifest_reader = csv.DictReader(infile, dialect)'''
		manifest_reader = csv.DictReader(infile)
		for row in manifest_reader:
			print "%s\t%s\t%s\t%s" %(row['#file_name'], row['experiment'], row['replicate'], row['technical_replicate'])
			experiment = get_ENCODE(row['experiment'])
			print "ENCODEd: %s has replicates %s" %(experiment['accession'], [(replicate['biological_replicate_number'], replicate['technical_replicate_number']) for replicate in experiment['replicates']])
			if (int(row['replicate']), int(row['technical_replicate'])) in [(replicate['biological_replicate_number'], replicate['technical_replicate_number']) for replicate in experiment['replicates']]:
				print "Found it"
			else:
				newrep = {
					"biological_replicate_number": int(row['replicate']),
					"technical_replicate_number": int(row['technical_replicate']),
					"experiment": row['experiment']
				}
				if DRY_RUN or not POST:
					print "dry_run: would post %s" %(newrep)
				elif POST:
					print "Posting: %s" %(newrep)
					newobj = new_ENCODE('replicates',newrep)
					print "Posted: %s" %(newobj)

if __name__ == '__main__':
	main()
