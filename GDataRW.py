import gdata
import gdata.spreadsheet.service

email = "yourname@gmail.com" # Stanford accounts won't work!
password = "abcxyz"

spreadname = 'Import Test Sheet'
workname = 'antitestset'


# start a connection
sheetclient = gdata.spreadsheet.service.SpreadsheetsService()
sheetclient.email = email
sheetclient.password = password
sheetclient.ProgrammaticLogin()


# find a specific spreadsheet and get the id
query = gdata.spreadsheet.service.DocumentQuery()
query.title = spreadname
query.title_exact = 'true'
spreadfeed = sheetclient.GetSpreadsheetsFeed(query=query)
spreadid = spreadfeed.entry[0].id.text.rsplit('/',1)[1]

# find a specific worksheet and get the id
query = gdata.spreadsheet.service.DocumentQuery()
query.title = workname
query.title_exact = 'true'
workfeed = sheetclient.GetWorksheetsFeed(spreadid,query=query)
workid = workfeed.entry[0].id.text.rsplit('/',1)[1]

# retrieve data as rows in a sheet
rows = sheetclient.GetListFeed(spreadid, workid).entry
for row in rows:
    for key in row.custom:
        print " %s: %s" % (key, row.custom[key].text)
    print

# retrieve data as cells
query = gdata.spreadsheet.service.CellQuery()
query.return_empty = "true" 
cells = sheetclient.GetCellsFeed(spreadid,workid,query=query)


# insert a new row (does not check for duplicate)
dicti = {}
dicti['bizarroname'] = 'AAA'
dicti['bizzarodepleted'] = '42' 
dicti['broken'] = 'no'
entry = sheetclient.InsertRow(dicti, spreadid, workid)


