from ENCODETools import ElasticSearchJSON
from ENCODETools import FlatJSON
from ENCODETools import WriteJSON
from ENCODETools import FindSets

from identity import keys

if __name__ == "__main__":
    '''
    This script will find a set of JSON objects based on specified criteria and save them to find.json.
    Specifically, it will retrieve all of the specified object types from the database, then search that list with the set of criteria.
    '''
    # FUTURE CHANGES: Nikhil may implement updates to the elasticsearch query which should allow more accurate return results.
    # At that point, this script may not be needed, as the main function may be able to handle it all in the query.

    # elasticsearch settings
    server = 'http://submit.encodedcc.org:9200'
    query = {'query': {'match_all': {}}}
    hitnum = 10000
    
    # the particular object types you want to return
    object_type = 'antibody_approval'

    # search criteria
    searchquery1 = {'accession':'ENCAB000AJM'}
    searchquery2 = {'name':'human'}

    # file name for saved objects
    find_file = 'find.json'

    
    # retrieve the relevant objects
    master_objects = ElasticSearchJSON(server,query,object_type,hitnum)

    # find the relevant objects based on search criteria
    [object_list1,other_list] = FindSets(master_objects,searchquery1,'original')
    [object_list,other_list] = FindSets(object_list1,searchquery2,'all')

    print(str(len(object_list)) + ' of ' + str(len(master_objects)) + ' Objects Found.')

    print('Flattening...')
    #print(object_list)
    for item in object_list:
        #print item
        item = FlatJSON(item,keys)

    # write object to file
    WriteJSON(object_list,find_file)
    print('Saved to ' + find_file + '.')
