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
	response = requests.get(url, auth=(authid, authpw), headers={'accept': 'application/json'})
	try:
		response.raise_for_status()
	except:
		logging.debug('HTTP GET failed: %s %s' %(response.status_code, response.reason))

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
		query = '/search/?type=experiment&field=assay_term_name&field=accession&field=biosample_term_name&field=biosample_type&field=lab.name&field=award.rfa&field=target.name&field=target.investigated_as&format=json&limit=all'
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

	fieldnames = ['download link','experiment','target_type','target','biosample_name',
		'biosample_type','biorep_id','lab','rfa','assembly','bam',
		'hiq_reads','loq_reads','mappable','fract_mappable','end','r_lengths','usable_frags','fract_usable',
		'NRF','PBC1','PBC2','frag_len','NSC','RSC','library','library aliases','from fastqs','date_created','release status']
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=',', quotechar='"')
	writer.writeheader()

	for experiment in experiments:
		row_template = {
			'experiment': urlparse.urljoin(server, '/experiments/%s' %(experiment.get('accession'))),
			'target_type': ','.join(experiment.get('target',{}).get('investigated_as') or []),
			'target': experiment.get('target',{}).get('name'),
			'biosample_name': experiment.get('biosample_term_name'),
			'biosample_type': experiment.get('biosample_type'),
			'lab': experiment.get('lab',{}).get('name'),
			'rfa': experiment.get('award',{}).get('rfa')
		}
		original_files = get_ENCODE(urlparse.urljoin(server,'/search/?type=file&dataset=/experiments/%s/&file_format=fastq&file_format=bam&frame=embedded&format=json' %(experiment.get('accession'))),authid,authpw)['@graph']
		fastqs = [f for f in original_files if f.get('file_format') == 'fastq' and f.get('status') not in ['deleted', 'revoked', 'replaced']]
		bams = [f for f in original_files if f.get('file_format') == 'bam' and (not args.assembly or f.get('assembly') == args.assembly) and f.get('status') not in ['deleted', 'revoked', 'replaced']]

		row = copy.deepcopy(row_template)

		if not bams:
			if not fastqs:
				row.update({'bam': "no fastqs"})
			else:
				row.update({'bam': "pending"})

				read_lengths =	set([str(f.get('read_length')) for f in fastqs])
				row.update({'r_lengths': ",".join(read_lengths)})

				paired_end_strs = []
				if any([f.get('run_type') == "single-ended" for f in fastqs]):
					paired_end_strs.append('SE')
				if any([f.get('run_type') == "paired-ended" for f in fastqs]):
					paired_end_strs.append('PE')
				if any([f.get('run_type') == "unknown" for f in fastqs]):
					paired_end_strs.append('unknown')
				row.update({'end': ",".join(paired_end_strs)})

			writer.writerow(row)
		else:
			for bam in bams:
				derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in [obj.get('accession') for obj in bam.get('derived_from') or []]]
				derived_from_fastqs = [f for f in fastqs if f.get('accession') in derived_from_accessions]
				derived_from_fastq_accessions = [f.get('accession') for f in fastqs if f.get('accession') in derived_from_accessions]
				bioreps = 		set([str(f.get('replicate').get('biological_replicate_number'))	for f in derived_from_fastqs])
				library_uris = 	set([str(f.get('replicate').get('library')) 					for f in derived_from_fastqs])
				read_lengths =	set([str(f.get('read_length')) 									for f in derived_from_fastqs])
				aliases = []
				libraries = []
				for uri in library_uris:
					library = get_ENCODE(urlparse.urljoin(server,'%s' %(uri)), authid, authpw)
					libraries.append(library.get('accession'))
					aliases.extend(library.get('aliases'))
				row.update({
					'biorep_id': ",".join(bioreps),
					'assembly': bam.get('assembly'),
					'bam': bam.get('accession'),
					'download link': urlparse.urljoin(server,bam.get('href')),
					'library': ','.join(libraries),
					'library aliases': ','.join(aliases),
					'r_lengths': ','.join(read_lengths),
					'from fastqs': ','.join(derived_from_fastq_accessions),
					'date_created': bam.get('date_created'),
					'release status': bam.get('status')
				})
				try:
					notes = json.loads(bam.get('notes'))
				except:
					notes = None
				quality_metrics = bam.get('quality_metrics')
				# if quality_metrics:
				# 	filter_qc = next(m for m in quality_metrics if "ChipSeqFilterQualityMetric" in m['@type'])
				# 	xcor_qc = next(m for m in quality_metrics if "SamtoolsFlagstatsQualityMetric" in m['@type'])


				# elif isinstance(notes,dict):
				if isinstance(notes,dict):
					#this needs to support the two formats from the old accessionator and the new accession_analysis
					if 'qc' in notes.get('qc'): #new way
						qc_from_notes = notes.get('qc')
					else:
						qc_from_notes = notes
					raw_flagstats		= qc_from_notes.get('qc')
					filtered_flagstats	= qc_from_notes.get('filtered_qc')
					duplicates			= qc_from_notes.get('dup_qc')
					xcor				= qc_from_notes.get('xcor_qc')
					pbc					= qc_from_notes.get('pbc_qc')

					try:
						fract_mappable = float(raw_flagstats.get('mapped')[0])/float(raw_flagstats.get('in_total')[0])
					except:
						fract_mappable = ''

					try:
						paired_end = filtered_flagstats.get('read1')[0] or filtered_flagstats.get('read1')[1] or filtered_flagstats.get('read2')[0] or filtered_flagstats.get('read2')[1]
					except:
						paired_end_str = ''
						usable_frags = ''
					else:
						if paired_end:
							usable_frags = filtered_flagstats.get('in_total')[0]/2
							paired_end_str = "PE"
						else:
							paired_end_str = "SE"
							usable_frags = filtered_flagstats.get('in_total')[0]
					row.update({'end': paired_end_str})

					try:
						fract_usable = float(filtered_flagstats.get('in_total')[0])/float(raw_flagstats.get('in_total')[0])
					except:
						fract_usable = ''


					if raw_flagstats:
						row.update({
							'hiq_reads': raw_flagstats.get('in_total')[0],
							'loq_reads': raw_flagstats.get('in_total')[1],
							'mappable': raw_flagstats.get('mapped')[0],
							'fract_mappable' : fract_mappable
							})
					if filtered_flagstats:
						row.update({
							'usable_frags': usable_frags,
							'fract_usable': fract_usable
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
				sys.stdout.flush()

if __name__ == '__main__':
	main()
