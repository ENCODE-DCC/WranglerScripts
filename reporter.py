#!/usr/bin/env python
# -*- coding: latin-1 -*-
''' BASIC REPORTER SCRIPT
'''
import requests
import json
import sys
import os.path
import argparse

HEADERS = {'content-type': 'application/json'}
global DEBUG_ON
DEBUG_ON = False
EPILOG = '''Examples:

To use a different key from the default keypair file:

        %(prog)s --key submit
'''


def get_ENCODE(obj_id):
        '''GET an ENCODE object as JSON and return as dict
        '''
        # url = SERVER+obj_id+'?limit=all'
        url = SERVER+obj_id
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


def patch_ENCODE(obj_id, patch_input):
        '''PATCH an existing ENCODE object and return the response JSON
        '''
        if isinstance(patch_input, dict):
            json_payload = json.dumps(patch_input)
        elif isinstance(patch_input, basestring):
                json_payload = patch_input
        else:
                print >> sys.stderr, 'Datatype to patch is not string or dict.'
        url = SERVER+obj_id
        if DEBUG_ON:
                print "DEBUG: PATCH URL : %s" % (url)
                print "DEBUG: PATCH data: %s" % (json_payload)
        response = requests.patch(url, auth=(AUTHID, AUTHPW), data=json_payload, headers=HEADERS)
        if DEBUG_ON:
                print "DEBUG: PATCH RESPONSE"
                print json.dumps(response.json(), indent=4, separators=(',', ': '))
        if not response.status_code == 200:
            print >> sys.stderr, response.text
        return response.json()


def post_ENCODE(collection_id, post_input):
        '''POST an ENCODE object as JSON and return the response JSON
        '''
        if isinstance(post_input, dict):
            json_payload = json.dumps(post_input)
        elif isinstance(post_input, basestring):
                json_payload = post_input
        else:
                print >> sys.stderr, 'Datatype to post is not string or dict.'
        url = SERVER+collection_id
        if DEBUG_ON:
                print "DEBUG: POST URL : %s" % (url)
                print "DEBUG: POST data:"
                print json.dumps(post_input, sort_keys=True, indent=4, separators=(',', ': '))
        response = requests.post(url, auth=(AUTHID, AUTHPW), headers=HEADERS, data=json_payload)
        if DEBUG_ON:
                print "DEBUG: POST RESPONSE"
                print json.dumps(response.json(), indent=4, separators=(',', ': '))
        if not response.status_code == 201:
                print >> sys.stderr, response.text
        print "Return object:"
        print json.dumps(response.json(), sort_keys=True, indent=4, separators=(',', ': '))
        return response.json()


def set_ENCODE_keys(keyfile, key):
        '''
          Set the global authentication keyds
        '''
        keysf = open(keyfile, 'r')
        keys_json_string = keysf.read()
        keysf.close()

        keys = json.loads(keys_json_string)
        key_dict = keys[key]

        global AUTHID
        global AUTHPW
        global SERVER

        AUTHID = key_dict['key']
        AUTHPW = key_dict['secret']
        SERVER = key_dict['server']
        if not SERVER.endswith("/"):
                SERVER += "/"
        return


def get_experiment_list(file, search):

        objList = []
        if search == "NULL":
            f = open(file)
            objList = f.readlines()
            for i in range(0, len(objList)):
                objList[i] = objList[i].strip()
        else:
            set = get_ENCODE(search + '&limit=all')
            for i in range(0, len(set['@graph'])):
                objList.append(set['@graph'][i]['accession'])

        return objList


def get_antibody_approval(antibody, target):

        search = get_ENCODE('search/?searchTerm='+antibody+'&type=antibody_approval')
        for approval in search['@graph']:
            if approval['target']['name'] == target:
                return approval['status']
        return "UNKNOWN"


def get_doc_list(documents):
   
    list = []
    for i in range(0, len(documents)):
        if 'attachment' in documents[i]:
            list.append(documents[i]['attachment']['download'])
        else:
            list.append(documents[i]['uuid'])
    return ' '.join(list)

# # I need my attachment thing here


