#!/usr/bin/env python
# -*- coding: latin-1 -*-
'''Read in a file of object, correction fields and patch each object'''

import basicStart
import argparse
import requests
import json
import sys
import os.path
from base64 import b64encode
from copy import deepcopy



HEADERS = {'content-type': 'application/json'}
DEBUG_ON = False
EPILOG = '''Examples:

To get one ENCODE object from the server/keypair called "default" in the default keypair file and print the JSON:

        %(prog)s --id ENCBS000AAA

To use a different key from the default keypair file:

        %(prog)s --id ENCBS000AAA --key submit
'''






def get_ENCODE(obj_id):
        '''GET an ENCODE object as JSON and return as dict
        '''
        url = SERVER+obj_id+'?limit=all'
        #url = SERVER+obj_id
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


## I need my attachment thing here









def main():

        parser = argparse.ArgumentParser(
            description=__doc__, epilog=EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument('--infile', '-i',
                            help="File containing the JSON object as a JSON string.")
        parser.add_argument('--objDict',
                            help="The object-dictionary of things to update.")
        parser.add_argument('--field',
                            help="The field to patch.")
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
        parser.add_argument('--array',
                            default=False,
                            action='store_true',
                            help="Field is an array.  Default is False.")
        args = parser.parse_args()

        DEBUG_ON = args.debug

        set_ENCODE_keys(args.keyfile, args.key)

        FIELD = args.field

        objDict = {}
        with open("objDict") as fd:
            objDict = dict(line.strip().split(None, 1) for line in fd)

        for key in objDict:

            '''build a URL that points to an ENCODE object'''
            URL = SERVER+'/'+key

            '''GET the ENCODE object using it's resource name and store the Response'''
            response = requests.get(URL, auth=(AUTHID, AUTHPW), headers=HEADERS)

            '''act on the Response object return code'''
            #print response.status_code
            if not response.status_code == requests.codes.ok:
                print response.text
                response.raise_for_status()

            '''build a python dictionary from the JSON response content'''
            object = response.json()

            '''convert NULLS to empty string'''
            if objDict[key].strip() == 'NULL':
                objDict[key] = ''
            elif objDict[key].strip() == 'False':
                objDict[key] = False
            elif objDict[key].strip() == 'True':
                objDict[key] = True 
            elif objDict[key].isdigit():
                objDict[key] = int(objDict[key]) 

            old_thing = ''
            if FIELD in object:
                old_thing = object[FIELD]
            if args.array:
                patch_thing = old_thing
                if objDict[key] == '':
                   patch_thing = []
                else:
                   patch_thing.append(objDict[key])
                   temp = list(set(patch_thing))
                   patch_thing = temp
                   patch_thing = [objDict[key]]
            else:
                patch_thing = objDict[key]

            '''construct a dictionary with the key and value to be changed'''
            patchdict = {FIELD: patch_thing}
            if FIELD == 'read_length':
               patchdict.update({'read_length_units':'nt'}) 
            '''convert the dictionary to a JSON object'''
            json_payload = json.dumps(patchdict)
            '''PATCH the ENCODE object with the new value'''
            response = requests.patch(URL, auth=(AUTHID, AUTHPW), data=json_payload, headers=HEADERS)
            '''act on the Response object return code'''
            if not response.status_code == requests.codes.ok:
                print response.text
                response.raise_for_status()
        
            '''verify that the PATCH worked'''
            '''GET the ENCODE object using it's resource name and store the Response'''
            response = requests.get(URL, auth=(AUTHID, AUTHPW), headers=HEADERS)
        
            '''act on the Response object return code'''
            if not response.status_code == requests.codes.ok:
                print response.text
                response.raise_for_status()
        
            '''build a python dictionary from the JSON response content'''
            object = response.json()
        
            '''extract the description from the ENCODE object'''
            new_thing = object[FIELD]
        
            '''print what we did'''
            print "Original:  %s" %(old_thing)
            print "PATCH:     %s" %(patch_thing)
            print "New value: %s" %(new_thing)


if __name__ == '__main__':
        main()
