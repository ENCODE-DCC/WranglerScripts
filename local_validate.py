#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Validate an ENCODE JSON object'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path

EPILOG = __doc__

'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}

def get_ENCODE(obj_id):
    '''GET an ENCODE object as JSON and return as dict'''
    url = SERVER+obj_id+'?limit=all'
    response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
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

def main():

	import argparse
	parser = argparse.ArgumentParser(
	    description="Validate ENCODE JSON object against the appropriate ENCODE schema", epilog=EPILOG,
	    formatter_class=argparse.RawDescriptionHelpFormatter,
	)

	parser.add_argument('--infile', '-i',
		help="File containing the JSON object as a JSON string.")
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

	if args.infile:
		infile = open(args.infile,'r')
	else:
		infile = sys.stdin

	json_string = infile.read()
	json_object = json.loads(json_string)

	try:
		datatype = json_object.pop('@type')[0]
	except:
		print "No datatype in @type property"
		raise

	schema_uri = '/profiles/' + datatype + '.json'
	object_schema = get_ENCODE(schema_uri)
	schema_fields = dict.fromkeys(object_schema['properties'].keys())

	jsonschema.validate(json_object, object_schema)
	print "Validation passed"

if __name__ == '__main__':
	main()
