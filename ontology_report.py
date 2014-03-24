#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Report on biosmaple ontology terms, including pulling organ_slims from two servers to compare'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path, pdb

EPILOG = '''Limitations:

Arrays of strings come back with the items quoted, SO NOT SUITABLE FOR DIRECT PATCH back

Examples:

	%(prog)s --key1 submit --key2 ec2.aws > ontology_report.tsv

'''

class ENC_Key:
	def __init__(self, keyfile, keyname):
		keys_f = open(keyfile,'r')
		keys_json_string = keys_f.read()
		keys_f.close()
		keys = json.loads(keys_json_string)
		key_dict = keys[keyname]
		self.authid = key_dict['key']
		self.authpw = key_dict['secret']
		self.server = key_dict['server']
		if not self.server.endswith("/"):
			self.server += "/"

class ENC_Connection:
	def __init__(self, key):
		self.headers = {'content-type': 'application/json'}
		self.server = key.server
		self.auth = (key.authid, key.authpw)

class ENC_Collection:
	def __init__(self, connection, supplied_name, frame='object'):
		if supplied_name.endswith('s'):
			self.name = supplied_name.replace('_','-')
			self.search_name = supplied_name.rstrip('s').replace('-','_')
			self.schema_name = self.search_name + '.json'
		elif supplied_name.endswith('.json'):
			self.name = supplied_name.replace('_','-').rstrip('.json')
			self.search_name = supplied_name.replace('-','_').rstrip('.json')
			self.schema_name = supplied_name
		else:
			self.name = supplied_name.replace('_','-') + 's'
			self.search_name = supplied_name.replace('-','_')
			self.schema_name = supplied_name.replace('-','_') + '.json'
		schema_uri = '/profiles/' + self.schema_name
		self.schema = get_ENCODE(schema_uri, connection)
		self.frame = frame
		search_string = '/search/?format=json&limit=all&type=%s&frame=%s' %(self.search_name, frame)
		collection = get_ENCODE(search_string, connection)
		self.items = collection['@graph']

class ENC_Item:
	def __init__(self, connection, id, frame='object'):
		self.id = id
		self.server = connection.server

		if id.rfind('?') == -1:
			get_string = id + '?'
		else:
			get_string = id + '&'
		get_string += 'frame=%s' %(frame)
		self.json = get_ENCODE(get_string, connection)

def get_ENCODE(obj_id, connection):
	'''GET an ENCODE object as JSON and return as dict'''
	if obj_id.rfind('?') == -1:
		url = connection.server+obj_id+'?limit=all'
	else:
		url = connection.server+obj_id+'&limit=all'
	if DEBUG:
		print "DEBUG: GET %s" %(url)
	response = requests.get(url, auth=connection.auth, headers=connection.headers)
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

	parser.add_argument('--key1',
		default='default',
		help="The keypair identifier from the keyfile for the primary server.  Default is --key=default")
	parser.add_argument('--key2',
		default='default',
		help="The keypair identifier from the keyfile for the secondary server.  Default is --key=default")
	parser.add_argument('--keyfile',
		default=os.path.expanduser("~/keypairs.json"),
		help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")

	args = parser.parse_args()

	global DEBUG
	DEBUG = args.debug

	key1 = ENC_Key(args.keyfile,args.key1)
	key2 = ENC_Key(args.keyfile,args.key2)

	primary_connection = ENC_Connection(key1)
	secondary_connection = ENC_Connection(key2)

	primary_bs_collection = ENC_Collection(primary_connection,'biosamples',frame='object')
	secondary_bs_collection = ENC_Collection(secondary_connection,'biosamples',frame='object')

	object_schema = primary_bs_collection.schema

	columns = [
		('accession','accession',primary_bs_collection),
		('description','description',primary_bs_collection),
		('biosample_type','biosample_type',primary_bs_collection),
		('biosample_term_name','biosample_term_name',primary_bs_collection),
		('biosample_term_id','biosample_term_id',primary_bs_collection),
		('primary:organ_slims','organ_slims',primary_bs_collection),
		('proposed:organ_slims','organ_slims',secondary_bs_collection)
	]

	headstring = ""
	for heading in [col[0] for col in columns]:
		headstring += heading + '\t'
	headstring = headstring.rstrip()
	print headstring

	primary_collection = primary_bs_collection
	
	all_organ_slim_terms = set([])
	for term_list in [obj['organ_slims'] for obj in primary_collection.items]:
		all_organ_slim_terms.update(term_list)

	for primary_object in primary_collection.items:
		accession = primary_object['accession']
		rowstring = ""
		rowvalues = []
		for prop_key, collection in [(col[1], col[2]) for col in columns]:
			if collection == primary_collection:
				obj = primary_object
			else:
				obj = (o for o in collection.items if o['accession']==accession).next()
			if prop_key in obj:
				rowvalues.append(obj[prop_key])
				tempstring = json.dumps(obj[prop_key]).lstrip('"').rstrip('"')
				if tempstring == '[]':
					tempstring = ""
				rowstring += tempstring + '\t'
			elif '.' in prop_key:
				try:
					embedded_key = obj[prop_key.split('.')[0]]
					if '/' in embedded_key:
						embedded_obj = get_ENCODE(embedded_key, primary_connection)
					else:
						embedded_obj = get_ENCODE(prop_key.split('.')[0] + '/' + obj[prop_key.split('.')[0]], primary_connection)
					rowvalues.append(embedded_obj[prop_key.split('.')[1]])
					embedded_value_string = json.dumps(embedded_obj[prop_key.split('.')[1]]).lstrip('"').rstrip('"')
					if embedded_value_string == '[]':
						embedded_value_string = ""
				except KeyError:
					embedded_value_string = ""
					rowvalues.append(None)
				rowstring += embedded_value_string + '\t'
			else:
				rowstring += '\t'
		#various conditions
		if rowvalues[5] == rowvalues[6]: #skip if primary organ slim agrees with proposed
			pass
		elif all(x in all_organ_slim_terms for x in rowvalues[6]): #skip if proposed slim term is in the primary organ slim somewhere
			pass
		else:
			rowstring = rowstring.rstrip()
			print rowstring

if __name__ == '__main__':
	main()
