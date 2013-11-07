from ENCODETools import ElasticSearchJSON
from ENCODETools import FlatJSON
from ENCODETools import WriteJSON

from identity import keys

if __name__ == "__main__":
    '''
    This script will find a set of JSON objects based on specified criteria and save them to find.json.
    Specifically, it will retrieve all of the specified object types from the database, then search that list with the set of criteria.
    '''
    # FUTURE CHANGES: Nikhil will soon implement the updates to the elasticsearch query which should allow more accurate return results.
    # At that point, this script may not be needed, as the main function may be able to handle it all in the query.

    # elasticsearch settings
    server = 'http://submit.encodedcc.org:9200'
    query = {'query': {'match_all': {}}}
    hitnum = 10000
    
    # the particular object types you want to return
    object_type = 'biosample'

    # search criteria
    search_value_string = 'GM12893'
    search_key_string = 'biosample_term_name'

    # file name for saved objects
    find_file = 'find.json'

    
    # retrieve the relevant objects
    master_objects = ElasticSearchJSON(server,query,object_type,hitnum)

    # flatten objects and select based on search criteria
    object_list = []
    for master_object in master_objects:
        master_object = FlatJSON(master_object,keys)
        for key,value in master_object.items():
            if search_key_string in str(key):
                #print(key)
                if type(value) is unicode:
                    if search_value_string in str(value):
                        print('Object ' + master_object[u'accession'] + ' Selected.  ' + str(key) + ' - ' + value)
                        object_list.append(master_object)
                        break
                if type(value) is list:
                    for entry in value:
                        if search_value_string in str(entry):
                            print('Object ' + master_object[u'accession'] + ' Selected.  ' + str(key) + ' - ' + entry)
                            object_list.append(master_object)
                            break

    print(str(len(object_list)) + ' of ' + str(len(master_objects)) + ' Objects Found.  Saved to ' + find_file + '.')

    # write object to file
    WriteJSON(object_list,find_file)
    
