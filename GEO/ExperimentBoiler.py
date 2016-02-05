
import json

''' script for boiling down experiment json objects
each field deemed as important will stay, while the unimportant fields will be removed '''

# organism object is replaced by organism scientific name
def boildown_organism(organism_object):
    return organism_object['scientific_name']

# award object is replaced by the name of the award
def boildown_award(award_object):
    return award_object['name']

# source object is replaced by the title of the source
def boildown_source(source_object):
    return source_object['title']

# lab object is replaced by the title of the lab
def boildown_lab(lab_object):
    return lab_object['title']

# check if the target object is a control or gene-target type
def is_control_target(target_object):
    for entry in target_object['investigated_as']:
        if entry == 'control':
            return True
    return False

# list of reference objects is replaced by boiled_down publications
def boildown_references(references_list):
    listToReturn = []
    for publicationObject in references_list:
        listToReturn.append(boildown_publication(publicationObject))
    return listToReturn

# publication object is replaced by publicatio identifiers (like Pubmed id)
def boildown_publication(publication_object):
    return publication_object['identifiers']

# document object is replaced by dictionary containing boiled down attachments and references in addition of a url if it exists
def boildown_document(document_object):
    documentDictionary = {}
    if 'attachment' in document_object:
        documentDictionary['attachment']=boildown_attachment(document_object['attachment'])
    if 'urls' in document_object:
        documentDictionary['urls']=document_object['urls']
    if 'references' in document_object:
        documentDictionary['references'] = boildown_references(document_object['references'])
    return documentDictionary

# attachment is replaced by dictionary of (md5sum and href) entries
def boildown_attachment(attachment_dict):
    dictionaryToReturn = {}
    for key in attachment_dict:
        if key in attachment_interesting_values:
            dictionaryToReturn[key]=attachment_dict[key]
    return dictionaryToReturn

# list of documents is replaced by list containing results of boildown_document() function calls
def boildown_documents(documents_list):
    listToReturn = []
    for documentObject in documents_list:
        listToReturn.append(boildown_document(documentObject))
    return listToReturn

# donor object is replaced by limited set (donor_interesting_values list) of its properties
def boildown_donor(donor_object):
    donorDictionary = {}
    for key in donor_object.keys():
        if key in donor_interesting_values:
            donorDictionary[key]=donor_object[key]
        if key == 'target' or key == 'mutated_gene':
            if is_control_target(donor_object[key]) == False:
                donorDictionary[key] = donor_object[key]['label']
    return donorDictionary

# constructs list is replaced by a list of boiled down construct objects
def boildown_constructs(constructs_list):
    listToReturn = []
    for entry in constructs_list:
        listToReturn.append(boildown_construct(entry))
    return listToReturn

# construct object is replaced by dictionary containing values form construct_interesting_values list and target and documents objects boiled down
def boildown_construct(construct_object):
    construct_dictionary = {}
    for key in construct_object.keys():
        if key in construct_interesting_values:
            construct_dictionary[key]=construct_object[key]
        if key == 'target':
            if is_control_target(construct_object[key]) == False:
                construct_dictionary[key] = construct_object[key]['label']
        if key == 'documents':
            construct_dictionary[key] = boildown_documents(construct_object[key])

    return construct_dictionary

# protocol documents are replaced by a list that is returned by boildown_documents() function call
def boildown_protocol_documents(documents_list):
    return boildown_documents(documents_list)

def boildown_replicates(replicates_list):
    listToReturn = []
    for entry in replicates_list:
        listToReturn.append(boildown_replicate(entry))
    return listToReturn

def boildown_replicate(replicate_object):
    replicate_dictionary = {}
    for key in replicate_object.keys():
        if key in replicate_simple_interesting_values:
            replicate_dictionary[key]=replicate_object[key]
        if key == 'library':
            replicate_dictionary[key]=boildown_library(replicate_object[key])
    return replicate_dictionary

def boildown_files(files_list):
    listToReturn = []
    for entry in files_list:
        listToReturn.append(boildown_file(entry))
    return listToReturn

