#!/usr/bin/env python
# -*- coding: latin-1 -*-
''' Script to convert a JSON file to TSV. Adapted from http://kailaspatil.blogspot.com/2013/07/python-script-to-convert-json-file-into.html
'''
import fileinput
import json
import csv
import sys

EPILOG = '''Usage: %(prog)s -i [input JSON file] > [output TSV file]'''

def main():
	import argparse
	parser = argparse.ArgumentParser(description=__doc__, epilog=EPILOG,
	    formatter_class=argparse.RawDescriptionHelpFormatter,
	)

	parser.add_argument('--infile', '-i', help="JSON file to convert to TSV")
	args = parser.parse_args()

	lines = []
	if args.infile:
		with open(args.infile, 'r') as f:
			for line in f:
				lines.append(line)
	else:
		print >> sys.stderr, "Usage: JSON2TSV.py -i [input JSON file] > [output TSV file]"
		sys.exit(0)

	new_json = json.loads(''.join(lines))
	keys = {}

	for i in new_json:
		for k in i.keys():
			keys[k] = 1

	tab_out = csv.DictWriter(sys.stdout, fieldnames=keys.keys(), dialect='excel-tab')
	tab_out.writeheader()

	for row in new_json:
		tab_out.writerow(row)

if __name__ == '__main__':
	main()