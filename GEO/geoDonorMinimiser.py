import  requests, json, sys, geoMinimisationCommon 
HEADERS = {'accept': 'application/json'}
def getKeyPair(path_to_key_pair_file, server_name):
    keysf = open(path_to_key_pair_file, 'r')
    keys_json_string = keysf.read()
    keysf.close()
    keys = json.loads(keys_json_string)
    key_dict = keys[server_name]
    AUTHID = key_dict['key']
    AUTHPW = key_dict['secret']
    return (AUTHID, AUTHPW)


keypair = getKeyPair('keypairs.json', 'test')

AUTHID = keypair[0]
AUTHPW = keypair[1]
URL = "https://www.encodeproject.org/human-donors/ENCDO008MFT/?frame=embedded&format=json"

function_dispatch = {
    'organism': geoMinimisationCommon.minimise_organism,
    'source': geoMinimisationCommon.minimise_source,
    'lab': geoMinimisationCommon.minimise_lab,
    'references': geoMinimisationCommon.minimise_references,
    'documents': geoMinimisationCommon.minimise_documents,
    'protocol_documents': geoMinimisationCommon.minimise_protocol_documents,
    'fraternal_twin': geoMinimisationCommon.donor_to_accession,
	'identical_twin': geoMinimisationCommon.donor_to_accession,
	'siblings': geoMinimisationCommon.minimize_donors,
	'children': geoMinimisationCommon.minimize_donors,
	'outcrossed_strain': geoMinimisationCommon.donor_to_accession,
	'mutated_gene': geoMinimisationCommon.minimise_target,
	'littermates': geoMinimisationCommon.minimize_donors,
	'characterizations': geoMinimisationCommon.minimize_characterizations,
}

values_to_retain_dictionary = {
	'Homo sapiens':['url','accession','sex','age','age_units','life_stage','health_status','ethnicity','dbxrefs'],
	'Mus musculus':['url','accession','strain_name','strain_background','dbxrefs'],
	'Drosophila melanogaster':['url','accession','strain_name','strain_background','mutagen','genotype','dbxrefs'],
	'Caenorhabditis elegans':['num_times_outcrossed','url','accession','strain_name','strain_background','mutagen','genotype','dbxrefs']
	}



def minimise_donor(donor_object):
	donor_organism_scientific_name = geoMinimisationCommon.minimise_organism(donor_object['organism'], True)
	retained_values = values_to_retain_dictionary[donor_organism_scientific_name]
	#print (donor_object)
	#print ("-----------")
	mini_dict = {}
	for key in donor_object.keys():
		if key in retained_values:
			mini_dict[key]=donor_object[key]
		else:
			if key in function_dispatch:
				mini_dict[key]=function_dispatch[key](donor_object[key],True)
    			
    	
	return mini_dict

def main():
	response = requests.get(URL, auth=(AUTHID, AUTHPW), headers=HEADERS)
	response_json_dict = response.json()
	print (json.dumps( minimise_donor(response_json_dict), indent=4, sort_keys=True))

	
if __name__ == "__main__":
    main()