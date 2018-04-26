import copy
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


def get_template(template):
    return copy.deepcopy(template)


def set_sheet_id(form, wks):
    form['repeatCell']['range']['sheetId'] = wks.id
    return form


def set_column_for_formatting(df, col_name, form):
    num = df.columns.get_loc(col_name)
    form['repeatCell']['range']['startColumnIndex'] = num
    form['repeatCell']['range']['endColumnIndex'] = num + 1
    return form


def set_column_for_conditional_formatting(df, col_name, form, wks):
    num = df.columns.get_loc(col_name)
    form['addConditionalFormatRule']['rule']['ranges'][0]['startColumnIndex'] = num
    form['addConditionalFormatRule']['rule']['ranges'][0]['endColumnIndex'] = num + 1
    form['addConditionalFormatRule']['rule']['ranges'][0]['sheetId'] = wks.id
    return form


def header_formatter(formatter_value, df, wks):
    form = get_template(formatter_value['template'])
    form = set_sheet_id(form, wks)
    return form


def freeze_header_formatter(formatter_value, df, wks):
    form = get_template(formatter_value['template'])
    form['updateSheetProperties']['properties']['sheetId'] = wks.id
    return form


def note_formatter():
    pass


def font_formatter(formatter_value, df, wks):
    form = get_template(formatter_value['template'])
    form = set_sheet_id(form, wks)
    return form


def number_formatter(formatter_value, df, wks):
    updates = []
    for col_pattern in formatter_value['numeric_cols_pattern']:
        form = get_template(formatter_value['template'])
        form = set_sheet_id(form, wks)
        form = set_column_for_formatting(df, col_pattern[0], form)
        form['repeatCell']['cell']['userEnteredFormat']['numberFormat']['pattern'] = col_pattern[1]
        updates.append(form)
    return updates


def conditonal_formatter(formatter_value, df, wks):
    updates = []
    for col_name, conditions in formatter_value['conditions'].items():
        for condition in conditions:
            form = get_template(formatter_value['template'])
            condition_type = condition[0]
            condition_values = condition[1]
            condition_color = condition[2]
            # Must loop through because NUMBER_BETWEEN condition requires two objects.
            if condition_values:
                for value in condition_values:
                        form['addConditionalFormatRule']['rule']['booleanRule']['condition']['values'].append(
                            {"userEnteredValue": value}
                        )
            form['addConditionalFormatRule']['rule']['booleanRule']['condition']['type'] = condition_type
            form['addConditionalFormatRule']['rule']['booleanRule']['format']['backgroundColor']['red'] = condition_color[0]
            form['addConditionalFormatRule']['rule']['booleanRule']['format']['backgroundColor']['green'] = condition_color[1]
            form['addConditionalFormatRule']['rule']['booleanRule']['format']['backgroundColor']['blue'] = condition_color[2]
            form = set_column_for_conditional_formatting(df, col_name, form, wks)
            updates.append(form)
    return updates


def additional_formatter():
    pass


formatter_mapping = {
    'header': header_formatter,
    'freeze_header': freeze_header_formatter,
    'note': note_formatter,
    'font': font_formatter,
    'number': number_formatter,
    'conditional': conditonal_formatter,
    'additional': additional_formatter
}


def get_formatter(formatter_name):
    formatter = formatter_mapping.get(formatter_name)
    if not formatter:
        raise KeyError('Formatter not found %s' % formatter_name)
    return formatter


def apply_formatting_to_dataframe(df, wks, report_type):
    formatting = REPORT_TYPE_DETAILS[report_type]['formatting']
    updates = []
    for formatter_name, formatter_value in formatting.items():
        if not formatter_value:
            continue
        # build the formatting
        formatter = get_formatter(formatter_name)
        update = formatter(formatter_value, df, wks)
        updates.extend(update) if isinstance(update, list) else updates.append(update)
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
