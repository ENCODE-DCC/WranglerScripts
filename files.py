#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Work on ENCODE files'''

import requests
import json
import sys, os.path

EPILOG = '''Examples:

'''

'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}
ENCODED_SERVER = 'https://www.encodedcc.org'
AUTHID = '***REMOVED***'
AUTHPW = '***REMOVED***'
DEBUG = False

def get_ENCODE(obj_id, frame='object'):
	'''GET an ENCODE object as JSON and return as dict'''
	if obj_id.rfind('?') == -1:
		url = ENCODED_SERVER+obj_id+'?limit=all&frame=%s' %(frame)
	else:
		url = ENCODED_SERVER+obj_id+'&limit=all&frame=%s' %(frame)
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

def main():
	response = get_ENCODE('/search/?type=file')
	files = response['@graph']
	print len(files)
	file_formats = {}
	for file_obj in files:
		file_format = file_obj['file_format']
		output_type = file_obj['output_type']
		#print "%s %s" %(file_format, output_type)
		if file_format in file_formats:
			if output_type in file_formats[file_format]:
				file_formats[file_format][output_type] += 1
			else:
				file_formats[file_format].update({output_type : 1})
		else:
			file_formats.update({file_format : {output_type : 1}})
	pprint_ENCODE(file_formats)
if __name__ == '__main__':
	main()
