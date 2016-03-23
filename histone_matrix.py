import sys
import requests
import urlparse
from time import sleep
import csv
import json

GET_HEADERS = {'accept': 'application/json'}


def get_ENCODE(obj_id, SERVER, AUTHID, AUTHPW, HEADERS):
    '''GET an ENCODE object as JSON and return as dict
    '''
    DEBUG_ON = False
    url = SERVER+obj_id+'?limit=all'
    if DEBUG_ON:
        print "DEBUG: GET %s" % (url)
    response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
    if DEBUG_ON:
        print "DEBUG: GET RESPONSE code %s" % (response.status_code)
        try:
            if response.json():
                print "DEBUG: GET RESPONSE JSON"
                print json.dumps(response.json(), indent=4, separators=(',', ': '))
        except:
            print "DEBUG: GET RESPONSE text %s" % (response.text)
    if not response.status_code == requests.codes.ok:
        response.raise_for_status()
    return response.json()

def encoded_get(url, keypair=None, frame='object', return_response=False):
    url_obj = urlparse.urlsplit(url)
    new_url_list = list(url_obj)
    query = urlparse.parse_qs(url_obj.query)
    if 'format' not in query:
        new_url_list[3] += "&format=json"
    if 'frame' not in query:
        new_url_list[3] += "&frame=%s" % (frame)
    if 'limit' not in query:
        new_url_list[3] += "&limit=all"
    if new_url_list[3].startswith('&'):
        new_url_list[3] = new_url_list[3].replace('&', '', 1)
    get_url = urlparse.urlunsplit(new_url_list)
    max_retries = 10
    max_sleep = 10
    while max_retries:
        try:
            if keypair:
                response = requests.get(get_url,
                                        auth=keypair,
                                        headers=GET_HEADERS)
            else:
                response = requests.get(get_url, headers=GET_HEADERS)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.SSLError) as e:
            print >> sys.stderr, e
            sleep(max_sleep - max_retries)
            max_retries -= 1
            continue
        else:
            if return_response:
                return response
            else:
                return response.json()


def is_interesting(experiment):
    if experiment['status'] in ['revoked', 'replaced', 'deleted']:
        return False
    return True


def is_replicated(experiment):
    if 'replication_type' in experiment and \
       experiment['replication_type'] == 'unreplicated':
        return False
    if 'audit' in experiment:
        list_of_audits = []
        if 'NOT_COMPLIANT' in experiment['audit']:
            list_of_audits.extend(experiment['audit']['NOT_COMPLIANT'])
        if 'WARNING' in experiment['audit']:
            list_of_audits.extend(experiment['audit']['WARNING'])
        for au in list_of_audits:
            if au['category'] in ['unreplicated experiment']:
                return False
    return True


def is_antibody_eligible(experiment):
    if 'audit' in experiment:
        if 'NOT_COMPLIANT' in experiment['audit']:
            for au in experiment['audit']['NOT_COMPLIANT']:
                if au['category'] in ['not eligible antibody']:
                    return False
    return True


def is_not_missing_antibody(experiment):
    if 'audit' in experiment:
        if 'ERROR' in experiment['audit']:
            for au in experiment['audit']['ERROR']:
                if au['category'] in ['missing antibody']:
                    return False
    return True


def is_not_missing_controls(experiment):
    if 'audit' in experiment:
        if 'NOT_COMPLIANT' in experiment['audit']:
            for au in experiment['audit']['NOT_COMPLIANT']:
                if au['category'] in ['missing possible_controls',
                                      'missing controlled_by']:
                    return False
    return True


def is_not_mismatched_controlled_by(experiment):
    if 'audit' in experiment:
        if 'ERROR' in experiment['audit']:
            for au in experiment['audit']['ERROR']:
                if au['category'] in ['mismatched controlled_by']:
                    return False
    return True


def is_not_mismatched_controlled_by_run_type(experiment):
    if 'audit' in experiment:
        if 'WARNING' in experiment['audit']:
            for au in experiment['audit']['WARNING']:
                if au['category'] in ['mismatched controlled_by run_type']:
                    return False
    return True


def is_not_mismatched_controlled_by_read_length(experiment):
    if 'audit' in experiment:
        if 'WARNING' in experiment['audit']:
            for au in experiment['audit']['WARNING']:
                if au['category'] in ['mismatched controlled_by read length']:
                    return False
    return True


