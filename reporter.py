#!/usr/bin/env python
# -*- coding: latin-1 -*-
''' BASIC REPORTER SCRIPT
'''
import requests
import json
import sys
import os.path
import argparse
from base64 import b64encode
from copy import deepcopy

HEADERS = {'content-type': 'application/json'}
DEBUG_ON = False
EPILOG = '''Examples:

To use a different key from the default keypair file:

        %(prog)s --key submit
'''




def get_ENCODE(obj_id):
        '''GET an ENCODE object as JSON and return as dict
        '''
        #url = SERVER+obj_id+'?limit=all'
        url = SERVER+obj_id
        if DEBUG_ON:
                print "DEBUG: GET %s" %(url)
        response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
        if DEBUG_ON:
                print "DEBUG: GET RESPONSE code %s" %(response.status_code)
                try:
                        if response.json():
                                print "DEBUG: GET RESPONSE JSON"
                                print json.dumps(response.json(), indent=4, separators=(',', ': '))
                except:
                        print "DEBUG: GET RESPONSE text %s" %(response.text)
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
                print "DEBUG: PATCH URL : %s" %(url)
                print "DEBUG: PATCH data: %s" %(json_payload)
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
                print "DEBUG: POST URL : %s" %(url)
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


def set_ENCODE_keys(keyfile,key):
        '''
          Set the global authentication keyds
        '''

        keysf = open(keyfile,'r')
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


def get_experiment_list(file,search):


        objList = []
        if search == "NULL":
            f = open(file)
            objList = f.readlines()
            for i in range(0, len(objList)):
               objList[i] = objList[i].strip()
        else:
            
            set = get_ENCODE(search +'&limit=all')
            for i in range(0, len(set['@graph'])):
                objList.append(set['@graph'][i]['accession'] )

        return objList 


def get_antibody_approval (antibody, target):

        search = get_ENCODE('search/?searchTerm='+antibody+'&type=antibody_approval')
        for approval in search['@graph']:
            if approval['target']['name'] == target:
                return approval['status']
        return "UNKNOWN"  



## I need my attachment thing here




checkedItems = ['project',
                'encode2_dbxrefs',
                'geo_dbxrefs',
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
                'description',
                #'document_count',
                #'documents',
                'control_exps',
                'theTarget',
                'file_count' #possibly this should go in replicate as well
                ]

