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

HEADERS = {'content-type': 'application/json'}
DEBUG_ON = False
EPILOG = '''Examples:

To use a different key from the default keypair file:

        %(prog)s --key submit
'''


def get_ENCODE(obj_id):
        '''GET an ENCODE object as JSON and return as dict
        '''
        # url = SERVER+obj_id+'?limit=all&datastore=database'
        url = SERVER+obj_id+'?frame=object'
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
                return ''               
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
            set = get_ENCODE(search+'&limit=all&frame=embedded')
            for i in range(0, len(set['@graph'])):
                #print set['@graph'][i]['accession'] 
                #objList.append(set['@graph'][i]['accession'] )
                objList.append(set['@graph'][i]['uuid'] )

        return objList 


def get_antibody_approval (antibody, target):

        search = get_ENCODE('search/?searchTerm='+antibody+'&type=antibody_approval')
        for approval in search['@graph']:
            if approval['target']['name'] == target:
                return approval['status']
        return "UNKNOWN"  



## I need my attachment thing here




def main():

        parser = argparse.ArgumentParser(
            description=__doc__, epilog=EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument('--infile', '-i',
                default='obList',
                help="File containing a list of ENCSRs.")
        parser.add_argument('--search',
                default='NULL',
                help="The search parameters.")
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
        parser.add_argument('--field',
                default='accession',
                help="The field to report.  Default is accession.")
        args = parser.parse_args()

        DEBUG_ON =args.debug
   
        set_ENCODE_keys(args.keyfile,args.key)


        #Get list of objects we are interested in

        objList = get_experiment_list ( args.infile, args.search )
        for i in range (0, len(objList)):

           ob = get_ENCODE(objList[i])
           field = ''     
           if ob != '':
                id = ob['uuid']
                if args.field in ob:
                    field = str(ob[args.field])
           else:
              id = objList[i]
           print '\t'.join([id,field])

if __name__ == '__main__':
     main()
