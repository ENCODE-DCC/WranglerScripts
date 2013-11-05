#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''GET an ENCODE JSON schema and print a useful list of properties, perhaps tab-delimited for a spreadsheet header'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path

EPILOG = '''Examples:

Print the sorted list of properties for the human-donor schema (using the default server/keypair from the default keypair file):

	%(prog)s human-donor
	%(prog)s human-donors
	%(prog)s human_donor
	%(prog)s human_donors
	%(prog)s human-donor.json

Print the list of submittable replicate properties from submit-dev, tab-delimited

	%(prog)s replicate --key submit-dev --tsv --submittable

diff the biosample schema properties between submit and demo-v

	diff <(%(prog)s biosample --key submit) <(%(prog)s biosample --key demo-v)
'''

'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}

def get_ENCODE(obj_id):
	'''GET an ENCODE object as JSON and return as dict'''
	url = SERVER+obj_id+'?limit=all'
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
	    description=__doc__, epilog=EPILOG,
	    formatter_class=argparse.RawDescriptionHelpFormatter,
	)

	parser.add_argument('collection',
		help="Anything resembling the schema name you want. (E.g. biosamples, biosample, biosample.json, human-donor, human_donor, human-donors, human_donors, etc.)")
	parser.add_argument('--submittable',
		default=False,
		action='store_true',
		help="Show only properties you might want a submitter to submit.")
	parser.add_argument('--tsv',
		default=False,
		action='store_true',
		help="Display the properties as a tab-delimited string, suitable for import into a spreadsheet.")
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

	supplied_name = args.collection

	if supplied_name.endswith('s'):
		schema_name = supplied_name.rstrip('s').replace('-','_') + '.json'
	elif supplied_name.endswith('.json'):
		schema_name = supplied_name
	else:
		schema_name = supplied_name.replace('-','_') + '.json'

	schema_uri = '/profiles/' + schema_name
	object_schema = get_ENCODE(schema_uri)
	headings = []
	for schema_property in object_schema["properties"]:
		if object_schema["properties"][schema_property]["type"] == 'string':
			headings.append(schema_property)
		elif object_schema["properties"][schema_property]["type"] == 'array':
			if object_schema["properties"][schema_property]["items"]["type"] == 'string':
				headings.append(schema_property + ':array')
			else:
				headings.append(schema_property + ':' + object_schema["properties"][schema_property]["items"]["type"] + ':array')
		else:
			headings.append(schema_property + ':' + object_schema["properties"][schema_property]["type"])
	headings.sort()

	exclude_unsubmittable = ['accession', 'uuid', 'schema_version', 'alternate_accessions', 'submitted_by']

	outstring = ""
	for heading in headings:
		if args.submittable and heading in exclude_unsubmittable:
			pass
		else:
			outstring += heading
			if args.tsv:
				outstring += '\t'
			else:
				outstring += '\n'
	print outstring.rstrip()

if __name__ == '__main__':
	main()
