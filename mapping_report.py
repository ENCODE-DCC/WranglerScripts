#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Reports replicate mappings'''

import pdb
import requests, json, jsonschema, csv
import logging, sys, os.path, urlparse, re

EPILOG = '''Example:
	%(prog)s --key www"
'''

def get_ENCODE(url, authid, authpw):
	'''force return from the server in JSON format'''
	'''GET an ENCODE object as JSON and return as dict'''
	if 'search' in url: #assume that a search query is complete except for &limit=all
		pass
	else:
		if '?' in url: # have to do this because it might be the first directive in the URL
			url += '&datastore=database'
		else:
			url += '?datastore=database'
	url += '&limit=all'
	logging.debug("GET %s" %(url))
	response = requests.get(url, auth=(authid, authpw), headers={'content-type': 'application/json'})
	try:
		response.raise_for_status()
	except:
		logging.error('HTTP GET failed: %s %s' %(response.status_code, response.reason))
		raise

	logging.debug("GET response code: %s" %(response.status_code))
	try:
		logging.debug("GET response json: %s" %(json.dumps(response.json(), indent=4, separators=(',', ': '))))
		return response.json()
	except:
		logging.debug("GET response text: %s" %(response.text))
		return response.text()

def processkeys(args):

	keysf = open(args.keyfile,'r')
	keys_json_string = keysf.read()
	keysf.close()
	keys = json.loads(keys_json_string)
	key_dict = keys[args.key]
	if not args.authid:
		authid = key_dict['key']
	else:
		authid = args.authid
	if not args.authpw:
		authpw = key_dict['secret']
	else:
		authpw = args.authpw
	if not args.server:
		server = key_dict['server']
	else:
		server = args.server
	if not server.endswith("/"):
		server += "/"

	return server, authid, authpw

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

	parser.add_argument('--query',
		help="A complete query to run rather than GET the whole collection.  \
		E.g. \"search/?type=biosample&lab.title=Ross Hardison, PennState\".  Implies --es.")
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

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

	server, authid, authpw = processkeys(args)

	url = urlparse.urljoin(server, "/search/?type=experiment&assay_term_name=ChIP-seq&target.label=Control&files.file_format=fastq&replicates.library.biosample.donor.organism.scientific_name=Homo%20sapiens&frame=embedded")

	result = get_ENCODE(url,authid,authpw)
	experiments = result['@graph']

	fieldnames = ['experiment','target','biosample_name','biosample_type','biorep_id','lab','rfa','assembly','bam','link','in_total_hiq','in_total_loq','read1_hiq','read1_loq','read2_hiq','read2_loq']
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=',', quotechar='"')
	writer.writeheader()

	for experiment in experiments:
		row = {}
		row_template = {
			'experiment': urlparse.urljoin(server, '/experiments/%s' %(experiment.get('accession'))),
			'target': experiment.get('target').get('name'),
			'biosample_name': experiment.get('biosample_term_name'),
			'biosample_type': experiment.get('biosample_type'),
			'lab': experiment.get('lab').get('name'),
			'rfa': experiment.get('award').get('rfa')
		}
		fastqs = [f for f in experiment.get('files') if f.get('file_format') == 'fastq']
		bams = [f for f in experiment.get('files') if f.get('file_format') == 'bam' and f.get('assembly') == "GRCh38"]
		if not bams:
			row = row_template
			writer.writerow(row)
		else:
			for bam in bams:
				derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in bam.get('derived_from')]
				bioreps = set([str(f.get('replicate').get('biological_replicate_number')) for f in fastqs if f.get('accession') in derived_from_accessions])
				row = row_template
				row.update({
					'biorep_id': ",".join(bioreps),
					'assembly': bam.get('assembly'),
					'bam': bam.get('accession'),
					'link': urlparse.urljoin(server,bam.get('href'))
				})
				notes = json.loads(bam.get('notes'))
				if isinstance(notes,dict):
					qc = notes.get('qc')
					row.update({
						'in_total_hiq': qc.get('in_total')[0],
						'in_total_loq': qc.get('in_total')[1],
						'read1_hiq': qc.get('read1')[0],
						'read1_loq': qc.get('read1')[1],
						'read2_hiq': qc.get('read2')[0],
						'read2_loq': qc.get('read2')[1]
					})

				writer.writerow(row)


if __name__ == '__main__':
	main()
