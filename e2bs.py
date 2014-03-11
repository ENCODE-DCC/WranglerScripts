#!/usr/bin/env python
# -*- coding: latin-1 -*-
''' Update ENCODE2 biosamples
'''
import xlrd, xlwt
import requests
import json
import sys
from base64 import b64encode

WORKBOOKPATH = 'biosample.xlsx'
OVERWRITE_ARRAYS = True
FORCE_PUT = False
'''force return from the server in JSON format'''
HEADERS = {'content-type': 'application/json'}

#SERVER = 'http://test.encodedcc.org'
#AUTHID = 'user'
#AUTHPW = 'user-secret'

def get_ENCODE(obj_id):
    '''GET an ENCODE object as JSON and return as dict'''
    url = SERVER+obj_id+'?limit=all'
    response = requests.get(url, auth=(AUTHID, AUTHPW), headers=HEADERS)
    if not response.status_code == requests.codes.ok:
        #print >> sys.stderr, response.text
        response.raise_for_status()
    return response.json()

def patch_ENCODE(obj_id, patch_input):
    '''PATCH an existing ENCODE object and return the response JSON'''
    '''
    if isinstance(patch_input, dict):
	    json_payload = json.dumps(patch_input)
    elif isinstance(patch_input, basestring):
	json_payload = 
    '''
    #json_payload = json.dumps(patch_input)
    json_payload = patch_input
    url = SERVER+obj_id
    #print json_payload
    response = requests.patch(url, auth=(AUTHID, AUTHPW), data=json_payload)
    if not response.status_code == 200:
        print >> sys.stderr, response.text
    return response.json()

def replace_ENCODE(obj_id, put_input):
	json_payload = put_input
	url = SERVER+obj_id
	response = requests.put(url, auth=(AUTHID, AUTHPW), data=json_payload)
	if not response.status_code == 200:
		print >> sys.stderr, response.text
	return response.json()

def new_ENCODE(collection_id, post_input):
    '''POST an ENCODE object as JSON and return the resppnse JSON'''
    url = SERVER+collection_id
    #json_payload = json.dumps(object_json)
    json_payload = post_input
    response = requests.post(url, auth=(AUTHID, AUTHPW), headers=HEADERS, data=json_payload)
    if not response.status_code == 201:
        print >> sys.stderr, response.text
    return response.json()

def headers(sheet):
	header_dict = {}
	cell_values = sheet.row_values(0)
	i = 0
	for cell_value in cell_values:
		headersplit = cell_value.split(':')
		headerstring = headersplit[0]
		try:
			datatype = headersplit[1]
		except IndexError:
			datatype = 'string'
		header_dict[headerstring] = {'index':i, 'datatype':datatype}
		i += 1
	return header_dict

