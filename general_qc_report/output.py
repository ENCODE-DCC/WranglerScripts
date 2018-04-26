import logging
import pandas as pd
import pygsheets
from datetime import datetime
from googleapiclient.errors import HttpError
from constants import REPORT_TYPE_DETAILS

# To authorize access to Google Drive/Sheets for particular account: Find
# client_secret file from Google and run
# gc = pygsheets.authorize(outh_file='client_secret_xxxx.json')
# This creates sheets.googleapis.com-python.json.


def get_outputter(output_type):
    if output_type == 'tsv':
        return output_to_tsv
    elif output_type == 'google_sheets':
        return output_to_google_sheets
    else:
        raise KeyError('Output function not found')


def make_page_title(report_type, assembly):
    date = datetime.now().strftime('%m_%d_%Y')
    return '%s_report_%s_%s' % (report_type, assembly, date)


def google_connection(api_key):
    logging.warn('Connecting to Google Sheets')
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
    wks.set_dataframe(df.fillna(''), copy_head=True, fit=True, start='A1')


def apply_formatting_to_dataframe(df, wks, report_type):
    formatting = REPORT_TYPE_DETAILS[report_type]['formatting']
    updates = []
    for f in formatting:
        # build the formatting
        update = {}
        updates.append(update)
    wks.client.sh_batch_update(wks.spreadsheet.id, updates)


def output_to_google_sheets(df, args):
    gc = google_connection(args.api_key)
    wks = open_and_clear_sheet(
        gc,
        args.sheet_title,
        make_page_title(args.report_type, args.assembly)
    )
    logging.warn('Sending dataframe to Google Sheets')
    send_dataframe_to_google_sheet(df, wks)
    logging.warn('Applying formatting')
    apply_formatting_to_dataframe(df, wks, args.report_type)


def output_to_tsv(df, args):
    logging.warn('Sending dataframe to TSV')
    df.to_csv(
        '%s.tsv' % make_page_title(args.report_type, args.assembly),
        sep='\t',
        index=False
    )
