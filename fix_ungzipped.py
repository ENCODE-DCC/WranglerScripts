#!/usr/bin/env python

import os, shutil, shlex, sys, subprocess, logging, re, json, urlparse, requests, time
import magic, mimetypes

EPILOG = '''Notes:

Examples:

	%(prog)s
'''

KEYFILE = os.path.expanduser("~/keypairs.json")
S3_BUCKET = "encode-files"

def get_args():
	import argparse
	parser = argparse.ArgumentParser(
		description=__doc__, epilog=EPILOG,
		formatter_class=argparse.RawDescriptionHelpFormatter)

	#parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
	parser.add_argument('--debug',   help="Print debug messages", default=False, action='store_true')
	parser.add_argument('--key', help="The keypair identifier from the keyfile.  Default is --key=default",
		default='default')
	parser.add_argument('--dryrun', help="Do everything except make changes", default=False, action='store_true')

	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	else: #use the defaulf logging level
		logging.basicConfig(format='%(levelname)s:%(message)s')

	return args

def processkey(key):

	if key:
		keysf = open(KEYFILE,'r')
		keys_json_string = keysf.read()
		keysf.close()
		keys = json.loads(keys_json_string)
		key_dict = keys[key]
	else:
		key_dict = {}
	AUTHID = key_dict.get('key')
	AUTHPW = key_dict.get('secret')
	if key:
		SERVER = key_dict.get('server')
	else:
		SERVER = DEFAULT_SERVER

	if not SERVER.endswith("/"):
		SERVER += "/"

	return (AUTHID,AUTHPW,SERVER)

def encoded_get(url, headers={'accept': 'application/json'}, **kwargs):
	#url = urlparse.urljoin(url,'?format=json&frame=embedded&datastore=database')
	for count in range(5):
		try:
			r = requests.get(url, headers=headers, **kwargs)
		except requests.ConnectionError:
			continue
		else:
			return r

def encoded_patch(url, headers={'content-type': 'application/json', 'accept': 'application/json'}, **kwargs):
	return requests.patch(url, headers=headers, **kwargs)

def gzip_and_post(f_obj, path, server, keypair):

	ungzipped_md5 = hashlib.md5()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(1024*1024), ''):
			ungzipped_md5.update(chunk)

	ungzipped_name = path.rpartition('.gz')[0]

	print "Backing up %s" %(path)
	backup_path = os.path.join('/external/backup',path.lstrip('/'))
	backup_dir = os.path.dirname(backup_path)
	if not os.path.exists(backup_dir):
		os.mkdirs(backup_dir)
	shutil.copy2(path, backup_path)

	print "Renaming %s to %s" %(path,ungzipped_name)
	os.rename(path,ungzipped_name)

	try:
		print "Gzipping",
		subprocess.check_call(['gzip', '-n', ungzipped_name])
	except subprocess.CalledProcessError as e:
		print "Gzip failed :%s" %(e)
		return
	else:
		print "complete"

	gzipped_md5 = hashlib.md5()
	with open(path, 'rb') as f:
		for chunk in iter(lambda: f.read(1024*1024), ''):
			gzipped_md5.update(chunk)

	'''
	query = '/files/%s/upload' %(f_obj.get('accession')
	url = urlparse.urljoin(server,query)
	r = encoded_post(url, auth=keypair, data='{}')
	try:
		r.raise_for_status
	except:
		print "GET credentials failed: %s %s" %(r.status_code, r.reason)
		print r.text
		return
	creds = r.json()['@graph'][0].get('upload_credentials')
	env = os.environ.copy()
	env.update({
		'AWS_ACCESS_KEY_ID': creds['access_key'],
		'AWS_SECRET_ACCESS_KEY': creds['secret_key'],
		'AWS_SECURITY_TOKEN': creds['session_token'],
		})
	'''

	print "Uploading %s" %(path)
	params = {'soft': True}
	url = urlparse.urljoin(server,f_obj.get('href'))
	r = encoded_get(url, auth=keypair, params=params)
	try:
		r.raise_for_status
	except:
		print "GET soft redirect failed: %s %s" %(r.status_code, r.reason)
		print r.text
		return
	full_url = r.json().['location']
	s3_filename = urlparse.urlparse(full_url).path
	s3_path = S3_BUCKET + s3_filename
	print path, s3_path
	try:
		subprocess.check_call(shlex.split("aws s3 --profile encode-prod cp %s %s" %(path, s3_path)))
	except subprocess.CalledProcessError as e:
		print("Upload failed with exit code %d" % e.returncode)
		return

	print "Patching %s" %(f_obj.get('accession'))
	notes_text = "ungzipped_md5=%s" %(ungzipped_md5.hexdigest())
	notes = f_obj.get('notes')
	if not notes:
		new_notes = notes_text
	else:
		new_notes = '%s; %s' %(notes, notes_text)
	patch_data = {
		"file_size": os.path.getsize(path),
		"md5sum": zipped_md5.hexdigest(),
		"notes": new_notes
	}
	uri = "/files/%s" %(f_obj.get('accession'))
	url = urlparse.urljoin(server,uri)
	r = encode_patch(url, auth=keypair, data=json.dumps(patch_data))
	try:
		r.raise_for_status
	except:
		print "PATCH failed: %s %s" %(r.status_code, r.reason)
		print r.text
		return

def main():
	global args
	args = get_args()

	authid, authpw, server = processkey(args.key)
	keypair = (authid,authpw)

	file_formats = ['bed'] #this should pull from the file object schema file_format_file_extension

	for file_format in file_formats:
		print file_format,
		query = '/search/?type=file&file_format=%s&frame=embedded&limit=all' %(file_format)
		url = urlparse.urljoin(server,query)
		print url
		response = encoded_get(url,auth=keypair)
		response.raise_for_status()
		files = response.json()['@graph']
		print "found %d files total." %(len(files))

		for f_obj in [f for f in files if f.get('accession') == 'ENCFF002DDZ'] :
			url = urlparse.urljoin(server,f_obj.get('href'))
			r = encoded_get(url, auth=keypair, allow_redirects=True, stream=True)
			try:
				r.raise_for_status
			except:
				print '%s href does not resolve' %(f_obj.get('accession'))
				continue
			s3_url = r.url
			r.close()
			o = urlparse.urlparse(s3_url)
			mahout_prefix = "/external/encode/s3/encode-files/"
			path = mahout_prefix.rstrip('/') + o.path
			try:
				magic_number = open(path,'rb').read(2)
			except IOError as e:
				print e
				continue
			else:
				is_gzipped = magic_number == b'\x1f\x8b'
				if not is_gzipped:
					if magic_number == 'ch':
						print "%s not gzipped" %(path)
						if not args.dryrun:
							gzip_and_post(f_obj, path, server, keypair, s3_url)
					else:
						print "%s not gzipped and does not start with ch" %(path)


if __name__ == '__main__':
	main()
