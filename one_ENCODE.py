#!/usr/bin/env python
# -*- coding: latin-1 -*-
''' Script to add one ENCODE object from a file or stdin or get one object from an ENCODE server
'''
import requests
import json
import sys
import os.path
from base64 import b64encode
from copy import deepcopy

EPILOG = __doc__

'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}

def get_ENCODE(obj_id):
	'''GET an ENCODE object as JSON and return as dict
	'''
	url = SERVER+obj_id+'?limit=all'
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
	response = requests.patch(url, auth=(AUTHID, AUTHPW), data=json_payload)
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
	response = requests.put(url, auth=(AUTHID, AUTHPW), data=json_payload)
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
	    description="POST, PATCH or PUT one ENCODE JSON object", epilog=EPILOG,
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
	parser.add_argument('--force-put',
		default=False,
		action='store_true',
		help="Force the object to be PUT rather than PATCHed.  Default is False.")
	parser.add_argument('--get-only',
		default=False,
		action='store_true',
		help="Do nothing but get the object and print it.  Default is False.")
	parser.add_argument('--id',
		help="URI for an object"),
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")
	args = parser.parse_args()

	global DEBUG_ON
	DEBUG_ON = args.debug

	if args.get_only:
		GET_ONLY = True
	else:
		GET_ONLY = False

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

	new_object = False
	if args.id:
		GET_ONLY = True
		print "Taking id to get from --id"
		new_json = {}
		uuid_response = {}
		accession_response = {}
		try:
			id_response = get_ENCODE(args.id)
		except:
			id_response = {}
			new_object = True
	else:
		if args.infile:
			infile = open(args.infile,'r')
		else:
			infile = sys.stdin

		new_json_string = infile.read()
		new_json = json.loads(new_json_string)
		if '@id' in new_json:
			try:
				id_response = get_ENCODE(new_json['@id'])
			except:
				id_response = {}
				new_object = True
		else:
			id_response = {}
		if 'uuid' in new_json:
			try:
				uuid_response = get_ENCODE(new_json['uuid'])
			except:
				uuid_response = {}
				new_object = True
		else:
			uuid_response = {}
		if 'accession' in new_json:
			try:
				accession_response = get_ENCODE(new_json['accession'])
			except:
				accession_response = {}
				new_object = True
		else:
			print "No identifier in new JSON object.  Assuming POST or PUT with auto-accessioning."
			new_object = True
			accession_response = {}

	object_exists = False
	if id_response:
		object_exists = True
		print "Found matching @id:"
		pprint_ENCODE(id_response)
	if uuid_response:
		object_exists = True
		print "Found matching uuid:"
		pprint_ENCODE(uuid_response)
	if accession_response:
		object_exists = True
		print "Found matching accession"
		pprint_ENCODE(accession_response)

	if id_response and uuid_response and (id_response != uuid_response):
		print "Existing id/uuid mismatch"
	if id_response and accession_response and (id_response != accession_response):
		print "Existing id/accession mismatch"
	if uuid_response and accession_response and (uuid_response != accession_response):
		print "Existing uuid/accession mismatch"

	if new_object and object_exists:
		print "Conflict:  At least one identifier already exists and at least one does not exist"

	supported_collections = ['access_key', 'antibody_approval', 'antibody_characterization',\
							'antibody_lot', 'award', 'biosample', 'biosample_characterization',\
							'construct', 'construct_characterization', 'dataset', 'document', 'donor',\
							'edw_key', 'experiment', 'file', 'file_relationship', 'human_donor', 'lab',\
							'library', 'mouse_donor', 'organism', 'platform', 'replicate', 'rnai',\
							'rnai_characterization', 'software', 'source', 'target', 'treatment', 'user']
	type_list = new_json.pop('@type',[])
	possible_collections = [x for x in type_list if x in supported_collections]
	if possible_collections:
		#collection = possible_collections[0] + 's/'
		collection = possible_collections[0]
	else:
		collection = []
	if '@id' in new_json:
		identifier = new_json.pop('@id')
	elif 'uuid' in new_json:
		if collection:
			identifier = '/' + collection + new_json['uuid'] + '/'
		else:
			identifier = '/' + new_json['uuid'] + '/'
	elif 'accession' in new_json:
		if collection:
			identifier = '/' + collection + new_json['accession'] + '/'
		else:
			identifier = '/' + new_json['accession'] + '/'
	if object_exists:
		if args.force_put:
			if not GET_ONLY:
				print "Replacing existing object"
				replace_ENCODE(identifier,new_json)
		else:
			if not GET_ONLY:
				print "Patching existing object"
				patch_ENCODE(identifier,new_json)
	elif new_object:
		if args.force_put:
			if not GET_ONLY:
				print "PUT'ing new object"
				replace_ENCODE(identifier,new_json)
		else:
			if not GET_ONLY:
				print "POST'ing new object"
				new_ENCODE(collection,new_json)


if __name__ == '__main__':
	main()