checkedItems = ['project',
                'dbxrefs',
                'accession',
                'aliases',
                'status',
                'lab_name',
                'submitter',
                'grant',
                'assay_term_name',
                'assay_term_id',
                'species',
                'biosample_term_name',
                'biosample_term_id',
                'biosample_type',
                'description',
                # 'document_count',
                'experiment_documents',
                'control_exps',
                'theTarget',
                'file_count'
                ]

repCheckedItems = [
                   'rep_file_count',
                   'antibody',
                   'antibody_source',
                   'antibody_product',
                   'antibody_lot',
                   'antibody_status',
                   'replicate_uuid',
                   'replicate_aliases',
                   'rep_status',
                   'biological_replicate_number',
                   'technical_replicate_number',
                   'read_length',
                   'paired_ended',
                   'platform',
                   'files'
                   ]

fileCheckedItems = ['accession',
                    'submitted_file_name',
                    'file_format',
                    'dataset',
                    'experiment',
                    'alias',
                    'replicate_alias',
                    'biological_replicate',
                    'technical_replicate',
                    'status',
                    'paired_end',
                    ]

libraryCheckedItems = [
                       'accession',
                       'aliases',
                       'library_status',
                       'nucleic_acid_term_name',
                       'nucleic_acid_term_id',
                       'depleted_in_term_name',
                       'size_range',
                       'lysis_method',
                       'fragmentation_method',
                       'extraction_method',
                       'library_size_selection_method',
                       'library_treatments',
                       'protocols',
                       'biosample_accession',
                       'biosample_status',
                       'biosample_biosample_term',
                       'biosample_biosample_id',
                       'biosample_biosample_type',
                       'subcellular_fraction',
                       'phase',
                       #'biological_treatment',
                       'donor',
                       'donor_status',
                       'strain',
                       'age',
                       'age_units',
                       'life_stage',
                       'library_paired_ended',
                       'strand_specificity',
                       ]


