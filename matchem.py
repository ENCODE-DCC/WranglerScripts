#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Take a list of strings and match each one to the most likely ENCODE object'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path, pdb

EPILOG = '''Limitations:

Pull strings from an input file, hit against a server

Examples:

	%(prog)s --key submit --infile mikeps_list.tsv > mikeps_list_matches.tsv

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

	parser.add_argument('--key',
		default='default',
		help="The keypair identifier from the keyfile for the server.  Default is --key=default")
	parser.add_argument('--keyfile',
		default=os.path.expanduser("~/keypairs.json"),
		help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
	parser.add_argument('--infile', '-i',
		help="File containing the JSON object as a JSON string.")
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")

	args = parser.parse_args()

	global DEBUG
	DEBUG = args.debug

	key = ENC_Key(args.keyfile,args.key)
	connection = ENC_Connection(key)
	collection = ENC_Collection(connection,'biosamples',frame='object')

	search_string = "(acc112)"

	es_query = {
		"fields": ["embedded.accession", "embedded.biosample_term_name", "embedded.biosample_term_id", \
					"embedded.description", "embedded.note", "embedded.notes", "embedded.organ_slims"],
		"query": {		
			"fuzzy_like_this": {
				"fields": ["embedded.biosample_term_name"],
				"like_text": search_string,
				"ignore_tf": True,
				"min_similarity": 0.5
			}
		}
	}

	'''
	es_query = {
		"query": {
			"more_like_this": {
				"fields": ["embedded.biosample_term_name"],
				"like_text": search_string,
				"min_term_freq" : 1
			}
		}
	}
	'''
	'''
	es_query = {
		"fields": ["embedded.accession", "embedded.biosample_term_name", "embedded.biosample_term_id", \
					"embedded.description", "embedded.note", "embedded.notes", "embedded.organ_slims"],
		"query": {
			"term": {"embedded.biosample_term_name": search_string }
		}
	}
	'''

	es_result = collection.query(es_query)
	print json.dumps(es_result, sort_keys=True, indent=4, separators=(',', ': '))

if __name__ == '__main__':
	main()