def is_not_missing_paired_with(experiment):
    if 'audit' in experiment:
        if 'NOT_COMPLIANT' in experiment['audit']:
            for au in experiment['audit']['NOT_COMPLIANT']:
                if au['category'] in ['missing paired_with']:
                    return False
    return True


def contains_duplicated_fastqs(experiment, server):
    if 'original_files' in experiment:
        for f in experiment['original_files']:
            file_object = encoded_get(server+f, keypair)
            if file_object['status'] not in FILE_IGNORE_STATUS and \
               file_object['file_format'] == 'fastq':
                content_md5_sum = file_object['content_md5sum']
                if encoded_get(server+'/search/?type=file&content_md5sum=%s' %
                   (content_md5_sum), keypair)['total'] > 1:
                    return True
    return False


def is_insufficient_read_depth(experiment):
    if 'audit' in experiment:
        list_of_audits = []
        if 'NOT_COMPLIANT' in experiment['audit']:
            list_of_audits.extend(experiment['audit']['NOT_COMPLIANT'])
        if 'WARNING' in experiment['audit']:
            list_of_audits.extend(experiment['audit']['WARNING'])
        for au in list_of_audits:
            if au['category'] in ['insufficient read depth']:
                return False
    return True


def is_insufficient_library_complexity(experiment):
    if 'audit' in experiment:
        if 'NOT_COMPLIANT' in experiment['audit']:
            for au in experiment['audit']['NOT_COMPLIANT']:
                if au['category'] in ['insufficient library complexity']:
                    return False
        if 'WARNING' in experiment['audit']:
            for au in experiment['audit']['WARNING']:
                if au['category'] in ['low library complexity']:
                    return False
    return True


def getKeyPair(path_to_key_pair_file, server_name):
    keysf = open(path_to_key_pair_file, 'r')
    keys_json_string = keysf.read()
    keysf.close()
    keys = json.loads(keys_json_string)
    key_dict = keys[server_name]
    AUTHID = key_dict['key']
    AUTHPW = key_dict['secret']
    return (AUTHID, AUTHPW)

CORE_MARKS = ['H3K27ac', 'H3K27me3', 'H3K36me3', 'H3K4me1',
              'H3K4me3', 'H3K9me3']
EXPERIMENT_IGNORE_STATUS = ['deleted', 'revoked', 'replaced']
FILE_IGNORE_STATUS = ['deleted', 'revoked', 'replaced',
                      'upload failed', 'format check failed', 'uploading']


'''
PLACE TO MODIFY TO GET RESULTS YOU WANT
'''

keypair = getKeyPair('keypairs.json', 'test')
server = 'https://www.encodeproject.org/'


lab = '&lab.title=Bing Ren, UCSD'
organism = '&replicates.library.biosample.donor.organism.scientific_name=Mus musculus'

#lab = '&lab.title=Bradley Bernstein, Broad'
#organism = '&replicates.library.biosample.donor.organism.scientific_name=Homo sapiens'

#target_investigated_as = "histone"
target_investigated_as = "transcription factor"

path_to_output_1 = "/Users/idan/Desktop/matrix.csv"
path_to_output_2 = "/Users/idan/Desktop/matrix_reps.csv"

histone_experiments_pages = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=' + target_investigated_as + lab +
                              '&format=json&frame=page&limit=all', keypair)['@graph']
print ("retreived "+str(len(histone_experiments_pages)) + " experiment pages")

histone_controls_pages = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=control' + lab +
                              '&format=json&frame=page&limit=all', keypair)['@graph']
print ("retreived "+str(len(histone_controls_pages)) + " control pages")

histone_experiments_objects = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=' + target_investigated_as + lab +
                              '&format=json&frame=embedded&limit=all', keypair)['@graph']
print ("retreived "+str(len(histone_experiments_objects)) + " experiment objects")

histone_controls_objects = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=control' + lab +
                              '&format=json&frame=embedded&limit=all', keypair)['@graph']
print ("retreived "+str(len(histone_controls_objects)) + " control objects")

matrix = {}
control_matrix = {}
sample_types = set()
marks = set()

histone_experiments_dict = {}
for entry in histone_experiments_pages:
    histone_experiments_dict[entry['accession']] = {'page': entry}
