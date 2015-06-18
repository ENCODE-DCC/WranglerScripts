#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Reports replicate mappings'''

import pdb
import requests, json, jsonschema, csv, copy
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

	parser.add_argument('--infile', help="Input file containing experiment accessions to report on (over-rides assay,rfa,lab,query_terms)", type=argparse.FileType('r'))
	parser.add_argument('--server', help="Full URL of the server.")
	parser.add_argument('--key', default='default', help="The keypair identifier from the keyfile.  Default is --key=default")
	parser.add_argument('--keyfile', default=os.path.expanduser("~/keypairs.json"), help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
	parser.add_argument('--authid', help="The HTTP auth ID.")
	parser.add_argument('--authpw', help="The HTTP auth PW.")
	parser.add_argument('--debug', default=False, action='store_true', help="Print debug messages.  Default is False.")
	parser.add_argument('--assembly', help="The genome assembly to report on", default=None)
	parser.add_argument('--assay', help="The assay_term_name to report on", default='ChIP-seq')
	parser.add_argument('--rfa', help='ENCODE2 or ENCODE3. Omit for all', default=None)
	parser.add_argument('--lab', help='ENCODE lab name, e.g. j-michael-cherry', default=None)
	parser.add_argument('--query_terms', help='Additional query terms in the form "&term=value"', default=None)

	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)

	server, authid, authpw = processkeys(args)

	if args.assembly in ['hg19','GRCh38']:
		organism_name = 'human'
	elif args.assembly in ['mm10','mm9']:
		organism_name = 'mouse'
	else:
		organism_name = ''

	if args.infile:
		experiments = []
		for expid in args.infile:
			expid = expid.rstrip()
			url = urlparse.urljoin(server, '/experiments/%s' %(expid))
			result = get_ENCODE(url,authid,authpw)
			experiments.append(result)
	else:
		query = '/search/?type=experiment&field=assay_term_name&field=accession&field=biosample_term_name&field=biosample_type&field=lab.name&field=award.rfa&field=target.name&format=json&limit=all'
		if args.assay:
			query += '&assay_term_name=%s' %(args.assay)
		if args.rfa:
			query += '&award.rfa=%s' %(args.rfa)
		if args.lab:
			query += '&lab.name=%s' %(args.lab)
		if organism_name:
			query += '&replicates.library.biosample.donor.organism.name=%s' %(organism_name)
		if args.query_terms:
			query += args.query_terms

		url = urlparse.urljoin(server, query)

		result = get_ENCODE(url,authid,authpw)
		experiments = result['@graph']

	fieldnames = ['download link','experiment','target','biosample_name',
		'biosample_type','biorep_id','lab','rfa','assembly','bam',
		'hiq_reads','loq_reads','unique','fract_unique','distinct','fract_distinct',
		'NRF','PBC1','PBC2','frag_len','NSC','RSC','library','library aliases']
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=',', quotechar='"')
	writer.writeheader()

	for experiment in experiments:
		row_template = {
			'experiment': urlparse.urljoin(server, '/experiments/%s' %(experiment.get('accession'))),
			'target': experiment.get('target',{}).get('name'),
			'biosample_name': experiment.get('biosample_term_name'),
			'biosample_type': experiment.get('biosample_type'),
			'lab': experiment.get('lab',{}).get('name'),
			'rfa': experiment.get('award',{}).get('rfa')
		}
		original_files = get_ENCODE(urlparse.urljoin(server,'/search/?type=file&dataset=/experiments/%s/&frame=embedded&format=json' %(experiment.get('accession'))),authid,authpw)['@graph']
		fastqs = [f for f in original_files if f.get('file_format') == 'fastq' and f.get('status') not in ['deleted', 'revoked', 'replaced']]
		bams = [f for f in original_files if f.get('file_format') == 'bam' and (not args.assembly or f.get('assembly') == args.assembly) and f.get('status') not in ['deleted', 'revoked', 'replaced']]

		if not bams:
			row = copy.deepcopy(row_template)
			writer.writerow(row)
		else:
			for bam in bams:
				derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in [obj.get('accession') for obj in bam.get('derived_from')]]
				bioreps = set([str(f.get('replicate').get('biological_replicate_number')) for f in fastqs if f.get('accession') in derived_from_accessions])
				library_uris = set([str(f.get('replicate').get('library')) for f in fastqs if f.get('accession') in derived_from_accessions])
				aliases = []
				libraries = []
				for uri in library_uris:
					library = get_ENCODE(urlparse.urljoin(server,'%s' %(uri)), authid, authpw)
					libraries.append(library.get('accession'))
					aliases.extend(library.get('aliases'))
				row = copy.deepcopy(row_template)
				row.update({
					'biorep_id': ",".join(bioreps),
					'assembly': bam.get('assembly'),
					'bam': bam.get('accession'),
					'download link': urlparse.urljoin(server,bam.get('href')),
					'library': ','.join(libraries),
					'library aliases': ','.join(aliases)
				})
				notes = json.loads(bam.get('notes'))
				if isinstance(notes,dict):
					raw_flagstats		= notes.get('qc')
					filtered_flagstats	= notes.get('filtered_qc')
					duplicates			= notes.get('dup_qc')
					xcor				= notes.get('xcor_qc')
					pbc					= notes.get('pbc_qc')

					try:
						fract_unique = float(raw_flagstats.get('mapped')[0])/float(raw_flagstats.get('in_total')[0])
					except:
						fract_unique = ''
					try:
						fract_distinct = float(filtered_flagstats.get('in_total')[0])/float(raw_flagstats.get('in_total')[0])
					except:
						fract_distinct = ''

					if raw_flagstats:
						row.update({
							'hiq_reads': raw_flagstats.get('in_total')[0],
							'loq_reads': raw_flagstats.get('in_total')[1],
							'unique': raw_flagstats.get('mapped')[0],
							'fract_unique' : fract_unique,
							})
					if filtered_flagstats:
						row.update({
							'distinct': filtered_flagstats.get('in_total')[0],
							'fract_distinct': fract_distinct
							})
					if pbc:
						row.update({
							'NRF': pbc.get('NRF'),
							'PBC1': pbc.get('PBC1'),
							'PBC2': pbc.get('PBC2')
							})
					if xcor:
						row.update({
							'frag_len': xcor.get('estFragLen'),
							'NSC': xcor.get('phantomPeakCoef'),
							'RSC': xcor.get('relPhantomPeakCoef')
						})

				writer.writerow(row)

if __name__ == '__main__':
	main()
