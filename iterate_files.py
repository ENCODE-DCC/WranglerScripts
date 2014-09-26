import requests, subprocess, shlex, urlparse, os

AUTHID='user'; AUTHPW='passwd'; HEADERS = {'content-type': 'application/json'}; SERVER = 'https://www.encodeproject.org/'
S3_SERVER='s3://encode-files/'

files = requests.get(
	'https://www.encodeproject.org/search/?type=file&frame=embedded&limit=all',
	auth=(AUTHID,AUTHPW), headers=HEADERS).json()['@graph']

iter_files = [f for f in files if f.get('lab') == '/labs/brenton-graveley/']

for f_obj in iter_files[50:52]:
	#make the URL that will get redirected
	encode_url = urlparse.urljoin(SERVER,f_obj.get('href'))

	#stream=True avoids actually downloading the file, but it evaluates the redirection
	r = requests.get(encode_url, auth=(AUTHID,AUTHPW), headers=HEADERS, allow_redirects=True, stream=True)
	
	#this is the actual URL after redirection
	s3_url = r.url
	
	#release the connection
	r.close()
	
	#split up the url into components
	o = urlparse.urlparse(s3_url)
	
	#pull out the filename
	filename = os.path.basename(o.path)
	
	#hack together the s3 cp url
	bucket_url = S3_SERVER.rstrip('/') + o.path
	
	#ls the file from the bucket
	print subprocess.check_output(shlex.split('aws s3 ls %s' %(bucket_url)))

	#do the actual s3 cp
	return_value = subprocess.check_call(shlex.split('aws s3 cp %s %s' %(bucket_url, filename)))

	#make sure it's here
	print subprocess.check_output(shlex.split('ls -l %s' %(filename)))

	#calculate the md5
	md5 = subprocess.check_output(shlex.split('md5 -q %s' %(filename))).rstrip()
	print md5
	if str(f_obj.get('md5sum')) == str(md5):
		pass
	else:
		accession = f_obj.get('accession')
		print "%s: md5 mismatch (%s.md5=%s, calculated=%s)" %(accession, accession, f_obj.get('md5sum'), md5)
	# do whatever else you want with the file

	# remove the file when you're done
	return_value = subprocess.check_call(shlex.split('rm %s' %(filename)))

	#I'm just breaking here so we don't download everything while we're testing
	break