import gdata
import gdata.spreadsheet.service

email = "yourname@gmail.com" # Stanford accounts won't work!
password = "abcxyz"

spreadname = 'Import Test Sheet'
workname = 'antitestset'

updates = {'B4':'42','B6':'21'}


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

# insert a new row (does not check for duplicate)
# (column names must be lowercase, spaces removed)
# if column doesn't match existing column, no patch is done for that value
dicti = {}
dicti['bizarroname'] = 'AAA'
dicti['bizzarodepleted'] = '42' 
dicti['broken'] = 'no'
entry = sheetclient.InsertRow(dicti, spreadid, workid)

# retrieve data as cells
query = gdata.spreadsheet.service.CellQuery()
query.return_empty = "true" 
cells = sheetclient.GetCellsFeed(spreadid,workid,query=query)

# update cell.  based on coordinate system on spreadsheet (column letter, row number)
# could also use col/row numbers by looking in entry.cell.row and entry.cell.col
# normal query doesn't work for GetCellsFeed (even though similar class structure)
#query = gdata.spreadsheet.service.DocumentQuery()
#query.title = cellname
#query.title_exact = "true"
query = gdata.spreadsheet.service.CellQuery()
query.return_empty = "true" 
cells = sheetclient.GetCellsFeed(spreadid,workid,query=query)
action = gdata.spreadsheet.SpreadsheetsCellsFeed()
for entry in cells.entry:
    for cellname in updates.keys():
        if entry.title.text == cellname:
            entry.cell.inputValue = updates[cellname]
            action.AddUpdate(entry)
updated = sheetclient.ExecuteBatch(action, cells.GetBatchLink().href)