def process_sheet(sheet,objname):
	header = headers(sheet)
	obj_schema = get_ENCODE('/profiles/' + objname + '.json')
	obj_properties = obj_schema['properties'].keys()
	collection_name = '/' + objname.replace('_','-') + 's/'

	first_rowi = 1
	last_rowi = sheet.nrows
	for i in range(first_rowi, last_rowi):
		cells = sheet.row_values(i)
		quuid = cells[header['uuid']['index']]
		try:
			existing_object = get_ENCODE(collection_name + quuid)
		except:
			existing_object = {}
		if existing_object:
			if FORCE_PUT:
				method = 'PUT'
			else:
				method = 'PATCH'
			print "Introspecting %s%s" %(collection_name, quuid)
		else:
			if FORCE_PUT:
				method = 'PUT'
			else:
				method = 'POST'
			print "Building new %s%s" %(collection_name, quuid)
		new_object = {}
		for header_name in header.keys():
			try:
				oldvalue = existing_object[header_name]
			except:
				oldvalue = ""
			newvalue = cells[header[header_name]['index']]
			#print newvalue
			datatype = header[header_name]['datatype']
			#print datatype
			if datatype != 'ignore':
				if datatype in ['string', 'integer', 'number']:
					if oldvalue != "":
						if header_name in ['lab', 'award']:
							if objname in ['human_donor', 'treatment']:
								oldobj = get_ENCODE(oldvalue)
								oldvalue = oldobj['name']
							else:
								oldvalue = oldvalue['name']
						if header_name in ['organism']:
							if objname in ['human_donor', 'target']:
								oldvalue = oldvalue['name']
							else:
								oldobj = get_ENCODE(oldvalue)
								oldvalue = oldobj['name']
						elif header_name == 'donor':
							oldvalue = oldvalue['accession']
							#print "Old donor %s" %(oldvalue)
							#print "New donor %s" %(newvalue)
						elif header_name in ['source']:
							oldvalue = oldvalue['name']
						elif header_name == 'submitted_by':
							if objname == 'treatment':
								oldobj = get_ENCODE(oldvalue)
								oldvalue = oldobj['email']
							else:
								oldvalue = oldvalue['email']
					if oldvalue != newvalue or FORCE_PUT:
						if newvalue == "":
							pass
						else:
							print "Changing value for %s from %s to %s." %(header_name, oldvalue, newvalue)
							new_object.update({header_name:newvalue})
				elif datatype == 'array':
					if newvalue != "":
						newvalue_list = str(newvalue).split(';')
						newvalue_list = [unicode(x.strip()) for x in newvalue_list]
						newvalue_list.sort()
					else:
						newvalue_list = []
					if oldvalue != "":
						if header_name in ['treatments','constructs','rnais']:
							oldvalue = [x['uuid'] for x in oldvalue]
						elif header_name in ['protocol_documents', 'characterizations']:
							temp = []
							#print oldvalue
							try:
								for document in oldvalue:
									for alias in document['aliases']:
										temp.append(alias)
							except:
								pass
							oldvalue = temp
						elif header_name in ['protocols']:
							temp = []
							try:
								for document in [get_ENCODE(x) for x in oldvalue]:
									for alias in document['aliases']:
										temp.append(alias)
							except:
								pass
							oldvalue = temp
						elif header_name in ['derived_from']:
							oldvalue = [x['accession'] for x in oldvalue]
						elif header_name in ['pooled_from']:
							oldvalue = [x.split('/')[2] for x in oldvalue]
					if sorted(oldvalue) != newvalue_list or FORCE_PUT:
						print "%s different" %(header_name)
						print sorted(oldvalue)
						if oldvalue != "":
							unique_elements = oldvalue
						else:
							unique_elements = []
						unique_elements += [x for x in newvalue_list if x not in oldvalue]
						if OVERWRITE_ARRAYS or FORCE_PUT:
							pass
						else:
							newvalue_list = unique_elements
						if FORCE_PUT and newvalue_list == []:
							pass
						else:
							print "Adding", newvalue_list
							new_object.update({header_name:newvalue_list})
				elif datatype == 'object':
					print "Object datatype not implemented"					
				else:
					print "Unknown type %s" %(datatype)
		if new_object != {}:
			resource_name = collection_name + quuid
			new_object_JSON = json.dumps(new_object)
			new_object_show = new_object
			new_object_JSON_show = json.dumps(new_object_show)
			while True:
				print "New JSON to %s to %s:" %(method, resource_name)
				print new_object_JSON_show
				resp = raw_input("Do it? (y,N,h)")
				if resp == 'y':
					if method == 'POST':
						response = new_ENCODE(collection_name,new_object_JSON)
						print response
					elif method == 'PATCH':
						response = patch_ENCODE(resource_name,new_object_JSON)
						print response
					elif method == 'PUT':
						response = replace_ENCODE(resource_name,new_object_JSON)
						print response
					else:
						print 'Error: Invalid method. Skipping.'
					break
				elif resp == 'n' or resp == '':
					print "Skipping"
					break
				elif resp == 'h':
					new_object_JSON = raw_input("Your JSON:")
					new_object_JSON_show = new_object_JSON
					pass
				else:
					print "%s is not an option" %(resp)
					pass


if __name__ == '__main__':

	workbook = xlrd.open_workbook(WORKBOOKPATH)

	for sheet in [x for x in workbook.sheets() if x.name in ['target', 'source', 'document', 'treatment', 'construct', 'biosample', 'human_donor', 'mouse_donor']]:
		print sheet.name
		process_sheet(sheet,sheet.name)
