#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Take a comma-delimited, double quote-quoted csv and update ENCODE objects appropriately'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path, pdb, csv
import logging

EPILOG = '''Notes:
	Requires comma-delimited, double quote-quoted (for values containing commas or newlines)
	csv's should have a header as below and data rows in the form:

	accession,property1,property2,property3 ...
	ENCBSxyzabc,value1,value2,value3 ...
	...

	The accession must exist and the properties must be in its schema.
	If the property does not exist in the object it is added with the specified value.
	If the property exists in the object, its value is over-written.
	If the property exists and the value is "", the property will be removed altogether.
	Whitespace is stripped from the supplied value.

	Each accession is echo'ed to stdout as the script works on it.

Examples:

	%(prog)s --key www --infile note2notes.csv

'''

class dict_diff(object):
	"""
	Calculate items added, items removed, keys same in both but changed values, keys same in both and unchanged values
	"""
	def __init__(self, current_dict, past_dict):
		self.current_dict, self.past_dict = current_dict, past_dict
		self.current_keys, self.past_keys = [
			set(d.keys()) for d in (current_dict, past_dict)
		]
		self.intersect = self.current_keys.intersection(self.past_keys)

	def added(self):
		diff = self.current_keys - self.intersect
		if diff == set():
			return None
		else:
			return diff

	def removed(self):
		diff = self.past_keys - self.intersect
		if diff == set():
			return None
		else:
			return diff 

	def changed(self):
		diff = set(o for o in self.intersect
				   if self.past_dict[o] != self.current_dict[o])
		if diff == set():
			return None
		else:
			return diff

	def unchanged(self):
		diff = set(o for o in self.intersect
				   if self.past_dict[o] == self.current_dict[o])
		if diff == set():
			return None
		else:
			return diff

	def same(self):
		return self.added() == None and self.removed() == None and self.changed() == None

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

class ENC_Connection(object):
	def __init__(self, key):
		self.headers = {'content-type': 'application/json'}
		self.server = key.server
		self.auth = (key.authid, key.authpw)

class ENC_Collection(object):
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
		self.connection = connection
		self.server = connection.server
		self.schema = get_ENCODE(schema_uri, connection)
		self.frame = frame
		search_string = '/search/?format=json&limit=all&type=%s&frame=%s' %(self.search_name, frame)
		collection = get_ENCODE(search_string, connection)
		self.items = collection['@graph']
		self.es_connection = None

	def query(self, query_dict, maxhits=10000):
		from pyelasticsearch import ElasticSearch
		if self.es_connection == None:
			es_server = self.server.rstrip('/') + ':9200'
			self.es_connection = ElasticSearch(es_server)
		results = self.es_connection.search(query_dict, index='encoded', doc_type=self.search_name, size=maxhits)
		return results

global schemas
schemas = []

class ENC_Schema(object):
	def __init__(self, connection, uri):
		self.uri = uri
		self.connection = connection
		self.server = connection.server
		response = get_ENCODE(uri, connection)
		self.properties = response['properties']

class ENC_Item(object):
	def __init__(self, connection, id, frame='object'):
		self.id = id
		self.connection = connection
		self.server = connection.server
		self.frame = frame

		if id.rfind('?') == -1:
			get_string = id + '?'
		else:
			get_string = id + '&'
		get_string += 'frame=%s' %(frame)
		item = get_ENCODE(get_string, connection)
		self.type = next(x for x in item['@type'] if x != 'item')
		self.properties = item

	def get(self, key):
		try:
			return self.properties[key]
		except KeyError:
			return None

	def sync(self):
		if self.id.rfind('?') == -1:
			get_string = self.id + '?'
		else:
			get_string = self.id + '&'
		get_string += 'frame=%s' %(self.frame)
		on_server = get_ENCODE(get_string, self.connection)
		diff = dict_diff(on_server, self.properties)
		if diff.same():
			logging.info("%s: No changes to sync" %(self.id))
		elif diff.added() or diff.removed(): #PUT
			excluded_from_put = ['schema_version']
			schema_uri = '/profiles/%s.json' %(self.type)
			try:
				schema = next(x for x in schemas if x.uri == schema_uri)
			except StopIteration:
				schema = ENC_Schema(self.connection, schema_uri)
				schemas.append(schema)

			put_payload = {}
			for prop in self.properties:
				if prop in schema.properties and prop not in excluded_from_put:
					put_payload.update({prop : self.properties[prop]})
				else:
					pass
			# should probably return the new object that comes back from the patch
			replace_ENCODE(self.id, self.connection, put_payload)

		else: #PATCH

			excluded_from_patch = ['schema_version', 'accession', 'uuid']
			patch_payload = {}
			for prop in diff.changed():
				patch_payload.update({prop : self.properties[prop]})
			#should probably return the new object that comes back from the patch
			patch_ENCODE(self.id, self.connection, patch_payload)


