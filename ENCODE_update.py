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
from encodedcc import ENC_Key, ENC_Connection, ENC_Item

EPILOG = '''Notes:
	Requires comma-delimited, double quote-quoted (for values containing commas or newlines)
	csv's should have a header as below and data rows in the form:

	accession,property1,property2,property3 ...
	ENCBSxyzabc,value1,value2,value3 ...
	...

	The accession (or uuid or other valid identifier) must exist and the properties must be in its schema.
	If the property does not exist in the object it is added with the specified value.
	If the property exists in the object, its value is over-written.
	If the property exists and the new value is "", the property will be removed altogether.

	Each object's identifier is echo'ed to stdout as the script works on it.

Examples:

	%(prog)s --key www --infile note2notes.csv

'''

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

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else: # use the defaulf logging level
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

	key = ENC_Key(args.keyfile, args.key) #get the keypair
	connection = ENC_Connection(key) #initialize the connection object
	#biosample_collection = ENC_Collection(connection,'biosamples',frame='object')

	with open(args.infile,'rU') as f:
		reader = csv.DictReader(f, delimiter=',', quotechar='"')
		for new_metadata in reader:
			uuid = new_metadata.pop('uuid',None)
			accession = new_metadata.pop('accession',None)
			if uuid: #use the uuid if there is one
				obj_id = uuid
			elif accession: #if no uuid then use the accession
				obj_id = accession
			else: #if neither uuid or accession, assume this is a new object
				obj_id = None
			enc_object = ENC_Item(connection, obj_id)
			for prop in new_metadata:
				if new_metadata[prop].strip() == "": #pop out the old property from the object
					old_value = enc_object.properties.pop(prop,None)
				else: #new property or new value for old property
					new_metadata_string = new_metadata[prop]
					#TODO here we need to explicitly handle datatypes (ints/floats, arrrays, strings)
					json = '{"%s" : "%s"}' %(prop, new_metadata_string) #this assumes string
					enc_object.properties.update(json.loads(json))
			logging.info('Syncing %s' %(obj_id))
			logging.info('%s' %(json.dumps(enc_object.properties, sort_keys=True, indent=4, separators=(',', ': '))))
			if not args.dryrun:
				enc_object.sync()

if __name__ == '__main__':
	main()