for entry in histone_experiments_objects:
    histone_experiments_dict[entry['accession']]['object'] = entry
    sample = entry['biosample_term_name']
    mark = entry['target']['label']
    if mark not in matrix:
        matrix[mark] = {}
    if sample not in matrix[mark]:
        matrix[mark][sample] = []

    if 'aliases' in entry:
        matrix[mark][sample].append((entry['accession'], entry['aliases']))
    else:
        matrix[mark][sample].append((entry['accession'], 'NO ALIASES'))

    sample_types.add(sample)

    marks.add(mark)


histone_controls_dict = {}
for entry in histone_controls_pages:
    histone_controls_dict[entry['accession']] = {'page': entry}
for entry in histone_controls_objects:
    histone_controls_dict[entry['accession']]['object'] = entry

    sample = entry['biosample_term_name']
    mark = 'control'
    if mark not in control_matrix:
        control_matrix[mark] = {}
    if sample not in control_matrix[mark]:
        control_matrix[mark][sample] = []

    if 'aliases' in entry:
        control_matrix[mark][sample].append((entry['accession'], entry['aliases']))
    else:
        control_matrix[mark][sample].append((entry['accession'], 'NO ALIASES'))

    sample_types.add(sample)

    marks.add(mark)

mone = 0
for ac in histone_experiments_dict:
    page = histone_experiments_dict[ac]['page']
    obj = histone_experiments_dict[ac]['object']
    mone += 1
    #  check only experiments that are not DELETED/REVOKED/REPLACED
    if is_interesting(obj):
        if mone % 10 == 0:
            print 'processed '+str(mone) + ' out of ' + \
                  str(len(histone_experiments_dict.keys()))

        statuses = {'replication': [], 'antibody': [], 'control': [], 'files': [], 'qc': []}
        if is_replicated(obj) is False or is_replicated(page) is False:
            statuses['replication'].append('unreplicated')
        if is_antibody_eligible(page) is False:
            statuses['antibody'].append('not eligible antybody')
        if is_not_missing_antibody(page) is False:
            statuses['antibody'].append('missing antybody')
        if is_not_mismatched_controlled_by(page) is False:
            statuses['control'].append('mismatched controled_by')
        if is_not_mismatched_controlled_by_run_type(page) is False:
            statuses['control'].append('mismatched controled_by run_type')
        if is_not_mismatched_controlled_by_read_length(page) is False:
            statuses['control'].append('mismatched controled_by read_length')
        if is_not_missing_controls(page) is False:
            statuses['control'].append('missing control')
        if is_not_missing_paired_with(page) is False:
            statuses['files'].append('missing paired_with files')
        if is_insufficient_read_depth(page) is False:
            statuses['qc'].append('insufficient read depth')
        if is_insufficient_library_complexity(page) is False:
            statuses['qc'].append('insufficient library complexity')

        if is_not_missing_controls(page) is True and \
           is_not_mismatched_controlled_by(page) is True:
            not_encode_3_flag = False
            for entry in obj['possible_controls']:
                control_accession = entry['accession']
                if control_accession in histone_controls_dict:
                    control_page = histone_controls_dict[control_accession]['page']
                    if is_insufficient_read_depth(control_page) is False:
                        statuses['control'].append('insufficient read '
                                                   'depth in control')
                    if is_insufficient_library_complexity(control_page) is False:
                        statuses['control'].append('insufficient library '
                                                   'complexity in control')
                else:
                    not_encode_3_flag = True
            if (not_encode_3_flag is True):
                statuses['control'].append('non ENCODE3 control')

        histone_experiments_dict[ac]['statuses'] = statuses

        rep_dict = {}
        for file_id in obj['original_files']:           
            file_object = get_ENCODE(file_id.split('/')[2], server, keypair[0], keypair[1], GET_HEADERS)
            if file_object['status'] in ['deleted', 'replaced', 'revoked']:
                continue
            if file_object['file_format'] == 'fastq':
                if 'replicate' in file_object:
                    bio_rep_number = file_object['replicate']['biological_replicate_number']
                    tec_rep_number = file_object['replicate']['technical_replicate_number']
                    key = (bio_rep_number,tec_rep_number)
                    if key not in rep_dict:
                        rep_dict[key] = set()
                    if 'read_length' in file_object and 'run_type' in file_object:
                        if file_object['run_type'] == 'single-ended':
                            record_val = str(file_object['read_length'])+'SE'
                        else:
                            record_val = str(file_object['read_length'])+'PE'
                        rep_dict[key].add(record_val)
        seq_info_string = ''
        for k in sorted(rep_dict.keys()):
            reps_string = ''
            for member in rep_dict[k]:
                reps_string += member + ', '
            seq_info_string += 'REP' + str(k[0]) + '.' + str(k[1]) + ' ' +reps_string[:-2]+'\r'

        histone_experiments_dict[ac]['seq_info'] = seq_info_string

        #print (ac)
        #print (histone_experiments_dict[ac]['seq_info'])

