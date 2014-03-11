#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''GET the ENCODE experiment collection and output a tsv of all objects and their properties suitable for spreadsheet import'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path

EPILOG = '''Limitations:

Gets all objects, no searching implemented yet.
Arrays of strings come back with the items quoted, SO NOT SUITABLE FOR DIRECT PATCH back

Examples:

Dump all the experiments, with all schema properties, from the default server with default keypair and save to a file

	# be patient, this takes some time to run
	%(prog)s > biosamples.tsv

'''

'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}

def get_ENCODE(obj_id):
	'''GET an ENCODE object as JSON and return as dict'''
	if obj_id.rfind('?') == -1:
		url = SERVER+obj_id+'?limit=all'
	else:
		url = SERVER+obj_id+'&limit=all'
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

	import argparse
	parser = argparse.ArgumentParser(
	    description=__doc__, epilog=EPILOG,
	    formatter_class=argparse.RawDescriptionHelpFormatter,
	)

	parser.add_argument('--es',
		default=False,
		action='store_true',
		help="Use elasticsearch")
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

	#this script only works for the experiments collection
	supplied_name = 'experiments'

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
			if 'items' in object_schema["properties"][schema_property].keys():
				whateveritscalled = "items"
			elif 'reference' in object_schema["properties"][schema_property].keys():
				whateveritscalled = "reference"
			elif 'url' in object_schema["properties"][schema_property].keys():
				whateveritscalled = "url"
			else:
				print object_schema["properties"][schema_property].keys()
				raise NameError("None of these match anything I know")
			if object_schema["properties"][schema_property][whateveritscalled]["type"] == 'string':
				headings.append(schema_property + ':array')
			else:
				headings.append(schema_property + ':' + object_schema["properties"][schema_property][whateveritscalled]["type"] + ':array')
		else:
			headings.append(schema_property + ':' + object_schema["properties"][schema_property]["type"])
	headings.sort()
	headings.append('award.rfa')
	#this is for experiments only
	headings.append('organism')
	headings.append('organ_slims')

	exclude_unsubmittable = ['accession', 'uuid', 'schema_version', 'alternate_accessions', 'submitted_by']

	if args.es:
		supplied_name = '/search/?format=json&limit=all&type=' + supplied_name
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

	for item in collected_items:
		obj = get_ENCODE(item['@id'])
		# starting here is code to pull the organisms and organ slims for the experiment
		replicates = obj['replicates']
		organism_list = []
		slims_list = []
		for rep in replicates:
			try:
				organism = rep['library']['biosample']['organism']['name']
			except KeyError:
				organism = 'none in rep'
			if organism in organism_list:
				pass
			else:
				organism_list.append(organism)
			try:
				first_slim = rep['library']['biosample']['organ_slims'][0]
			except (KeyError, IndexError):
				first_slim = ''
			if first_slim in slims_list:
				pass
			else:
				slims_list.append(first_slim)

		organism = ''
		if len(organism_list) > 1:
			for org in organism_list:
				organism += org + ','
			organism = organism.rstrip(',')
		elif len(organism_list) == 1:
			organism = organism_list[0]
		else:
			organism = 'no reps'

		slims = ''
		if len(slims_list) > 1:
			for slim in slims_list:
				slims += slim + ','
			slims = slims.rstrip(',')
		elif len(slims_list) == 1:
			slims = slims_list[0]
		else:
			slims = ''

		obj['organism'] = organism
		obj['organ_slims'] = slims
		# end code to pull the organisms for the experiment
		obj = flat_ENCODE(obj)
		rowstring = ""
		for header in headstring.split('\t'):
			prop_key = header.split(':')[0]
			if prop_key in obj:
				tempstring = json.dumps(obj[prop_key]).lstrip('"').rstrip('"')
				if tempstring == '[]':
					tempstring = ""
				rowstring += tempstring + '\t'
			elif '.' in prop_key:
				embedded_obj = get_ENCODE(prop_key.split('.')[0] + '/' + obj[prop_key.split('.')[0]])
				embedded_value_string = json.dumps(embedded_obj[prop_key.split('.')[1]]).lstrip('"').rstrip('"')
				if embedded_value_string == '[]':
					embedded_value_string = ""
				rowstring += embedded_value_string + '\t'
			else:
				rowstring += '\t'
		rowstring = rowstring.rstrip()
		print rowstring

if __name__ == '__main__':
	main()