def main():

        parser = argparse.ArgumentParser(
            description=__doc__, epilog=EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument('--infile', '-i',
                            default='objList',
                            help="File containing a list of ENCSRs.")
        parser.add_argument('--search',
                            default='NULL',
                            help="The search parameters.")
        parser.add_argument('--datatype',
                            default='OTHER',
                            help="The datatype format to print your report. (CHIP,RNA,REPLI,OTHER)")
        parser.add_argument('--key',
                            default='default',
                            help="The keypair identifier from the keyfile.  Default is --key=default")
        parser.add_argument('--keyfile',
                            default=os.path.expanduser("~/keypairs.json"),
                            help="The keypair file.  Default is --keyfile=%s" % (os.path.expanduser("~/keypairs.json")))
        parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            help="Print debug messages.  Default is False.")
        parser.add_argument('--details',
                            default=False,
                            action='store_true',
                            help="Print detailed report.  Default off")
        parser.add_argument('--status',
                            default=False,
                            action='store_true',
                            help="Print statuses of each object.  Default off")
        parser.add_argument('--mouse',
                            default=False,
                            action='store_true',
                            help="Print mouse specific details.  Default off")
        parser.add_argument('--simple',
                            default=False,
                            action='store_true',
                            help="Very simple output.  Default off")
        parser.add_argument('--library',
                            default=False,
                            action='store_true',
                            help="Print library details.  Default off")
        parser.add_argument('--files',
                            default=False,
                            action='store_true',
                            help="Print a file based report versus a replicate based one.  Default off")
        parser.add_argument('--encode2',
                            default=False,
                            action='store_true',
                            help="Print dbxrefs for ENCODE2.  Default off")
        args = parser.parse_args()

        DEBUG_ON = args.debug

        set_ENCODE_keys(args.keyfile, args.key)

        '''Adjust the checked list by the datatype'''
        if args.datatype != 'CHIP':
            checkedItems.remove('theTarget')
            checkedItems.remove('control_exps')
            repCheckedItems.remove('antibody')
            repCheckedItems.remove('antibody_status')
            repCheckedItems.remove('antibody_source')
            repCheckedItems.remove('antibody_product')
            repCheckedItems.remove('antibody_lot')
        
        if args.datatype != 'REPLI':
            libraryCheckedItems.remove('phase')

        if args.datatype != 'RNA':
            libraryCheckedItems.remove('subcellular_fraction')
            libraryCheckedItems.remove('library_treatments')
            libraryCheckedItems.remove('depleted_in_term_name')
         
        if args.simple:
            if args.datatype == 'CHIP': 
                repCheckedItems.remove('antibody_status')
                repCheckedItems.remove('antibody_source')
                repCheckedItems.remove('antibody_product')
                repCheckedItems.remove('antibody_lot')

        if not args.details:
            checkedItems.remove('project')
            checkedItems.remove('submitter')
            checkedItems.remove('grant')
            checkedItems.remove('assay_term_id')
            checkedItems.remove('biosample_term_id')
            libraryCheckedItems.remove('nucleic_acid_term_id')
            libraryCheckedItems.remove('biosample_biosample_term')
            libraryCheckedItems.remove('biosample_biosample_id')
            libraryCheckedItems.remove('biosample_biosample_type')

        if not args.library:
            libraryCheckedItems.remove('lysis_method')
            libraryCheckedItems.remove('fragmentation_method')
            libraryCheckedItems.remove('extraction_method')
            libraryCheckedItems.remove('library_size_selection_method')
            libraryCheckedItems.remove('size_range')
            libraryCheckedItems.remove('library_paired_ended')
        
        if not args.status:
            libraryCheckedItems.remove('library_status')
            libraryCheckedItems.remove('biosample_status')
            libraryCheckedItems.remove('donor_status')
            repCheckedItems.remove('rep_status')
            checkedItems.remove('status')

        if not args.encode2:
            checkedItems.remove('dbxrefs')

        if not args.mouse:
            libraryCheckedItems.remove('strain')

        if args.files:
            print '\t'.join(fileCheckedItems)
        else:
            print '\t'.join(checkedItems+repCheckedItems+libraryCheckedItems)



        # Get list of objects we are interested in
        search = args.search
        objList = get_experiment_list(args.infile, search)


        if args.files:
            for i in range(0, len(objList)):
                exp = get_ENCODE(objList[i])
                for i in range(0, len(exp['files'])):
                    fileob = {}
                    file = exp['files'][i]
                    for field in fileCheckedItems:
                        fileob[field] = file.get(field)
                    fileob['experiment'] = exp['accession']
                    fileob['alias'] = exp['aliases'][0]    
                    fileob['biological_replicate'] = file['replicate']['biological_replicate_number']
                    fileob['technical_replicate'] = file['replicate']['technical_replicate_number']
                    fileob['replicate_alias'] = file['replicate'].get('aliases')
                    row = []
                    for j in fileCheckedItems:
                        row.append(str(fileob[j]))
                    print '\t'.join(row)
            return

        for i in range(0, len(objList)):

            exp = get_ENCODE(objList[i])
            ob = {}

            for i in checkedItems:
                if i in exp:
                    ob[i] = exp[i]
                else:
                    ob[i] = ''

            '''Get the counts'''
            ob['replicate_count'] = len(exp['replicates'])
            ob['document_count'] = len(exp['documents'])
            ob['file_count'] = len(exp['files'])

            '''Get the experiment level ownership'''
            ob['lab_name'] = exp['lab']['name']
            ob['project'] = exp['award']['rfa']
            ob['grant'] = exp['award']['name']
            ob['submitter'] = exp['submitted_by']['title']
            ob['experiment_documents'] = get_doc_list(exp['documents'])


            temp = ''
            for i in range(0, len(exp['dbxrefs'])):
                temp = temp + ' ; ' + exp['dbxrefs'][i]
            ob['dbxrefs'] = temp

            ob['control_exps'] = ''
            for q in exp['possible_controls']:
                ob['control_exps'] = ob['control_exps']+' '+q['accession']

            if 'target' in exp:
                ob['theTarget'] = exp['target']['label']

            files_count = {}
            files_list = {}
            for i in range(0, len(exp['files'])):
                item = exp['files'][i]
                if 'replicate' in item:
                    repId = item['replicate']['uuid']
                else:
                    repId = 'no rep'

                if repId in files_list:
                   files_list[repId].append(item['accession'])
                elif repId != 'no rep':
                   files_list[repId] = [item['accession']]

                if repId in files_count:
                    files_count[repId] = files_count[repId] + 1
                else:
                    files_count[repId] = 1

            libs = []

            for q in range(0, ob['replicate_count']):
                rep = exp['replicates'][q]

                '''Inititalize rep object'''
                repOb = {}
                for field in libraryCheckedItems:
                    repOb[field] = ''
                for field in repCheckedItems:
                    if field in rep:
                        repOb[field] = rep[field]
                    else:
                        repOb[field] = ''
                if rep['uuid'] in files_count:
                    repOb['files'] = files_list[rep['uuid']]
                    repOb['rep_file_count'] = files_count[rep['uuid']]
                else:
                    repOb['rep_file_count'] = 0
                    repOb['files'] =[]
                repOb['replicate_aliases'] = rep['aliases']
                repOb['replicate_uuid'] = rep['uuid']
                repOb['rep_status'] = rep['status']
                if 'platform' in rep:
                    repOb['platform'] = rep['platform']['term_name']
                if 'antibody' in rep:
                        repOb['antibody'] = rep['antibody']['accession']
                        #repOb['antibody_status'] = rep['antibody']['approvals'][0]['status']
                        repOb['antibody_source'] = rep['antibody']['source']
                        repOb['antibody_product'] = rep['antibody']['product_id']
                        repOb['antibody_lot'] = rep['antibody']['lot_id']
                lib = []

                # inititalize the lib with repItems
                for i in repCheckedItems:
                    if i in repOb:
                        lib.append(str(repOb[i]))

                if 'library' in rep:

                    for field in libraryCheckedItems:
                        if field in rep['library']:
                            repOb[field] = rep['library'][field]
                    repOb['protocols'] = get_doc_list (rep['library']['documents'])
                    repOb['library_status'] = rep['library']['status']
                    repOb['library_paired_ended'] = rep['library']['paired_ended']
                    if 'biosample' in rep['library']:
                        bs = rep['library']['biosample']
                        repOb['biosample_accession'] = bs['accession']
                        repOb['biosample_status'] = bs['status']
                        repOb['biosample_biosample_term'] = bs['biosample_term_name']
                        repOb['biosample_biosample_id'] = bs['biosample_term_id']
                        repOb['biosample_biosample_type'] = bs['biosample_type']
                        ob['species'] = bs['organism']['name']
                        if 'subcellular_fraction' in bs:
                            repOb['subcellular_fraction'] = bs['subcellular_fraction']
                        else:
                            repOb['subcellular_fraction'] = 'unfractionated'

                        if bs['treatments'] != []:
                            repOb['biological_treatment'] = bs['treatments'][0]
                            # Note, we would have to pull the treatments individually
                            # rep['library']['biological_treatment'] = bs['treatments'][0]['dbxrefs'] 
                        if 'donor' in bs:
                            repOb['donor'] = bs['donor']['accession']
                            repOb['donor_status'] = bs['donor']['status']
                            if 'strain_background' in bs['donor']:
                                repOb['strain'] = bs['donor']['strain_background']
                        for term in ('phase', 'age', 'age_units', 'life_stage'):
                            if term in bs:
                                repOb[term] = bs[term]

                    temp = ' '.join(rep['library']['aliases'])
                    repOb['aliases'] = temp
                    ob['list_libraries'] = ''
                    ob['list_libraries'] = ob['list_libraries']+' '+rep['library']['accession']

                    for i in libraryCheckedItems:
                        if i in repOb:
                            lib.append(str(repOb[i]))
                        else:
                            lib.append( '')
                libs.append(lib)

            row = []
            for j in checkedItems:
                row.append(str(ob[j]))
            if len(libs) == 0:
                print '\t'.join(row)
            for k in range(0, len(libs)):
                print '\t'.join(row+libs[k])


if __name__ == '__main__':
    main()