def get_ENCODE(obj_id, connection):
	'''GET an ENCODE object as JSON and return as dict'''
	if obj_id.rfind('?') == -1:
		url = connection.server+obj_id+'?limit=all'
	else:
		url = connection.server+obj_id+'&limit=all'
	logging.info('GET %s' %(url))

	response = requests.get(url, auth=connection.auth, headers=connection.headers)
	logging.info('GET RESPONSE code %s' %(response.status_code))
	try:
		if response.json():
			logging.info('GET RESPONSE JSON: %s' %(json.dumps(response.json(), indent=4, separators=(',', ': '))))
	except:
		logging.info('GET RESPONSE text %s' %(response.text))
	if not response.status_code == 200:
		logging.warning('GET failure.  Response code = %s' %(response.text))
	return response.json()

def replace_ENCODE(obj_id, connection, put_input):
	'''PUT an existing ENCODE object and return the response JSON
	'''
	if isinstance(put_input, dict):
		json_payload = json.dumps(put_input)
	elif isinstance(put_input, basestring):
		json_payload = put_input
	else:
		logging.warning('Datatype to put is not string or dict.')
	url = connection.server + obj_id
	logging.info('PUT URL : %s' %(url))
	logging.info('PUT data: %s' %(json_payload))
	response = requests.put(url, auth=connection.auth, data=json_payload, headers=connection.headers)
	logging.info('PUT RESPONSE: %s' %(json.dumps(response.json(), indent=4, separators=(',', ': '))))
	if not response.status_code == 200:
		logging.warning('PUT failure.  Response = %s' %(response.text))
	return response.json()

def patch_ENCODE(obj_id, connection, patch_input):
	'''PATCH an existing ENCODE object and return the response JSON
	'''
	if isinstance(patch_input, dict):
	    json_payload = json.dumps(patch_input)
	elif isinstance(patch_input, basestring):
		json_payload = patch_input
	else:
		print >> sys.stderr, 'Datatype to patch is not string or dict.'
	url = connection.server + obj_id
	logging.info('PATCH URL : %s' %(url))
	logging.info('PATCH data: %s' %(json_payload))
	response = requests.patch(url, auth=connection.auth, data=json_payload, headers=connection.headers)
	logging.info('PATCH RESPONSE: %s' %(json.dumps(response.json(), indent=4, separators=(',', ': '))))
	if not response.status_code == 200:
	    logging.warning('PATCH failure.  Response = %s' %(response.text))
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
	parser.add_argument('--key',
		default='default',
		help="The keypair identifier from the keyfile for the server.  Default is --key=default")
	parser.add_argument('--keyfile',
		default=os.path.expanduser("~/keypairs.json"),
		help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
	parser.add_argument('--infile', '-i',
		help="CSV file with metadata to update")
	parser.add_argument('--dryrun',
		default=False,
		action='store_true',
		help="Do everything except save changes")
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")

	args = parser.parse_args()

	global DEBUG
	DEBUG = args.debug
	if DEBUG:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else: # use the defaulf logging level
		logging.basicConfig(format='%(levelname)s:%(message)s')

	key = ENC_Key(args.keyfile,args.key)
	connection = ENC_Connection(key)
	#biosample_collection = ENC_Collection(connection,'biosamples',frame='object')

	with open(args.infile,'rU') as f:
		reader = csv.DictReader(f, delimiter=',', quotechar='"')
		for new_metadata in reader:
			accession = new_metadata.pop('accession')
			print accession
			enc_object = ENC_Item(connection, accession)
			for prop in new_metadata:
				if new_metadata[prop].strip() == "":
					old_value = enc_object.properties.pop(prop,None)
				else:
					enc_object.properties.update({prop : new_metadata[prop]})
			logging.info('Syncing %s' %(accession))
			logging.info('%s' %(json.dumps(enc_object.properties, sort_keys=True, indent=4, separators=(',', ': '))))
			if not args.dryrun:
				enc_object.sync()

if __name__ == '__main__':
	main()
