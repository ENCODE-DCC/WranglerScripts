#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Take an ENCODE file accession number and ls that file from the S3 bucket'''

EPILOG = '''Example:
	%(prog)s ENCFF000AAA

'''

import requests, subprocess, shlex, urlparse, os, sys, json
import argparse, logging

def processkeys(args):

	if args.key:
		keysf = open(args.keyfile,'r')
		keys_json_string = keysf.read()
		keysf.close()
		keys = json.loads(keys_json_string)
		key_dict = keys[args.key]
	else:
		key_dict = {}
	global AUTHID
	global AUTHPW
	global SERVER
	if not args.authid:
		AUTHID = key_dict.get('key')
	else:
		AUTHID = args.authid
	if not args.authpw:
		AUTHPW = key_dict.get('secret')
	else:
		AUTHPW = args.authpw
	if args.server:
		SERVER = args.server
	elif key_dict:
		SERVER = key_dict.get('server')
	else:
		SERVER = 'https://www.encodeproject.org/'

	if not SERVER.endswith("/"):
		SERVER += "/"

def encoded_get(url):
	if AUTHID and AUTHPW:
		response = requests.get(url, auth=(AUTHID,AUTHPW), headers=HEADERS)
	else:
		response = requests.get(url, headers=HEADERS)
	return response

parser = argparse.ArgumentParser(
	description=__doc__, epilog=EPILOG,
	formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('file_accession',
	help="The file accession you're looking for")
parser.add_argument('destination',
	help="The desination path for the file",
	default='.')
parser.add_argument('--server',
	help="Full URL of the server.")
parser.add_argument('--key',
	default=None,
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

processkeys(args)

if args.debug:
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
else: # use the defaulf logging level
	logging.basicConfig(format='%(levelname)s:%(message)s')

S3_SERVER='s3://encode-files/'
HEADERS = {'content-type': 'application/json'}

url = SERVER + 'search/?type=file&accession=%s&format=json&frame=embedded&limit=all' %(args.file_accession)
#get the file object
response = encoded_get(url)

#select your file
f_obj = response.json()['@graph'][0]

#make the URL that will get redirected - get it from the file object's href property
encode_url = urlparse.urljoin(SERVER,f_obj.get('href'))

#stream=True avoids actually downloading the file, but it evaluates the redirection
r = requests.get(encode_url, auth=(AUTHID,AUTHPW), headers=HEADERS, allow_redirects=True, stream=True)
try:
	r.raise_for_status
except:
	print '%s href does not resolve' %(f_obj.get('accession'))
	sys.exit()

#this is the actual S3 https URL after redirection
s3_url = r.url

#release the connection
r.close()

#split up the url into components
o = urlparse.urlparse(s3_url)

#pull out the filename
filename = os.path.basename(o.path)

#hack together the s3 cp url (with the s3 method instead of https)
bucket_url = S3_SERVER.rstrip('/') + o.path
#print bucket_url

#cp the file from the bucket
print subprocess.check_output(shlex.split('aws s3 cp %s %s' %(bucket_url, args.destination)))
