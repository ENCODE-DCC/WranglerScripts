'''
Common functions for GEO Minimization of the JSON objects
'''

def minimise_organism(organism_object, donor_flag):
    # object in donor and in biosample
    return organism_object['scientific_name']
	
def minimise_award(award_object, donor_flag):
    # object in biosample, string in donor
    if donor_flag==True:
        return award_object.split("/")[2]
    else:
        return award_object['name']

def minimise_source(source_object, donor_flag):
    # object in biosample, string in donor
    if donor_flag==True:
        return source_object.split("/")[2]
    else:
        return source_object['title']

def minimise_lab(lab_object, donor_flag):
    # object in biosample, string in donor
    if donor_flag == True:
        return lab_object.split("/")[2]
    else:
        return lab_object['title']

def minimise_references(references_list, donor_flag):
    list_to_return = []
    for publication_object in references_list:
        list_to_return.append(minimise_publication(publication_object, donor_flag))
    return list_to_return

def minimise_document(document_object, donor_flag):
    document_dictionary = {}
    if 'attachment' in document_object:
        document_dictionary['attachment']=minimise_attachment(document_object['attachment'], donor_flag, document_object['@id'])
    if 'urls' in document_object:
        document_dictionary['urls']=document_object['urls']
    if 'references' in document_object:
        document_dictionary['references'] = minimise_references(document_object['references'], donor_flag)
    return document_dictionary

def minimise_attachment(attachment_dict, donor_flag, attachment_id):
    return attachment_id+attachment_dict['href']

def minimise_documents(documents_list, donor_flag):
    list_to_return = []
    for document_object in documents_list:
        list_to_return.append(minimise_document(document_object, donor_flag))
    return list_to_return

def minimise_publication(publication_object, donor_flag):
    return publication_object['identifiers']


def minimise_constructs(constructs_list, donor_flag):
    list_to_return = []
    for entry in constructs_list:
        list_to_return.append(minimise_construct(entry, donor_flag))
    return list_to_return

def minimise_construct(construct_object, donor_flag):
    construct_dictionary = {}
    for key in construct_object.keys():
        if key in construct_interesting_values:
            construct_dictionary[key]=construct_object[key]
        if key == 'target':
            if is_control_target(construct_object[key]) == False:
                construct_dictionary[key] = construct_object[key]['label']
        if key == 'documents':
            construct_dictionary[key] = minimise_documents(construct_object[key], donor_flag)
    return construct_dictionary

def minimise_protocol_documents(documents_list, donor_flag):
    return minimise_documents(documents_list, donor_flag)

def minimize_characterizations(characterizations_list, donor_flag):
    list_to_return = []
    for entry in characterizations_list:
        list_to_return.append(minimise_characterization(entry, donor_flag))
    return list_to_return

def minimize_characterization(characterization_object, donor_flag):
    interesting = ['primary_characterization_method','secondary_characterization_method','characterization_method']
    characterization_dictionary = {}
    for key in characterization_object.keys():
        if key in interesting:
            characterization_dictionary[key]=characterization_object[key]
        else:
            if key == 'references':
                characterization_dictionary[key] = minimise_references(characterization_object[key], donor_flag)
            else:
                if key == 'target':
                    characterization_dictionary[key] = minimise_target(characterization_object[key], donor_flag)
    
    return characterization_dictionary

def minimize_donors(donors_list, donor_flag):
    if donor_flag == True:
        list_to_return = []
        for entry in donors_list:
            list_to_return.append(entry.split("/")[2])
        return list_to_return
    else:
        list_to_return = []
        for entry in donors_list:
            list_to_return.append(donor_to_accession(entry))
        return list_to_return

def donor_to_accession(donor_object, donor_flag):
    return donor_object['accession']

# check if the target object is a control or gene-target type
def is_control_target(target_object, donor_flag):
    for entry in target_object['investigated_as']:
        if entry == 'control':
            return True
    return False

def minimise_target(target_object,donor_flag):
    if is_control_target(target_object) == False:
        return target_object['label']
    else:
        return None

def minimize_treatments(treatments_list,donor_flag):
    list_to_return = []
    for treatment in treatments_list:
        list_to_return.append(minimize_treatment(treatment))
    return list_to_return

def minimize_treatment(treatment_object):
    treatment_dict = {}
    for key in treatment_object.keys():
        if key in ['treatment_type','dbxrefs','treatment_term_name','treatment_term_id','concentration','concentration_units','duration','duration_units','temperature','temperature_units']:
            treatment_dict[key]=treatment_object[key] 
    return treatment_dict

def main():
    print ("Common functions for GEO-JSON objects minimisation")
    
if __name__ == "__main__":
    main()