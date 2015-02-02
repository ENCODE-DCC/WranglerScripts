#!/usr/bin/env python
# -*- coding: latin-1 -*-
''' Example to extract files from a search result
'''
import requests

AUTH = "LXDWVIW7", "uz2dmao52jxsv6jj"
HEADERS = {'content-type': 'application/json'}
query_url = "https://www.encodeproject.org/search/?type=experiment&assay_term_name=RNA-seq&replicates.library.biosample.donor.organism.scientific_name=Mus+musculus&limit=all&lab.title=Barbara+Wold%2C+Caltech&format=json&frame=embedded"

r = requests.get(query_url, auth=AUTH, headers=HEADERS) # gets the full JSON output from the server

try:
	r.raise_for_status()
except:
	print('GET failed: %s %s' %(r.status_code, r.reason))
	print(r.text)
	raise

experiments = r.json()['@graph'] # extracts just the ENCODE experiment objects

for experiment in experiments: # for each experiment, build a downloadable URL for each fastq file
	for file_obj in experiment['files']:
		if file_obj['file_format'] == 'fastq':
			download_url = "https://www.encodeproject.org" + file_obj['href']
			try:
				paired_end = file_obj['paired_end']
			except:
				paired_end = ""
			print('%s\t%s\t%s\t%s\t%s\t%s' \
				%(experiment['accession'],
				  experiment['biosample_term_name'],
				  experiment['description'],
				  file_obj['replicate']['biological_replicate_number'],
				  paired_end,
				  download_url))
