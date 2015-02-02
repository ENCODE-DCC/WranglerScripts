#!/usr/bin/env python
# -*- coding: latin-1 -*-

import requests, re, time, json, subprocess

def main():

	ignore_statuses = ['deleted', 'revoked', 'replaced']
	search_string = "2014-10"
	lab = "/labs/bradley-bernstein/"

	all_files = requests.get('https://www.encodeproject.org/search/?type=file&lab=%s&field=accession&field=lab&field=date_created&format=json&limit=all' %(lab), auth=('LXDWVIW7','uz2dmao52jxsv6jj'), headers={'content-type': 'application/json'}).json()['@graph']

	files = [f for f in all_files if re.search(search_string,f.get('date_created')) and f.get('status') not in ignore_statuses]
	print "%s %s" %(lab, len(files))

	print [(f.get('accession'), subprocess.call('ENCODE_s3ls.py --key www %s' %(f.get('accession')), shell=True)) for f in files]


if __name__ == '__main__':
	main()