#print ("-------------")
mone = 0
for ac in histone_controls_dict:
    mone += 1

    page = histone_controls_dict[ac]['page']
    obj = histone_controls_dict[ac]['object']
    if is_interesting(obj):
        if mone % 10 == 0:
            print 'processed '+str(mone) + ' out of ' + str(len(histone_controls_dict.keys()))
        statuses = {'replication': [], 'files': [], 'qc': []}
        if is_replicated(obj) is False or is_replicated(page) is False:
            statuses['replication'].append('unreplicated')
        if is_not_missing_paired_with(page) is False:
            statuses['files'].append('missing paired_with files')
        if is_insufficient_read_depth(page) is False:
            statuses['qc'].append('insufficient read depth')
        if is_insufficient_library_complexity(page) is False:
            statuses['qc'].append('insufficient library complexity')

    histone_controls_dict[ac]['statuses'] = statuses
    rep_dict = {}
    for file_id in obj['original_files']:     
        file_object = get_ENCODE(file_id.split('/')[2], server, keypair[0], keypair[1], GET_HEADERS)
        if file_object['status'] in ['deleted', 'replaced', 'revoked']:
            continue
        if file_object['file_format'] == 'fastq':
            #print (file_object['accession'])
            if 'replicate' in file_object:
                bio_rep_number = file_object['replicate']['biological_replicate_number']
                tec_rep_number = file_object['replicate']['technical_replicate_number']
                key = (bio_rep_number,tec_rep_number)
                if key not in rep_dict:
                    rep_dict[key] = set()
                if 'read_length' in file_object and 'run_type' in file_object:
                    if file_object['run_type'] == 'single-ended':
                        record_val = str(file_object['read_length'])+'SE'
                    else:
                        record_val = str(file_object['read_length'])+'PE'
                    rep_dict[key].add(record_val)
    seq_info_string = ''
    for k in sorted(rep_dict.keys()):
        reps_string = ''
        for member in rep_dict[k]:
            reps_string += member + ', '
        seq_info_string += 'REP' + str(k[0]) + '.' + str(k[1]) + ' ' +reps_string[:-2]+'\r'
    histone_controls_dict[ac]['seq_info'] = seq_info_string
    #print (ac)
    #print (histone_controls_dict[ac]['seq_info'])
    
# we have matrix dictionary for the matrix creation - each cell contains a lit of all the accessions
# we have the histone_experiments_dict that for each accession has a list of statuses ['replication', 'antibody', control']

if target_investigated_as == "histone":

    marks_to_print = ['control']
    marks_to_print.extend(CORE_MARKS)
    for m in marks:
        if m not in CORE_MARKS and m != 'control':
            marks_to_print.append(m)
else:
    marks_to_print = ['control']
    for m in marks:
        if m != 'control':
            marks_to_print.append(m)

