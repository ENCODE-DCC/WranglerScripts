#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Detect duplicated sequence id's in or between fastqs'''

EPILOG = '''Notes:

Examples:

	%(prog)s
'''

import sys, logging, os.path
from zlib import crc32
import gzip
import common

logger = logging.getLogger(__name__)

def get_args():
	import argparse
	parser = argparse.ArgumentParser(
		description=__doc__, epilog=EPILOG,
		formatter_class=argparse.RawDescriptionHelpFormatter)

	parser.add_argument('infile',	help="Fastq's to search within and across", nargs='+')
	parser.add_argument('--mesh',		help="Sampling rate (approximately mesh^-1)", default=1000000)
	parser.add_argument('--debug',		help="Print debug messages", default=False, action='store_true')

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

	#force out to be unbuffered
	out = os.fdopen(sys.stdout.fileno(), 'w', 0)

	mesh = int(args.mesh)
	logger.debug("Mesh %d" %(mesh))
	sampled_seqids = {}
	for filename in args.infiles:
		out.write("Sampling %s" %(filename))

		fh = gzip.open(filename)
		for i, line in enumerate(fh):
			if i % 4 != 0:
				continue
			# Normalize crc32 result to an unsigned int for Python 2.
			if (crc32(line) & 0xffffffff) % mesh == 0:
				out.write('.')
				if line in sampled_seqids:
					sampled_seqids[line].append(filename)
				else:
					sampled_seqids.update({line:[filename]})
		out.write('\n')
		logger.debug("%s" %(sampled_seqids))

	for seqid,hits in sampled_seqids.iteritems():
		if len(hits) > 1:
			out.write('%s in %s\n' %(seqid.strip(),hits))


if __name__ == '__main__':
	main()
