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

HEADERS = {'accept': 'application/json'}

keypair = getKeyPair('keypairs.json', 'test')

AUTHID = keypair[0]
AUTHPW = keypair[1]
URL = "https://www.encodeproject.org/biosamples/ENCBS780BKX/?frame=embedded&format=json"


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
	'donor': geoMinimisationCommon.donor_to_accession,
	'mutated_gene': geoMinimisationCommon.minimise_target,
	'littermates': geoMinimisationCommon.minimize_donors,
	'characterizations': geoMinimisationCommon.minimize_characterizations,
	'treatments':geoMinimisationCommon.minimize_treatments
}


values_to_retain = [
	"summary",
	"accession",
	"biosample_type",
	"biosample_term_name",
	"biosample_term_id",
	"description",
	"dbxrefs",
	"passage_number",
	"model_organism_mating_status",
	"subcellular_fraction_term_name",
	"subcellular_fraction_term_id",
	"phase",
	"url",
	"fly_synchronization_stage",
	"post_synchronization_time",
	"post_synchronization_time_units",
	"worm_synchronization_stage",
	"age_units",
	"sex",
	"health_status",
	"age",
	"life_stage"
]

def minimise_biosample(biosample_object):

	mini_dict = {}
	for key in biosample_object.keys():
		if key in values_to_retain:
			mini_dict[key]=biosample_object[key]
		else:
			if key in function_dispatch:
				mini_dict[key]=function_dispatch[key](biosample_object[key],False)
    			
    	
	return mini_dict

def main():
	response = requests.get(URL, auth=(AUTHID, AUTHPW), headers=HEADERS)
	response_json_dict = response.json()
	print (json.dumps( minimise_biosample(response_json_dict), indent=4, sort_keys=True))

	
if __name__ == "__main__":
    main()