#!/usr/bin/env python

import os, sys, logging, urlparse, requests, csv, StringIO, re, copy
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
	parser.add_argument('--assembly', 	help='Genome assembly like hg19 or mm10', required=True)
	parser.add_argument('--debug',		help="Print debug messages", default=False, action='store_true')
	parser.add_argument('--key',		help="The keypair identifier from the keyfile.", default='www')
	parser.add_argument('--keyfile',	help="The keyfile.", default=os.path.expanduser("~/keypairs.json"))
	parser.add_argument('--query', 		help="Take experiments from a query")

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
		for f in fastqs:
			f['replicate'] = common.encoded_get(urlparse.urljoin(server,'%s' %(f.get('replicate'))), keypair)
		for bam in bams:
			bioreps = common.biorep_ns(bam.get('accession'),server,keypair)
			if len(bioreps) != 1:
				logger.error("Expected to find 1 biorep for bam %s, found %d.  Skipping." %(bam.get('accession'), len(bioreps)))
				continue
			else:
				bam_biorep = bioreps[0]
			try:
				derived_from = [common.encoded_get(urlparse.urljoin(server,'%s' %(uri)), keypair) for uri in bam.get('derived_from')]
			except:
				derived_from = None
			if not derived_from:
				logger.error('bam %s is derived from nothing. Skipping' %(bam.get('accession')))
				continue
			for f in derived_from:
				if f.get('file_format') != 'fastq':
					logger.error("bam %s appears to be derived from non-fastq %s. Continuing with other derived_from files." %(bam.get('accession'), f.get('accession')))
					continue
				try:
					if common.after(f.get('date_created'), bam.get('date_created')):
						logger.error("Date conflict. Bam %s is derived from newer Fastq %s" %(bam.get('accession'), f.get('accession')))
				except:
					logger.error("Cannot compare bam date %s with fastq date %s. Continuing with other derived_from files." %(bam.get('date_created'), f.get('date_created')))
					continue
			for f in fastqs:
				if f.get('replicate').get('biological_replicate_number') == bam_biorep:
					if common.after(f.get('date_created'), bam.get('date_created')):
						logger.info("bam %s is out-of-date.  fastq %s is newer" %(bam.get('accession'), f.get('accession')))
						if re.search('control',experiment_object.get('target').lower()):
							logger.info("WARNING, %s is a control experiment so many other experiments may be out-of-date." %(experiment_object.get('accession')))

if __name__ == '__main__':
	main()
