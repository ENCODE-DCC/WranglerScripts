import pandas as pd
import pygsheets
from googleapiclient.errors import HttpError


# To authorize access to Google Drive/Sheets for particular account: Find
# client_secret file from Google and run
# gc = pygsheets.authorize(outh_file='client_secret_xxxx.json')
# This creates sheets.googleapis.com-python.json.


def google_connection(api_key):
    return pygsheets.authorize(api_key)


def open_and_clear_sheet(gc, sheet_title, page_title):
    # Open/create Google Sheet.
    try:
        sh = gc.open(sheet_title)
    except pygsheets.exceptions.SpreadsheetNotFound:
        sh = gc.create(sheet_title)
    try:
        wks = sh.add_worksheet(page_title)
    except HttpError:
        wks = sh.worksheet_by_title(page_title)
    wks.clear()
    return wks


def send_dataframe_to_google_sheet(df, wks):
    wks.set_dataframe(df, copy_head=True, fit=True, start='A1')


def output_to_google_sheets():
    pass


def output_to_tsv():
    pass