#output = open("/Users/idan/Desktop/mat.csv", "w")
with open(path_to_output_1, 'wb') as output:
    fields = ['sample'] + marks_to_print
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for sample in sample_types:
        row = {'sample': sample}


        for mark in marks_to_print:
            if mark != 'control':
                if sample in matrix[mark]:
                    total = len(matrix[mark][sample])

                    accessionStatuses = {}
                    aliases = {}
                    for (acc, al) in matrix[mark][sample]:
                        aliases[acc] = al
                        accessionStatuses[acc] = []
                        statuses = histone_experiments_dict[acc]['statuses']

                        for k in statuses:
                            if len(statuses[k]) > 0:
                                statuses_string = ''
                                for status in statuses[k]:
                                    statuses_string += '-' + status + '\r'
                                accessionStatuses[acc].append(statuses_string)
                    cell_info = ''
                    for acc in accessionStatuses:
                        if len(accessionStatuses[acc]) < 1:

                            cell_info += acc + ' ' + histone_experiments_dict[acc]['object']['status'] + \
                                               '\r' + str(aliases[acc])

                        else:
                            statuses_string = ''
                            for status in accessionStatuses[acc]:
                                    statuses_string += status
                            cell_info += acc + ' ' + histone_experiments_dict[acc]['object']['status'] + \
                                               '\r' + str(aliases[acc]) + '\r' + \
                                               statuses_string
                        cell_info += '\r\n'
                    row.update({mark: 'Experiments number : '+str(total)+'\r' +
                               cell_info})
                else:
                    row.update({mark: 'NONE'})
            else:
                if sample in control_matrix[mark]:
                    total = len(control_matrix[mark][sample])

                    accessionStatuses = {}
                    aliases = {}
                    for (acc, al) in control_matrix[mark][sample]:
                        aliases[acc] = al
                        accessionStatuses[acc] = []
                        statuses = histone_controls_dict[acc]['statuses']

                        for k in statuses:
                            if len(statuses[k]) > 0:
                                statuses_string = ''
                                for status in statuses[k]:
                                    statuses_string += '-' + status + '\r'
                                accessionStatuses[acc].append(statuses_string)
                    cell_info = ''
                    for acc in accessionStatuses:
                        if len(accessionStatuses[acc]) < 1:
                            cell_info += acc + ' ' + histone_controls_dict[acc]['object']['status'] + \
                                               '\r' + str(aliases[acc])
                        else:
                            statuses_string = ''
                            for status in accessionStatuses[acc]:
                                    statuses_string += status
                            cell_info += acc + ' ' + histone_controls_dict[acc]['object']['status'] + \
                                               '\r' + str(aliases[acc]) + '\r' + \
                                               statuses_string
                        cell_info += '\r\n'
                    row.update({mark: 'Experiments number : '+str(total)+'\r' +
                                      cell_info})
                else:
                    row.update({mark: 'NONE'})

        writer.writerow(row)


with open(path_to_output_2, 'wb') as output:
    fields = ['sample'] + marks_to_print
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for sample in sample_types:
        row = {'sample': sample}


        for mark in marks_to_print:
            if mark != 'control':
                if sample in matrix[mark]:
                    total = len(matrix[mark][sample])

                    accessionStatuses = {}
                    aliases = {}
                    for (acc, al) in matrix[mark][sample]:
                        aliases[acc] = al
                        accessionStatuses[acc] = []
                        statuses = histone_experiments_dict[acc]['statuses']

                        for k in statuses:
                            if len(statuses[k]) > 0:
                                statuses_string = ''
                                for status in statuses[k]:
                                    statuses_string += '-' + status + '\r'
                                accessionStatuses[acc].append(statuses_string)
                    cell_info = ''
                    for acc in accessionStatuses:
                        cell_info += acc + ' ' + \
                                           histone_experiments_dict[acc]['object']['status'] + \
                                           '\r' + str(aliases[acc]) + \
                                           '\r' + \
                                           histone_experiments_dict[acc]['seq_info']
                       
                        cell_info += '\r\n'
                    row.update({mark: 'Experiments number : '+str(total)+'\r' +
                               cell_info})
                else:
                    row.update({mark: 'NONE'})
            else:
                if sample in control_matrix[mark]:
                    total = len(control_matrix[mark][sample])

                    accessionStatuses = {}
                    aliases = {}
                    for (acc, al) in control_matrix[mark][sample]:
                        aliases[acc] = al
                        accessionStatuses[acc] = []
                        statuses = histone_controls_dict[acc]['statuses']

                        for k in statuses:
                            if len(statuses[k]) > 0:
                                statuses_string = ''
                                for status in statuses[k]:
                                    statuses_string += '-' + status + '\r'
                                accessionStatuses[acc].append(statuses_string)
                    cell_info = ''
                    for acc in accessionStatuses:

                        cell_info += acc + ' ' + histone_controls_dict[acc]['object']['status'] + \
                                           '\r' + str(aliases[acc]) + '\r' + \
                                           histone_controls_dict[acc]['seq_info']
                       
                        cell_info += '\r\n'
                    row.update({mark: 'Experiments number : '+str(total)+'\r' +
                                      cell_info})
                else:
                    row.update({mark: 'NONE'})

        writer.writerow(row)