libraryCheckedItems = [
                       'antibody',
                       'antibody_source',
                       'antibody_product',
                       'antibody_lot',
                       'antibody_status',
                       'accession',
                       'aliases',
                       #'replicate_aliases',
                       'nucleic_acid_term_name',
                       'nucleic_acid_term_id',
                       'depleted_in_term_name',
                       'size_range',
                       'library_treatments',
                       'protocols',
                       'biological_replicate_number',
                       'technical_replicate_number',
                       'biosample_accession',
                       'subcellular_fraction',
                       'phase',
                       'biological_treatment',
                       'donor',
                       'strain',
                       'age',
                       'age_units',
                       'life_stage',
                       'read_length',
                       'paired_ended',
                       'strand_specificity',
                       'platform',
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
                help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
        parser.add_argument('--debug',
                default=False,
                action='store_true',
                help="Print debug messages.  Default is False.")
        parser.add_argument('--details',
                default=False,
                action='store_true',
                help="Print detailed report.  Default is False.")
        parser.add_argument('--mouse',
                default=False,
                action='store_true',
                help="Print mouse specific information.  Default is False.")
        parser.add_argument('--no-otherIds',
                default=False,
                action='store_true',
                help="Surpress the printing of other IDs like ENCODE2 or GEO.  Default is False.")
        args = parser.parse_args()

        DEBUG_ON =args.debug
   
        set_ENCODE_keys(args.keyfile,args.key)



        '''Adjust the checked list by the datatype'''
        if args.datatype != 'CHIP':
           checkedItems.remove('theTarget')
           checkedItems.remove('control_exps')
           libraryCheckedItems.remove('antibody')
           libraryCheckedItems.remove('antibody_status')
           libraryCheckedItems.remove('antibody_source')
           libraryCheckedItems.remove('antibody_product')
           libraryCheckedItems.remove('antibody_lot')
       
        if args.datatype != 'REPLI':
           libraryCheckedItems.remove('phase')

        if args.datatype != 'RNA':
           libraryCheckedItems.remove('subcellular_fraction')
           libraryCheckedItems.remove('library_treatments')
           libraryCheckedItems.remove('depleted_in_term_name')

        if not args.details:
           checkedItems.remove('project')
           checkedItems.remove('submitter')
           checkedItems.remove('grant')
           checkedItems.remove('assay_term_id')
           checkedItems.remove('biosample_term_id')
           libraryCheckedItems.remove('nucleic_acid_term_id')
           libraryCheckedItems.remove('size_range')

        if not args.mouse:
           libraryCheckedItems.remove('strain')

        print '\t'.join(checkedItems+libraryCheckedItems)
        




        #Get list of objects we are interested in

        #search_results = get_ENCODE("search/?type=experiment&lab.title=Bing%20Ren,%20UCSD&assay_term_name=ChIP-seq&target.label=H3K4me2")
        #search = "search/?type=experiment&assay_term_name=Repli-seq" 
        #search = "search/?type=experiment&assay_term_name=DNase-seq&lab.title=John%20Stamatoyannopoulos,%20UW&award.rfa=ENCODE2"
        #search = "search/?type=experiment&assay_term_name=RNA%20Array&lab.title=John%20Stamatoyannopoulos,%20UW"
        #search = "search/?type=experiment&assay_term_name=DNase-seq&lab.title=John%20Stamatoyannopoulos,%20UW&award.rfa=ENCODE2-Mouse"
        #search = "search/?type=experiment&assay_term_name=RNA-seq&lab.title=John%20Stamatoyannopoulos,%20UW&award.rfa=ENCODE2-Mouse"
        ##search = "search/?type=experiment&assay_term_name=ChIP-seq&lab.title=John%20Stamatoyannopoulos,%20UW&award.rfa=ENCODE2"
        #search = "search/?type=experiment&lab.title=Bing+Ren%2C+UCSD&award.rfa=ENCODE2-Mouse&assay_term_name=ChIP-seq"
        #search = "search/?type=experiment&lab.title=Bing%20Ren,%20UCSD&assay_term_name=RNA-seq&award.rfa=ENCODE2-Mouse


        search = args.search

        objList = get_experiment_list ( args.infile, search )
        for i in range (0, len(objList)):

           ob = get_ENCODE(objList[i])
        
           '''Get the counts'''
           ob['replicate_count'] = len(ob['replicates'])
           ob['document_count'] = len(ob['documents'])
           ob['file_count'] = len(ob['files'])
       
           '''Get the experiment level ownership''' 
           ob['lab_name']= ob['lab']['name']
           ob ['project'] = ob['award']['rfa']
           ob ['grant'] = ob['award']['name']
           ob ['submitter'] = ob['submitted_by']['title']
        

           if len(ob['geo_dbxrefs']) >0:
              ob['geo_series']= ob['geo_dbxrefs'][0]
        
           ob['control_exps'] = ''
           for q in ob['possible_controls']:
               ob['control_exps'] = ob['control_exps']+' '+q['accession']
        
           ob['theTarget'] = ''
           if 'target' in ob:
              ob['theTarget'] = ob['target']['label']
        
        
           ob['list_libraries'] = ''
           ob['list_biosamples'] = ''
           ob['species'] = ''
           libs = []
           for q in range(0, ob['replicate_count']):
               rep = ob['replicates'][q]
               if  'library' in rep:


                  '''Inititalize'''
                  rep['library']['replicate_aliases'] = rep['aliases']
                  rep['library']['antibody'] = ''
                  rep['library']['antibody_status'] = ''
                  rep['library']['platform'] = ''
                  rep['library']['read_length'] = ''

                  if 'antibody' in rep:
                      rep['library']['antibody'] = rep['antibody']['accession']
                      rep['library']['antibody_status'] = rep['antibody']['status']
                      rep['library']['antibody_source'] = rep['antibody']['source']
                      rep['library']['antibody_product'] = rep['antibody']['product_id']
                      rep['library']['antibody_lot'] = rep['antibody']['lot_id']

                  if 'platform' in rep:
                      rep['library']['platform'] = rep['platform']['term_name']
        
                  rep['library']['biological_replicate_number'] = rep['biological_replicate_number']
                  rep['library']['technical_replicate_number'] = rep['technical_replicate_number']
                  if 'read_length' in rep:
                      rep['library']['read_length'] = rep['read_length']
        
                  rep['library']['protocols'] = []
                  for i in range (0, len(rep['library']['documents'])):
                      rep['library']['protocols'].append (rep['library']['documents'][i]['attachment']['download'])
                  temp = ' '.join(rep['library']['protocols'])
                  rep['library']['protocols'] = temp
        
        
                  if 'biosample' in rep['library']:
                      bs = rep['library']['biosample']
                      rep['library']['biosample_accession'] = rep['library']['biosample']['accession']

                      if 'subcellular_fraction' in rep['library']['biosample']:
                          rep['library']['subcellular_fraction'] = rep['library']['biosample']['subcellular_fraction']
                      else:
                          rep['library']['subcellular_fraction'] = 'unfractionated'

                      if bs['treatments'] != []:
                          rep['library']['biological_treatment'] = bs['treatments'][0]
                          #Note, we would have to pull the treatments individually
                          #rep['library']['biological_treatment'] = bs['treatments'][0]['encode2_dbxrefs'] 
                      if 'donor' in bs:
                          rep['library']['donor'] = bs['donor']['accession']
                          if 'strain_background' in bs['donor']:
                              rep['library']['strain'] = bs ['donor']['strain_background']
                      for term in ('phase','age', 'age_units', 'life_stage'):
                          if term in rep['library']['biosample']:
                             rep['library'][term] = rep['library']['biosample'][term]
        
        
        
        
                  temp = ' '.join(rep['library']['aliases'])
                  rep['library']['aliases'] = temp
        
        
        
                  lib = []
                  for i in libraryCheckedItems:
                      if i in rep['library']:
                          lib.append(str(rep['library'][i]))
                      else:
                          lib.append( '')
                  libs.append(lib)
                  ob['list_libraries'] = ob['list_libraries']+' '+rep['library']['accession']
        
        
                  ''' Does every library have a valid biosample?  Does it match each other?  Does it match experiment?'''
                  if 'biosample' in rep['library']:
                     ob['list_biosamples'] = ob['list_biosamples']+' '+rep['library']['biosample']['accession']
                     if ob['species'] == '':
                        ob['species'] = rep['library']['biosample']['organism']['name']
                     elif ob['species'] != rep['library']['biosample']['organism']['name']:
                        ob['species'] = 'ERROR'
                  else:
                     ob['list_biosamples'] = ob['list_biosamples']+' '+ 'ERROR'
           row =[]
           for j in checkedItems:
              row.append(str(ob[j]))
           if len(libs) ==0:
               print '\t'.join(row)
           for k in range(0,len(libs)):
               print '\t'.join(row+libs[k])
        
        
if __name__ == '__main__':
     main()
