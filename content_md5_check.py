#!/usr/bin/env python

import os, shutil, shlex, sys, subprocess, logging, re, json, urlparse, requests, time, gzip
import hashlib, cPickle

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
	for count in range(5):
		try:
			r = requests.patch(url, headers=headers, **kwargs)
		except requests.ConnectionError:
			continue
		else:
			return r


def gzip_and_post(f_obj, original_path, server, keypair):

	ungzipped_md5 = hashlib.md5()
	with open(original_path, 'rb') as f:
		for chunk in iter(lambda: f.read(1024*1024), ''):
			ungzipped_md5.update(chunk)

	work_path = os.path.join('/external/encode/fix_ungzipped',original_path.lstrip('/'))
	#print "Copying %s to %s" %(original_path, work_path)
	work_dir = os.path.dirname(work_path)
	if not os.path.exists(work_dir):
		os.makedirs(work_dir)
	shutil.copyfile(original_path, work_path)

	ungzipped_name = work_path.rpartition('.gz')[0]

	#print "Renaming %s to %s" %(work_path,ungzipped_name)
	os.rename(work_path,ungzipped_name)

	try:
		print "Gzipping",
		subprocess.check_call(['gzip', '-n', ungzipped_name])
	except subprocess.CalledProcessError as e:
		print "Gzip failed :%s" %(e)
		return
	else:
		print "complete"

	gzipped_md5 = hashlib.md5()
	with open(work_path, 'rb') as f:
		for chunk in iter(lambda: f.read(1024*1024), ''):
			gzipped_md5.update(chunk)
	
	#print "Uploading %s" %(work_path)
	params = {'soft': True}
	url = urlparse.urljoin(server,f_obj.get('href'))
	r = encoded_get(url, auth=keypair, params=params)
	try:
		r.raise_for_status
	except:
		print "GET soft redirect failed: %s %s" %(r.status_code, r.reason)
		print r.text
		return
	full_url = r.json()['location']
	s3_filename = urlparse.urlparse(full_url).path
	s3_path = S3_BUCKET + s3_filename
	#print work_path, s3_path
	try:
		out = subprocess.check_output(shlex.split("aws s3 cp %s s3://%s --profile encode-prod" %(work_path, s3_path)))
		print out.rstrip()
	except subprocess.CalledProcessError as e:
		print("Upload failed with exit code %d" % e.returncode)
		return

	print "Patching %s" %(f_obj.get('accession'))
	patch_data = {
		"file_size": os.path.getsize(work_path),
		"md5sum": gzipped_md5.hexdigest()
	}
	uri = "/files/%s" %(f_obj.get('accession'))
	url = urlparse.urljoin(server,uri)
	r = encoded_patch(url, auth=keypair, data=json.dumps(patch_data))
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

	#file_formats = ['bed'] #this should pull from the file object schema file_format_file_extension
	file_formats = ['fastq'] #this should pull from the file object schema file_format_file_extension
	for file_format in file_formats:
		print file_format,
		query = '/search/?type=file&file_format=%s&field=accession&field=href&field=dataset&field=status&field=lab&format=json&limit=all' %(file_format)
		url = urlparse.urljoin(server,query)
		print url
		response = encoded_get(url,auth=keypair)
		response.raise_for_status()
		all_files = response.json()['@graph']
		files = []
		status_to_ignore = ['deleted','revoked','replaced']
		for f in all_files:
			if 'status' not in f:
				print '%s has no status.  Skipping' %(f.get('accession'))
			else:
				if f['status'] not in status_to_ignore:
					files.append(f)
		print "found %d files total not of status %s." %(len(files), ', '.join(status_to_ignore))

		#for f_obj in [f for f in files if f.get('accession') == 'ENCFF915YMM']: #.bed.gz E3 from Ren
		#for f_obj in [f for f in files if f.get('accession') in ['ENCFF002END', 'ENCFF915YMM']]:
		md5sums = {}
		for f_obj in files:
			sys.stdout.write('.')
			sys.stdout.flush()
			url = urlparse.urljoin(server,f_obj.get('href'))
			r = encoded_get(url, auth=keypair, allow_redirects=True, stream=True)
			try:
				r.raise_for_status
			except:
				print >> sys.stderr, '%s href does not resolve' %(f_obj.get('accession'))
				continue
			s3_url = r.url
			r.close()
			o = urlparse.urlparse(s3_url)
			mahout_prefix = "/external/encode/s3/encode-files/"
			path = mahout_prefix.rstrip('/') + o.path
			try:
				fh = open(path,'rb')
				magic_number = fh.read(2)
				fh.close()
			except IOError as e:
				print >> sys.stderr, e
				continue
			else:
				is_gzipped = magic_number == b'\x1f\x8b'
				if is_gzipped:
					fh = gzip.open(path,'rb')
					m = hashlib.md5()
					m.update(fh.read(100000))
					md5sum = m.hexdigest()
					file_info = {'accession': f_obj['accession'], 'dataset': f_obj['dataset'], 'lab': f_obj['lab']}
					if md5sum in md5sums:
						md5sums[md5sum].append(file_info)
						print '\n'
						print md5sums[md5sum]
					else:
						md5sums.update({md5sum: [file_info]})
					fh.close()
				else:
					print >> sys.stderr, "%s not gzipped" %(path)
		for md5sum,duplicate_files in md5sums.iteritems():
			if len(duplicate_files) > 1:
				print >> sys.stderr, duplicate_files
		with open("%s_md5sums.pkl" %(file_format),'wb') as outfh:
			cPickle.dump(md5sums,outfh)

if __name__ == '__main__':
	main()
