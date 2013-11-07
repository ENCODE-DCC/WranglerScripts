import os
import sys
import csv
import json
import jsonschema
import requests
from pyelasticsearch import ElasticSearch
import xlrd
import xlwt
from base64 import b64encode

# set headers.  UNCLEAR IF THIS IS USED PROPERLY
HEADERS = {'content-type': 'application/json'}

# get object from server
def get_ENCODE(obj_id,keys):
    '''GET an ENCODE object as JSON and return as dict'''
    url = keys['server']+obj_id+'?limit=all'
    response = requests.get(url, auth=(keys['authid'],keys['authpw']), headers=HEADERS)
    if not response.status_code == 200:
        print >> sys.stderr, response.text
    return response.json()

# get object from server
def GetENCODE(object_id,keys):
    '''GET an ENCODE object as JSON and return as dict'''
    if type(object_id) is str:
        url = keys['server']+object_id+'?limit=all'
        #print(url)
        try:
            response = requests.get(url,auth=(keys['authid'],keys['authpw']), headers=HEADERS)
            if not response.status_code == 200:
                print >> sys.stderr, response.text
        # no
        except Exception as e:
            print("Get request failed:")
            #print(e)
        # yes
        else:
            return response.json()


# patch object to server
def patch_ENCODE(obj_id,patch_json,keys):
    '''PATCH an existing ENCODE object and return the response JSON'''
    url = keys['server']+obj_id
    json_payload = json.dumps(patch_json)
    response = requests.patch(url, auth=(keys['authid'],keys['authpw']), data=json_payload)
    print "Patch:"
    print response.status_code
    if not response.status_code == 200:
        print >> sys.stderr, response.text
    return response.json()

# post object to server
def new_ENCODE(collection_id, object_json,keys):
    '''POST an ENCODE object as JSON and return the resppnse JSON'''
    url = keys['server'] +'/'+collection_id+'/'
    json_payload = json.dumps(object_json)
    response = requests.post(url, auth=(keys['authid'],keys['authpw']), headers=HEADERS, data=json_payload)
    print(response.status_code)
    if not response.status_code == 201:
        print >> sys.stderr, response.text
    return response.json()

# get keys from file
def KeyENCODE(key_file,user_name,server_name):
    key_open = open(key_file)
    keys = csv.DictReader(key_open,delimiter = '\t')
    for key in keys:
        if (key.get('Server') == server_name) & (key.get('User') == user_name):
            key_info = {}
            key_info['user'] = key.get('User')
            key_info['server'] = ('http://' + key.get('Server') + '.encodedcc.org')
            key_info['authid'] = key.get('ID')
            key_info['authpw'] = key.get('PW')
            print('Identity confirmed')
    key_open.close()
    return(key_info)

# read json objects from file
def ReadJSON(json_file):
    json_load = open(json_file)
    json_read = json.load(json_load)
    json_load.close()
    return json_read

# write new json obect.  SHOULD BE MODIFIED TO CUSTOM OUTPUT FORMAT (FOR HUMAN VIEWING)
def WriteJSON(new_object,object_file):
    with open(object_file, 'w') as outfile:
        json.dump(new_object, outfile)
        outfile.close()

# check json object for validity.  SHOULD ONLY NEED OBJECT.  NEED DEF TO EXTRACT VALUE (LIKE TYPE) FROM JSON OBJECT GRACEFULLY.
def ValidJSON(object_type,object_id,new_object,keys):
    #get the relevant schema
    object_schema = GetENCODE(('/profiles/' + object_type + '.json'),keys)

    # test the new object.  SHOULD HANDLE ERRORS GRACEFULLY        
    try:
        jsonschema.validate(new_object,object_schema)
    # did not validate
    except Exception as e:
        print('Validation of ' + object_id + ' failed.')
        print(e)
        return False

    # did validate
    else:
        # inform the user of the success
        print('Validation of ' + object_id + ' succeeded.')
        return True

# intended to fix invalid JSON.  removes unexpected or unpatchable properties.  DOES NOT REMOVE ITEMS THAT CAN ONLY BE POSTED
def CleanJSON(new_object,object_schema,action):
    for key in new_object.keys():
        if not object_schema[u'properties'].get(key):
            new_object.pop(key)
        elif object_schema[u'properties'][key].get(u'requestMethod'):
            if object_schema[u'properties'][key][u'requestMethod'] is []:
                new_object.pop(key)
            elif action not in object_schema[u'properties'][key][u'requestMethod']:
                new_object.pop(key)
    return new_object

# flatten embedded json objects to their ID
def FlatJSON(json_object,keys):
    json_object = EmbedJSON(json_object,keys)
    for key,value in json_object.items():
        if type(value) is dict:
            json_object[key] = json_object[key][u'@id']
        if type(value) is list:
            #print("Found List: " + key)
            value_new = []
            for value_check in value:
                #print("Checking...")
                if type(value_check) is dict:
                    #print("Found Object")
                    value_check = value_check[u'@id']
                    #print(value_check)
                value_new.append(value_check)
            json_object[key] = value_new
    return json_object

# expand json object
def EmbedJSON(json_object,keys):
    for key,value in json_object.items():
        if (type(value) is unicode):
            if (len(value) > 1):
                if str(value[0]) == '/':
                    json_sub_object = GetENCODE(str(value),keys)
                    if type(json_sub_object) is dict:
                        #json_sub_object = EmbedJSON(json_sub_object,keys)
                        json_object[key] = json_sub_object
        elif type(value) is list:
            values_embed = []
            for entry in value:
                if (type(entry) is unicode):
                    if (len(entry) > 1):
                        if str(entry[0]) == '/':
                            json_sub_object = GetENCODE(str(entry),keys)
                            if type(json_sub_object) is dict:
                                #json_sub_object = EmbedJSON(json_sub_object,keys)
                                values_embed.append(json_sub_object)
            if len(values_embed) is len(json_object[key]):
                json_object[key] = values_embed
    return json_object


# run an elasticsearch query.  SHOULD BE EXPANDED TO CONSTRUCT THE QUERY OBJECT.
def ElasticSearchJSON(server,query,object_type,hitnum):
    '''
    Run an elasticsearch query and return JSON objects
    server: should be currently set to 'http://submit.encodedcc.org:9200'
    query: a dict formatted as specified by elasticsearch.
        the default match_all query is {'query': {'match_all': {}}}
    object_type: the name of the object type.  for example 'biosample'
    hitnum: the maximum number of returned json objects
        set this as high as you can take it (10000 will do for now)
    '''
    #make instance of elastic search
    connection = ElasticSearch(server)
    # run query on server for index
    results = connection.search(query,index=object_type,size=hitnum)
    # result objects are embedded in a dict of search result metrics
    result_objects = results['hits']['hits']
    # extract the json objects from the results
    json_objects = []
    for result_object in result_objects:
        json_objects.append(result_object[u'_source'])
    return json_objects