def boildown_file(file_object):
    file_dictionary = {}
    for key in file_object.keys():
        if key in file_interesting_values:
            file_dictionary[key]=file_object[key]
        if key=='platform':
            file_dictionary[key]=boildown_platform(file_object[key])
        if key=='replicate':
            file_dictionary[key]={'biological_replicate_number':file_object[key]['biological_replicate_number'],'technical_replicate_number':file_object[key]['technical_replicate_number']}
        if key=='derived_from':
            file_dictionary[key]=boildown_derived_from(file_object[key])
    return file_dictionary


def boildown_platform(platform_object):
    platform_dictionary = {}
    for key in platform_object.keys():
        if key in platform_interesting_values:
            platform_dictionary[key]=platform_object[key]
    return platform_dictionary
def boildown_derived_from(derived_from_list):
    listToReturn = []
    for entry in derived_from_list:
        listToReturn.append(entry['accession'])
    return listToReturn

def boildown_spikeins(spikeins_list):
    listToReturn = []
    for entry in spikeins_list:
        listToReturn.append(boildown_spikein(entry))
    return listToReturn

def boildown_spikein(spikein_object):
    spikein_dictionary = {}
    for key in spikein_object.keys():
        if key in spikein_simple_interesting_values:
            spikein_dictionary[key]=spikein_object[key]
    return spikein_dictionary

def boildown_library(library_object):
    library_dictionary = {}
    for key in library_object.keys():
        if key in library_simple_interesting_values:
            library_dictionary[key]=library_object[key]
        if key=='biosample':
            library_dictionary[key]=library_object[key]['accession']
        if key == 'spikeins_used':
            library_dictionary[key]=boildown_spikeins(library_object[key])
    return library_dictionary



# same as in biosample
platform_interesting_values = ['dbxrefs','term_id','term_name']
file_interesting_values = ['accession','md5sum','output_type','file_format','file_type','href','content_md5sum','read_length','read_length_units','file_size','run_type','output_category']
attachment_interesting_values = ['md5sum','href']
construct_interesting_values = ['construct_type','description','url']
donor_interesting_values = ['accession', 'strain_name', 'strain_background', 'sex', 'life_stage', 'health_status', 'alternate_accessions', 'ethnicity', 'genotype' , 'mutagen']
# values from experiment that does not require in deep inspection (no embedded things here)
experiment_simple_interesting_values = ['date_released','accession','alternate_accessions','assay_term_id', 'biosample_term_id', 'biosample_type', 'assay_term_name', 'assembly','assay_synonyms','description', 'dbxrefs', 'biosample_synonyms', 'biosample_term_name']
replicate_simple_interesting_values = ['biological_replicate_number','technical_replicate_number']
library_simple_interesting_values = ['accession','nucleic_acid_starting_quantity_units','fragmentation_method','strand_specificity','library_size_selection_method','nucleic_acid_term_name','nucleic_acid_term_id','size_range','nucleic_acid_starting_quantity']
spikein_simple_interesting_values = ['accession','alternate_accessions','dbxrefs', 'description']





function_dispatch = {
    'organism': boildown_organism,
    'award': boildown_award,
    'source': boildown_source,
    'donor': boildown_donor,
    'lab': boildown_lab,
    'references': boildown_references,
    'constructs': boildown_constructs,
    'protocol_documents': boildown_protocol_documents,
    'documents' : boildown_documents,
    'files': boildown_files,
    'replicates': boildown_replicates,
    'spikeins_used': boildown_spikeins,
    'library': boildown_library,
}


########################################
###### Example of usage ################
########################################

#with open("/Users/idan/Documents/GEO/example/ENCBS778MKB.json", encoding='utf-8') as data_file:
#with open("/Users/idan/Documents/GEO/example/ENCBS823IZS.json", encoding='utf-8') as data_file:
with open("/Users/idan/Documents/GEO/example/ENCSR236EGS.json", encoding='utf-8') as data_file:
    data = json.loads(data_file.read())


#creating json dictioanry
json_dict = {}
for entry in data.keys():
    if entry in function_dispatch: # dealing with complex entries
        json_dict[entry]=function_dispatch[entry](data[entry])
    else:
        if entry in experiment_simple_interesting_values: #dealing with simple entries
            json_dict[entry]=data[entry]

print (json.dumps(json_dict, indent=4, sort_keys=True))

