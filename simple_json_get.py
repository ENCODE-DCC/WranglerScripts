import requests

url = 'https://www.encodeproject.org/search/?' + \
	   'type=experiment&' + \
	   'assay_term_name=ChIP-seq&' + \
	   'organ_slims=lung&' + \
	   'frame=object&' + \
	   'format=json'

lung_experiments = requests.get(url, headers={'content-type': 'application/json'}).json()['@graph']

files = [experiment['files'] for experiment in lung_experiments]
