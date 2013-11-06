#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''GET an ENCODE collection and output a tsv of all objects and their properties suitable for spreadsheet import'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path

EPILOG = '''Limitations:

Gets all objects, no searching implemented yet.
Bug #822 makes this not work for characterizations, datasets, documents, experiments and software
	(I can write a workaround but only if 822 takes long to fix)
Arrays of strings come back with the items quoted, SO NOT SUITABLE FOR DIRECT PATCH back

Examples:

Dump all the biosamples, with all schema properties, from the default server with default keypair and save to a file

	# be patient, this takes some time to run
	%(prog)s biosamples > biosamples.tsv

Same for human-donors

	%(prog)s human-donors > human-donors.tsv

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

def flat_one(JSON_obj):
	return [JSON_obj[identifier] for identifier in \
				['accession', 'name', 'email', 'title', 'uuid', 'href'] \
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

	parser.add_argument('collection',
		help="The collection to get")
	parser.add_argument('--submittable',
		default=False,
		action='store_true',
		help="Show only properties you might want a submitter to submit.")
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

	global collection
	collection = get_ENCODE(supplied_name)
	collected_items = collection['@graph']

	headstring = ""
	for heading in headings:
		if args.submittable and heading.split(':')[0] in exclude_unsubmittable:
			pass
		else:
			headstring += heading + '\t'
	headstring = headstring.rstrip()
	print headstring

	for obj in [get_ENCODE(item['@id']) for item in collected_items]:
		obj = flat_ENCODE(obj)
		rowstring = ""
		for header in headstring.split('\t'):
			prop_key = header.split(':')[0]
			if prop_key in obj:
				tempstring = json.dumps(obj[prop_key]).lstrip('"').rstrip('"')
				if tempstring == '[]':
					tempstring = ""
				rowstring += tempstring + '\t'
			else:
				rowstring += '\t'
		rowstring = rowstring.rstrip()
		print rowstring

if __name__ == '__main__':
	main()
