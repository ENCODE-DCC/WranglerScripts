#!/usr/bin/env python

import os, sys, logging, urlparse, requests, csv, StringIO, re, copy, json
import dxpy
import common

logger = logging.getLogger(__name__)

EPILOG = '''Notes:

Examples:

	%(prog)s
'''

def get_args():
	import argparse
	parser = argparse.ArgumentParser(
		description=__doc__, epilog=EPILOG,
		formatter_class=argparse.RawDescriptionHelpFormatter)

	parser.add_argument('experiments',	help='List of ENCSR accessions to report on', nargs='*', default=None)
	parser.add_argument('--infile',		help='File containing ENCSR accessions', type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument('--debug',		help="Print debug messages", default=False, action='store_true')
	parser.add_argument('--key',		help="The keypair identifier from the keyfile.", default='www')
	parser.add_argument('--keyfile',	help="The keyfile.", default=os.path.expanduser("~/keypairs.json"))
	parser.add_argument('--query', 		help="Take experiments from a query")
	parser.add_argument('--dryrun',		help="Do everything except change the database", default=False, action='store_true')

	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else: #use the defaulf logging level
		logging.basicConfig(format='%(levelname)s:%(message)s')

	return args


def main():

	args = get_args()
	if args.debug:
		logger.setLevel(logging.DEBUG)
	else:
		logger.setLevel(logging.INFO)

	authid, authpw, server = common.processkey(args.key, args.keyfile)
	keypair = (authid,authpw)

	if args.query:
		r = requests.get(args.query, auth=keypair, headers={'content-type': 'application/json', 'accept': 'application/json'})
		experiments = r.json()['@graph']
		exp_ids = [e['accession'] for e in experiments]
	elif args.experiments:
		exp_ids = args.experiments
	else:
		exp_ids = args.infile

	for (i, exp_id) in enumerate(exp_ids):
		exp_id = exp_id.strip()
		logger.info('%s' %(exp_id))
		url = urlparse.urljoin(server, '/experiments/%s' %(exp_id))
		experiment_object = common.encoded_get(url, keypair)
		original_files = [common.encoded_get(urlparse.urljoin(server,'%s' %(uri)), keypair) for uri in experiment_object.get('original_files')]
		bams = [f for f in original_files if f.get('file_format') == 'bam' and f.get('status') not in ['revoked','deleted','replaced']]
		fastqs = [f for f in original_files if f.get('file_format') == 'fastq' and f.get('status') not in ['revoked','deleted','replaced']]
		beds = [f for f in original_files if f.get('file_format') == 'bed' and f.get('status') not in ['revoked','deleted','replaced']]
		bigBeds = [f for f in original_files if f.get('file_format') == 'bigBed' and f.get('status') not in ['revoked','deleted','replaced']]
		for f in beds + bigBeds:
			notes = json.loads(f.get('notes'))
			f['job'] = dxpy.describe(notes['dx-createdBy']['job'])
			job = dxpy.describe(notes['dx-createdBy']['job'])
			output_names = [output_name for output_name,value in job['output'].iteritems() if dxpy.is_dxlink(value) and value['$dnanexus_link'] == notes['dx-id']]
			assert len(output_names) == 1
			f['output_name'] = output_names[0]
			f['dxid'] = notes['dx-id']
		for bb in bigBeds:
			print bb['accession']
			notes = json.loads(bb.get('notes'))
			job = dxpy.describe(notes['dx-createdBy']['job'])
			output_name = bb['output_name']
			assert output_name.endswith('_bb')
			print output_name
			bed_output_name = output_name.rpartition('_bb')[0]
			print bed_output_name
			bed_dxid = job['output'][bed_output_name]['$dnanexus_link']
			print bed_dxid
			possible_beds = [bed['accession'] for bed in beds if bed.get('notes') and json.loads(bed['notes'])['dx-id'] == bed_dxid]
			print possible_beds
			assert len(possible_beds) == 1
			print possible_beds[0]
			if not args.dryrun:
				url = urlparse.urljoin(server,'/files/%s/' %(bb['accession']))
				payload = {'derived_from':[possible_beds[0]]}
				print url
				print payload
				r = requests.patch(url, auth=keypair, data=json.dumps(payload), headers={'content-type': 'application/json', 'accept': 'application/json'})
				try:
					r.raise_for_status()
				except:
					print r.text
		overlapping_peaks_beds = [b for b in beds if b.get('output_name') == 'overlapping_peaks']
		assert len(overlapping_peaks_beds) == 1
		overlapping_peaks_bed = overlapping_peaks_beds[0]
		job = overlapping_peaks_bed['job']
		derived_from_dxids = [job['input'][input_name]['$dnanexus_link'] for input_name in job['input'].keys() if input_name in ['rep1_peaks', 'rep2_peaks', 'pooled_peaks']]
		print derived_from_dxids
		derived_from_accessions = [bed['accession'] for bed in beds if bed['dxid'] in derived_from_dxids]
		print derived_from_accessions
		if not args.dryrun:
			url = urlparse.urljoin(server,'/files/%s/' %(overlapping_peaks_bed['accession']))
			payload = {'derived_from':derived_from_accessions}
			print url
			print payload
			r = requests.patch(url, auth=keypair, data=json.dumps(payload), headers={'content-type': 'application/json', 'accept': 'application/json'})
			try:
				r.raise_for_status()
			except:
				print r.text
	

if __name__ == '__main__':
	main()
