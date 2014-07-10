#! /usr/bin/env python

'''GET an object from ENCODE metadata server'''
import requests, json

def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return local_filename

HEADERS = {'accept': 'application/json'}

FILE_URL = 'http://encodedcc.sdsc.edu/warehouse/'
### WARNING THIS SUBJECT TO CHANGE WITHOUT NOTICE

# This URL returns all fastqs from experiment ENCSR000AKS
BASE_URL = 'https://www.encodedcc.org/search/?'
QUERY = 'type=file&dataset=/experiments/ENCSR000AKS/&file_format=fastq&limit=all&frame=object'

# get the metadata object
response = requests.get(BASE_URL+QUERY, headers=HEADERS)

# get the files
import pdb; pdb.set_trace()
for file_dict in response.json()['@graph']:
    fn = download_file(FILE_URL+file_dict['download_path'])
    print "Downloaded: %s" % fn