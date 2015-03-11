#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Take a list of Publication identifiers and post Publication objects appropriatley'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path, pdb
import logging
from encodedcc import ENC_Key, ENC_Connection, ENC_Item

EPILOG = '''Notes:
	Requires a list of publication ids in the form:

	PMID:10373322
	doi:10.1038/nrm2003
	...

	Each object's identifier is echo'ed to stdout as the script works on it.

Examples:

	%(prog)s --key www --infile publication.txt

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
		help="file with publications to make")
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")

	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

	key = ENC_Key(args.keyfile, args.key) #get the keypair
	connection = ENC_Connection(key) #initialize the connection object
	obj_id = None
	search_url= 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term='
	summary_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id='

	f = open(args.infile,'rU')
	reader = f.readlines()
	for new_publication in reader:
		split_id = new_publication.partition( ':' )
		prefix = split_id[0]
		pub_id = split_id[2]
		
		#must make additional search to get PMID if PMID not supplied
		if prefix is not 'PMID': 
			search_response = requests.get(search_url + pub_id, headers = connection.headers)
			search_response_dict = search_response.json()
			if search_response_dict['esearchresult']['count'] == '0':
				logging.warning('SEARCH failure. Response = %s' % (search_response.text))
				continue
			pub_id = search_response_dict ['esearchresult']['idlist'][0]
		
		#build publication object
		publication_obj = {'@type': 'publication', 'status': 'published'}
		enc_object = ENC_Item(connection, obj_id)
		summary_response = requests.get(summary_url + pub_id, headers = connection.headers)
		summary_response_dict = summary_response.json()
		summary_publication = summary_response_dict ['result'][pub_id]
		publication_obj['title'] = summary_publication['title']
		publication_obj['date_published'] = summary_publication['pubdate']
		publication_obj['journal'] = summary_publication['source']
		publication_obj['volume'] = summary_publication['volume']
		publication_obj['issue'] = summary_publication['issue']
		publication_obj['page'] = summary_publication['pages']
		authors = []
		for author in summary_publication['authors']:
			authors.append(author['name'])
		publication_obj['authors'] = ', '.join(authors)
		references = []
		for article_id in summary_publication['articleids']:
			if article_id['idtype'] == 'pubmed':
				references.append('PMID:' + article_id['value'])
			elif  article_id['idtype'] == 'pmc':
				references.append('PMCID:' + article_id['value'])
			elif  article_id['idtype'] == 'doi':
				references.append('doi:' + article_id['value'])
		publication_obj['references'] = references # will change to identifiers with script update
		enc_object.properties.update(publication_obj)
		logging.info('Syncing %s' %(pub_id))
		logging.debug('%s' %(json.dumps(enc_object.properties, sort_keys=True, indent=4, separators=(',', ': '))))
		response_dict = enc_object.sync()
		print response_dict
		if response_dict['status'] == 'success':
			posted_object = response_dict['@graph'][0]
			new_id = posted_object['@id']
			print "New ENCODE id number: %s" %(new_id)
			print json.dumps(posted_object, sort_keys=True, indent=4, separators=(',', ': '))
	f.close()

if __name__ == '__main__':
	main()
