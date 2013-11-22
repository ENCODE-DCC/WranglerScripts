from ENCODETools import ReadJSON
from ENCODETools import GetENCODE
from ENCODETools import FlatJSON
from ENCODETools import LoginGSheet
from ENCODETools import FindGSpreadSheet
from ENCODETools import FindGWorkSheet

from identity import keys


if __name__ == "__main__":
    '''
    This script will read in a set of json objects and add them to a spreadsheet
    '''

    data_file = 'update.json'

    email = "yourname@gmail.com" # Stanford accounts won't work!
    password = "abc123"

    spreadname = 'Import Test Sheet'

    rowsize = 2
    colsize = 52

    # load object  SHOULD HANDLE ERRORS GRACEFULLY
    print('Opening ' + data_file)
    object_list = ReadJSON(data_file)
    # find out what types of objects you have. use as worksheet names.
    # also, change all json object values to strings
    typelist = []
    for json_object in object_list:
        json_object = FlatJSON(json_object,keys)
        typetemp = str(json_object['@type'][0])
        typelist.append(typetemp)
        for name,value in json_object.items():
            if type(value) is list:
                if value is []:
                    json_object[name] = ''
                else:
                    json_object[name] = ', '.join(value)
            elif type(value) is int:
                json_object[name] = str(value)
    typelist = list(set(typelist))
    typelist.sort()

    # get column headers based on schema fields
    # get all relevant schema
    print('Getting Schema')
    object_schemas = {}
    for object_type in typelist:
        object_schemas.update({object_type:GetENCODE(('/profiles/' + object_type + '.json'),keys)})
    # get list of keys (column headers) for each schema
    print('Getting Columns')
    columnslist = {}
    for object_type,object_schema in object_schemas.items():
        columns = object_schema[u'properties'].keys()
        columns.sort()
        columnslist.update({object_type:columns})

    # start a spreadsheet login
    print('Open Login')
    sheetclient = LoginGSheet(email,password)

    # run for each worksheet type
    for workname,columns in columnslist.items():

        # find existing viewer spreadsheet.  if it exists, delete it and make a new one.
        print('Format Sheet')
        [spreadid,spreadsheet] = FindGSpreadSheet(sheetclient,spreadname)
        [workid,worksheet] = FindGWorkSheet(sheetclient,spreadid,workname)
            # CREATE NEW SPREADSHEET COMMAND HERE
        if workid == '':
            sheetclient.AddWorksheet(workname,rowsize,colsize,spreadid)
            [workid,worksheet] = FindGWorkSheet(sheetclient,spreadid,workname)
        else:
            response = sheetclient.DeleteWorksheet(worksheet)
            sheetclient.AddWorksheet(workname,rowsize,colsize,spreadid)
            [workid,worksheet] = FindGWorkSheet(sheetclient,spreadid,workname)

        # make first row the column headers
        print('Add Headers')
        for indexcol,column in enumerate(columns):
            #print(indexcol,column,spreadid,workid)
            response = sheetclient.UpdateCell(1,indexcol+1,column,spreadid,workid)

        # add rows for those objects that match the worksheet title
        print('Add Rows')
        for json_object in object_list:
            if json_object.has_key('@type'):
                if workname in json_object['@type']:
                    for name,value in json_object.items():
                        if name not in columns:
                            json_object.pop(name)
                    print(json_object)
                    response = sheetclient.InsertRow(json_object, spreadid, workid)

