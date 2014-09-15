#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''GET an ENCODE url and gather links to data files'''

'''use requests to handle the HTTP connection'''
import requests
'''use json to convert between Python dictionaries and JSON objects'''
import json
'''use jsonschema to validate objects against the JSON schemas'''
import jsonschema
import sys, os.path, pdb, codecs
import logging
from urlparse import urlsplit, urlunsplit
from csv import DictWriter

EPILOG = '''
Todo: Link in controls

Examples:

	%(prog)s "https://www.encodedcc.org/search/?type=experiment&assay_term_name=ChIP-seq&status=released&organ_slims=skin%%20of%%20body" > data_files.tsv

'''

DOWNLOAD_URL_BASE = 'http://encodedcc.sdsc.edu/warehouse/'

class ENC_Key:
	def __init__(self, keyfile, keyname):
		if keyname:
			keys_f = open(keyfile,'r')
			keys_json_string = keys_f.read()
			keys_f.close()
			keys = json.loads(keys_json_string)
			key_dict = keys[keyname]
			self.auth = (key_dict['key'], key_dict['secret'])
			self.url = urlsplit(key_dict['server'])
		else:
			self.auth = None
			self.url = None

class ENC_Connection(object):
	def __init__(self, urlstr, key=None):
		self.session = requests.Session()
		self.session.headers.update({'content-type': 'application/json'})

		if key and urlstr:
			self.session.auth = key.auth
			self.url = urlsplit(urlstr)
		elif key:
			self.session.auth = key.auth
			self.url = key.url
		elif urlstr:
			self.session.auth = None
			self.url = urlsplit(urlstr)
		else:
			logging.exception('Connection requires at least a key or a url')


	def get(self, urlstr="", frame='object'):
		supplied_url = urlsplit(urlstr)
		url_attributes = [
			supplied_url.scheme if supplied_url.scheme else self.url.scheme,
			supplied_url.netloc if supplied_url.netloc else self.url.netloc,
			supplied_url.path if supplied_url.path else self.url.path,
			supplied_url.query if supplied_url.query else self.url.query,
			""]
 		query_string = url_attributes[3]
 		query_string += '&format=json'
		if 'limit=' not in query_string:
			query_string += '&limit=all'
		if 'frame=' not in supplied_url.query:
			query_string += '&frame=' + frame
		url_attributes[3] = query_string
		url_tuple = tuple(url_attributes)
		url = urlunsplit(url_tuple)
		logging.info('GET url %s' %(url))
		response = self.session.get(url)
		logging.info('GET RESPONSE code %s' %(response.status_code))
		try:
			if response.json():
				pass
				#logging.info('GET RESPONSE JSON: %s' %(json.dumps(response.json(), indent=4, separators=(',', ': '))))
		except:
			logging.info('GET RESPONSE text %s' %(response.text))
		if not response.status_code == 200:
			logging.warning('GET failure.  Response code = %d Response text = %s' %(response.status_code, response.text))
		return response


def main():

	import argparse
	parser = argparse.ArgumentParser(
		description=__doc__, epilog=EPILOG,
		formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('url',
		help="Any valid ENCODE url to GET, including searches.  If no server is specified, it will be inferred from key.")
	parser.add_argument('outfile',
		help="Output file in which to save the results")
	parser.add_argument('--key',
		default=None,
		help="The keypair identifier from the keyfile for the server.  Necessary to retrieve unreleased data.  Defaults to None, in which case requests will be made with no authentication.")
	parser.add_argument('--keyfile',
		default=os.path.expanduser("~/keypairs.json"),
		help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
	parser.add_argument('--debug',
		default=False,
		action='store_true',
		help="Print debug messages.  Default is False.")

	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else: # use the defaulf logging level
		logging.basicConfig(format='%(levelname)s:%(message)s')

	if args.key:
		key = ENC_Key(args.keyfile, args.key)
	else:
		key = None
	connection = ENC_Connection(args.url, key)

	response = connection.get(frame='embedded')
	if response.status_code == 200:
		json = response.json()
		try:
			items = json['@graph']
		except:
			items = [json]
	else:
		items = []

	rows = []
	for experiment in items:
		for file_obj in experiment['files']:
			row = {}
			row['ENCSR'] = experiment['accession']
			logging.info('%s' %(experiment['accession']))
			row['file'] = file_obj['accession']
			if 'biosample_term_name' in experiment:
				row['biosample'] = experiment['biosample_term_name']
			else:
				row['biosample'] = ""
			if 'target' in experiment:
				row['target'] = experiment['target']['name']
			else:
				row['target'] = ""
			row['lab'] = experiment['lab']['name']
			row['phase'] = experiment['award']['rfa']
			row['output type'] = file_obj['output_type']
			row['file format'] = file_obj['file_format']
			row['download link'] = DOWNLOAD_URL_BASE + file_obj['download_path']
			row['submitted filename'] = file_obj['submitted_file_name']

			try: #if the file has a replicate
				replicate = file_obj['replicate'] #replicate is embedded in file
			except KeyError:
				logging.info('File has no replicate')
				replicate = None

			if replicate:
				for exp_replicate in experiment['replicates']:
					if exp_replicate['uuid'] == replicate['uuid']:
						replicate = exp_replicate
						break

			try:
				biosample = replicate['library']['biosample']
			except:
				logging.info('Replicate has no library or library has no biosample')
				biosample = None
			
			if replicate:
				row['biorep num'] = replicate['biological_replicate_number']
				row['techrep num'] = replicate['technical_replicate_number']
			else:
				row['biorep num'] = None
				row['techrep num'] = None

			if biosample:
				treatment_str = u''
				for treatment in biosample['treatments']:
					#treatment = connection.get(treatment_uri).json()
					for key in ['concentration', 'concentration_units', 'treatment_term_name', 'duration', 'duration_units']:
						if key in treatment.keys():
							treatment_str += unicode(treatment[key]) + u" "
					treatment_str = treatment_str.rstrip()
				if treatment_str:
					row['treatment'] = treatment_str
				else: # there are no treatments to the biosamples
					row['treatment'] = None
			else: # there are no biosamples
				row['treatment'] = None

			rows.append(row)

	
	headers = ['ENCSR','biosample','target','treatment','biorep num','techrep num','file','output type','file format','download link','submitted filename','lab','phase']
	f = codecs.open(args.outfile, encoding='utf-8', mode='wb')
	writer = DictWriter(f,fieldnames=headers)
	writer.writeheader()
	#writer.writerows(rows) can't use this becuase it doesn't support unicode
	for row in rows:
		row_str = u''
		for field in headers:
			if ',' in unicode(row[field]):
				row_str += u'"' + unicode(row[field]) + u'"' + u','
			else:
				row_str += unicode(row[field]) + u','
		row_str = row_str.rstrip()
		row_str = row_str.rstrip(',')
		row_str += u'\n'
		f.write(row_str)
	f.close()

if __name__ == '__main__':
	main()
