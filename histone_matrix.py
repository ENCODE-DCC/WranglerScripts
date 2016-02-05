'''
For a given lab performing histone modifications ChIP-seq experiments we would
like to create a matrix that will include information about experiments
statuses, audit errors etc.

More specifically we are interested for every given experiment:

A. PRIOR ANALYSIS

1. If it has an antibody (Experiment level audit "missing antibody" reported for every replicate (ERROR))
2. If it has eligible antibody (Experiment level audit "not eligible antibody" reported for every replicate (NOT COMPLIANT))
3. Each experiment has to have 2 technical replicates (Experiment level audit: "unreplicated experiment" reported once for experiment (WARNING" or "NOT_COMPLIANT"))

4. File duplication/concatenation. For every fastq file - it's content md5sum is unique on the portal, and the sizes of paired end fastqs are comparable
5. Mixture of read lengths between and without biological replicates, same for paired/single ended sequencing.

6. controls? in general some kind of different treatment
	audit - miising controlled by, and for present controls pull the control from portal and iterragate the audits
	 - in controls, in audits I should look for:
	a) if processed - insufficient read depth, and library complexity
	b) if not inconsistent biosample rep number, mismatched replicate,  replicate with no library (not a problem for broad, but is for HAIB)

B. POST ANALYSIS

1. Read depth (File level audit "insufficient read depth")
2. Library complexity (File level audit "insufficient library complexity" / "low library complexity")


After having this information for all the histone modifications ChIP-seq experiments of a given lab
I have to create a dictionary (histome mark, cell type) andd each cell with have :

1. URL pointing to the group of these experiments on portal
2. Some kind of summary of the problems for this group

This dictionary can be displayed as excel matrix, may be google doc sheet - if I learn how to do these
'''
import sys
import requests
import urlparse
from time import sleep
import csv

GET_HEADERS = {'accept': 'application/json'}


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
            if file_object['status'] not in FILE_IGNORE_STATUS and file_object['file_format'] == 'fastq':
                content_md5_sum = file_object['content_md5sum']
                if encoded_get(server+'/search/?type=file&content_md5sum=%s' % (content_md5_sum), keypair)['total'] > 1:
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


CORE_MARKS = ['H3K27ac', 'H3K27me3', 'H3K36me3', 'H3K4me1', 'H3K4me3', 'H3K9me3']
EXPERIMENT_IGNORE_STATUS = ['deleted','revoked','replaced']
FILE_IGNORE_STATUS = ['deleted','revoked','replaced', 'upload failed', 'format check failed', 'uploading']

keypair = ('K72CG7FY', 'hwzqj7gf3q5x3exk')
server = 'https://www.encodeproject.org/'

lab = '&lab.title=Bing Ren, UCSD'
organism = '&replicates.library.biosample.donor.organism.scientific_name=Mus musculus'

#lab = '&lab.title=Bradley Bernstein, Broad'
#organism = '&replicates.library.biosample.donor.organism.scientific_name=Homo sapiens'


url = server +'search/?searchTerm=ctcf&type=Experiment&format=json&frame=object&limit=all'

histone_experiments_pages = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=histone' + lab +
                              '&format=json&frame=page&limit=all', keypair)['@graph']

histone_controls_pages = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=control' + lab +
                              '&format=json&frame=page&limit=all', keypair)['@graph']

histone_experiments_objects = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=histone' + lab +
                              '&format=json&frame=embedded&limit=all', keypair)['@graph']

histone_controls_objects = encoded_get(server + 'search/?type=Experiment'
                              '&assay_term_name=ChIP-seq'
                              '&award.rfa=ENCODE3' + organism +
                              '&target.investigated_as=control' + lab +
                              '&format=json&frame=embedded&limit=all', keypair)['@graph']

matrix = {}
control_matrix = {}
sample_types = set()
marks = set()

histone_experiments_dict = {}
for entry in histone_experiments_pages:
    histone_experiments_dict[entry['accession']] = {'page': entry}
for entry in histone_experiments_objects:
    #contains_duplicated_fastqs(entry, server)
    #break

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
            print 'processed '+str(mone) + ' out of ' + str(len(histone_experiments_dict.keys()))
        statuses = {'replication': [], 'antibody': [], 'control': [], 'files': [], 'qc': []}
        if is_replicated(obj) is False or is_replicated(page) is False:
            statuses['replication'].append('unreplicated')
        if is_antibody_eligible(page) is False:
            statuses['antibody'].append('not eligible antybody')
        if is_not_missing_antibody(page) is False:
            statuses['antibody'].append('missing antybody')
        if is_not_mismatched_controlled_by(page) is False:
            statuses['control'].append('mismatched controled_by')
        if is_not_missing_controls(page) is False:
            statuses['control'].append('missing control')
        if is_not_missing_paired_with(page) is False:
            statuses['files'].append('missing paired_with files')
        # checking for duplication is slow, so I gues sI should do it externally
        # and in general it was solved
        #if contains_duplicated_fastqs(obj, server) is True:
        #    statuses['files'].append('duplicated fastq files')
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


for ac in histone_controls_dict:
    page = histone_controls_dict[ac]['page']
    obj = histone_controls_dict[ac]['object']
    if is_interesting(obj):
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

# we have matrix dictionary for the matrix creation - each cell contains a lit of all the accessions
# we have the histone_experiments_dict that for each accession has a list of statuses ['replication', 'antibody', control']


marks_to_print = ['control']
marks_to_print.extend(CORE_MARKS)
for m in marks:
    if m not in CORE_MARKS and m != 'control':
        marks_to_print.append(m)

#output = open("/Users/idan/Desktop/mat.csv", "w")
with open("/Users/idan/Desktop/mat.csv", 'wb') as output:
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
                            cell_info += acc +'\r' + str(aliases[acc])
                        else:
                            statuses_string = ''
                            for status in accessionStatuses[acc]:
                                    statuses_string += status
                            cell_info += acc +'\r' + str(aliases[acc]) + '\r' + statuses_string
                        cell_info += '\r\n'
                    row.update({mark: 'Experiments number : '+str(total)+'\r'+ cell_info})
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
                            cell_info += acc +'\r' + str(aliases[acc])
                        else:
                            statuses_string = ''
                            for status in accessionStatuses[acc]:
                                    statuses_string += status
                            cell_info += acc +'\r' + str(aliases[acc]) + '\r' + statuses_string
                        cell_info += '\r\n'
                    row.update({mark: 'Experiments number : '+str(total)+'\r'+ cell_info})
                else:
                    row.update({mark: 'NONE'})

        writer.writerow(row)

# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!
# TODO ADD DUPLICATION AND CONCATENATION CHECKS!!!!!

# USE THE DEMO OF RELEASE TO GET LIB COMPLEXITY

# NOT SURE HOW TO MAKE LINKS IN EXCEL

'''


for sample in sample_types:
    sampleLine = sample

    for mark in CORE_MARKS:

        if sample in matrix[mark]:

            total = len(matrix[mark][sample])
            statuses_to_report = ''

            for acc in matrix[mark][sample]:
                statuses_to_report += ' '+acc
                statuses = histone_experiments_dict[acc]

                for k in statuses:
                    if len(statuses[k]) > 0:
                        statuses_to_report += ' ' + str(statuses[k])
                statuses_to_report += '<br/>'

            sampleLine += ', \" TOTAL : '+str(total)+'<br/>'+statuses_to_report + '\"'
        else:
            sampleLine += ', None'
    output.write(sampleLine+'\n')

output.close()
'''