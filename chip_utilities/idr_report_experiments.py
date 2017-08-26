#!/usr/bin/env python

import os
import sys
import logging
import csv
import common
import numpy as np
import pandas as pd
import pygsheets

from datetime import datetime
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

EPILOG = '''Notes:

Examples:

    %(prog)s
'''

# To authorize access to Google Drive/Sheets for particular account: Find
# client_secret file from Google and run
# gc = pygsheets.authorize(outh_file='client_secret_xxxx.json')
# This creates the sheets.googleapis.com-python.json that --apikey argument
# must point to.

# Conditional formatting rules for Google Sheet.

colors = np.array([[183, 225, 205],
                   [253, 231, 181],
                   [243, 200, 194]]) / 255.0

green = colors[0]
yellow = colors[1]
red = colors[2]

header = {
    "repeatCell": {
        "range": {
            "startRowIndex": 0,
            "endRowIndex": 1,
        },
        "cell": {
            "userEnteredFormat": {
                "textFormat": {
                    "fontSize": 10,
                    "bold": True
                }
            }
        },
        "fields": "userEnteredFormat(textFormat)"
    }
}

# Column names to apply number format.
number_format_columns = ['rescue_ratio',
                         'self_consistency_ratio',
                         'Ft',
                         'Fp',
                         'F1',
                         'F2']

number_format = {
    "repeatCell": {
        "range": {
            "startRowIndex": 1
        },
        "cell": {
            "userEnteredFormat": {
                "numberFormat": {
                    "type": "NUMBER",
                    "pattern": "0.00"
                }

            }
        },
        "fields": "userEnteredFormat.numberFormat"
    }
}

# Column names to apply font size.
font_size_columns = ['Nt',
                     'Np',
                     'N1',
                     'N2',
                     'rescue_ratio',
                     'self_consistency_ratio',
                     'Ft',
                     'Fp',
                     'F1',
                     'F2']

font_size_format = {
    "repeatCell": {
        "range": {
            "startRowIndex": 1
        },
        "cell": {
            "userEnteredFormat": {
                "textFormat": {
                    "fontSize": 9,
                }
            }
        },
        "fields": "userEnteredFormat(textFormat)"
    }
}

conditions = [
    {"addConditionalFormatRule": {
        "rule": {
            "ranges": [
                {
                    "startRowIndex": 1
                }
            ],
            "booleanRule": {
                "condition": {
                    "type": "TEXT_CONTAINS",
                    "values": [
                        {
                            "userEnteredValue": "pass"
                        }
                    ]
                },
                "format": {
                    "backgroundColor": {
                        "red": green[0],
                        "green": green[1],
                        "blue": green[2]
                    },
                }
            }
        }, "index": 0
    }
    },
    {"addConditionalFormatRule": {
        "rule": {
            "ranges": [
                {
                    "startRowIndex": 1,
                }
            ],
            "booleanRule": {
                "condition": {
                    "type": "TEXT_CONTAINS",
                    "values": [
                        {
                            "userEnteredValue": "borderline"
                        }
                    ]
                },
                "format": {
                    "backgroundColor": {
                        "red": yellow[0],
                        "green": yellow[1],
                        "blue": yellow[2]
                    },
                }
            }
        }, "index": 0
    }
    },
    {"addConditionalFormatRule": {
     "rule": {
         "ranges": [
             {
                 "startRowIndex": 1
             }
         ],
         "booleanRule": {
             "condition": {
                 "type": "TEXT_CONTAINS",
                 "values": [
                     {
                         "userEnteredValue": "fail"
                     }
                 ]
             },
             "format": {
                 "backgroundColor": {
                     "red": red[0],
                     "green": red[1],
                     "blue": red[2]
                 },
             }
         }
     }, "index": 0
     }
     }
]

notes_dict = {'Nt': 'Nt = number of peaks that pass IDR comparing peaks called on reads from each true (biological) replicate',
              'Np': 'Np = the number of peaks that pass IDR when comparing peaks called on psedoreplicates of the reads pooled from both true replicates',
              'N1': 'N1 = the number of peaks that pass IDR comparing pseudoreplicates of rep 1',
              'N2': 'N2 = the number of peaks that pass IDR comparing pseudoreplicates of rep 2',
              'rescue_ratio': 'rescue_ratio = (max(Np,Nt)) / (min(Np,Nt)) Estimates replicate similarity by comparing how similar the peak lists are from treating replicates separately vs. pooling them',
              'self_consistency_ratio': 'self_consistency_ratio = (max(N1,N2)) / (min(N1,N2)) Estimates replicate similarity by comparing how similar the peak lists are from pseudoreplication of each true replicate',
              'reproducibility_test': 'reproducibility_test Pass if both rescue and self_consistency ratios are < 2. Borderline if one is > 2. Fail if both are > 2.',
              'Ft': 'Ft = FRiP score based on peaks that pass IDR comparing peaks called on reads from each true (biological) replicate',
              'Fp': 'Fp = FRiP score based on peaks that pass IDR when comparing peaks called on psedoreplicates of the reads pooled from both true replicates',
              'F1': 'F1 = FRiP score based on peaks that pass IDR comparing pseudoreplicates of rep 1',
              'F2': 'F2 = FRiP score based on peaks that pass IDR comparing pseudoreplicates of rep 2'}

note = {
    "repeatCell": {
        "range": {
            "startRowIndex": 0,
            "endRowIndex": 1,
        },
        "cell": {
            "note": ""
        },
        "fields": "note"
    }
}


class InputError(Exception):
    pass


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('experiments',
                        help='List of experiment accessions to report on.',
                        nargs='*',
                        default=None)
    parser.add_argument('--infile',
                        help='File containing experiment accessions.',
                        type=argparse.FileType('r'),
                        default=None)
    parser.add_argument('--all',
                        help='Report on all possible IDR experiments.',
                        default=False,
                        action='store_true')
    parser.add_argument('--outfile',
                        help='CSV output.',
                        type=argparse.FileType('wb'),
                        default=sys.stdout)
    parser.add_argument('--debug',
                        help='Print debug messages.',
                        default=False,
                        action='store_true')
    parser.add_argument('--key',
                        help='The keypair identifier from the keyfile.',
                        default='www')
    parser.add_argument('--keyfile',
                        help='The keyfile.',
                        default=os.path.expanduser('~/keypairs.json'))
    parser.add_argument('--assembly',
                        help='Genome assembly to report on'
                        ' (e.g. hg19 or GRCh38).',
                        required=True)
    parser.add_argument('--create_google_sheet',
                        help='Create Google Sheet with conditional formatting.'
                        ' Default is False. Requires API key.',
                        default=False,
                        action='store_true')
    parser.add_argument('--sheet_title',
                        help='Name of Google Sheet.',
                        default='ENCODE3 ChIP QC')
    parser.add_argument('--apikey',
                        help='Path to secret credential for Google Sheets.',
                        default=os.path.expanduser(
                            '~/sheets.googleapis.com-python.json'))

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s',
                            level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        # Use the default logging level.
        logging.basicConfig(format='%(levelname)s:%(message)s')
        logger.setLevel(logging.INFO)
    authid, authpw, server = common.processkey(args.key, args.keyfile)
    keypair = (authid, authpw)
    if args.experiments:
        ids = args.experiments
    elif args.all:
        # Get metadata for all ChIP-seq Experiments.
        exp_query = '/search/?type=Experiment'\
            '&assay_title=ChIP-seq'\
            '&award.project=ENCODE'\
            '&status=released&status=submitted'\
            '&status=in+progress&status=started&status=release+ready'
        all_experiments = common.encoded_get(server + exp_query,
                                             keypair)['@graph']
        # Extract Experiment accessions.
        ids = [exp.get('accession') for exp in all_experiments]
    elif args.infile:
        ids = args.infile
    else:
        # Never reached because infile defaults to stdin.
        raise InputError('Must supply experiment ids'
                         ' in arguments or --infile.')
    # Define column names for TSV.
    fieldnames = ['date',
                  'analysis',
                  'uuid',
                  'experiment',
                  'target',
                  'biosample_term_name',
                  'biosample_type',
                  'replication',
                  'lab',
                  'rfa',
                  'assembly',
                  'Nt',
                  'Np',
                  'N1',
                  'N2',
                  'rescue_ratio',
                  'self_consistency_ratio',
                  'reproducibility_test',
                  'Ft',
                  'Fp',
                  'F1',
                  'F2',
                  'state',
                  'release',
                  'quality_metric_of']
    if args.create_google_sheet:
        # Force creation of temporary CSV that can be loaded into a DataFrame,
        # written to Google Sheets, then deleted.
        temp_file = 'temp_idr_%s.tsv' % (args.assembly)
        args.outfile = open(temp_file, 'w')
    writer = csv.DictWriter(args.outfile,
                            fieldnames=fieldnames,
                            delimiter='\t',
                            quotechar='"')
    writer.writeheader()
    # Get metadata for all IDR output Files.
    idr_query = '/search/?type=File'\
        '&assembly=%s'\
        '&file_format=bed'\
        '&output_type=optimal+idr+thresholded+peaks'\
        '&output_type=conservative+idr+thresholded+peaks'\
        '&output_type=pseudoreplicated+idr+thresholded+peaks'\
        '&lab.title=ENCODE+Processing+Pipeline'\
        '&lab.title=J.+Michael+Cherry,+Stanford'\
        '&status=in+progress&status=released'\
        '&status=uploading&status=uploaded' % (args.assembly)
    all_idr_files = common.encoded_get(server + idr_query, keypair)['@graph']
    na = 'not_available'
    for (i, experiment_id) in enumerate(ids):
        if experiment_id.startswith('#'):
            continue
        experiment_id = experiment_id.rstrip()
        experiment_uri = '/experiments/%s/' % (experiment_id)
        # Select only Files part of specified Experiment.
        idr_files = [
            f for f in all_idr_files if f['dataset'] == experiment_uri]
        if not idr_files:
            if not args.all:
                logger.warning(
                    '%s: Found %d IDR files. Skipping'
                    % (experiment_id, len(idr_files)))
            continue
        idr_qc_uris = []
        assemblies = []
        for f in idr_files:
            quality_metrics = f.get('quality_metrics')
            if not len(quality_metrics) == 1:
                logger.error('%s: Expected one IDR quality metric for file %s.'
                             ' Found %d.' % (experiment_id,
                                             f.get('accession'),
                                             len(quality_metrics)))
            idr_qc_uris.extend(quality_metrics)
            assembly = f.get('assembly')
            if not assembly:
                logger.error('%s: File %s has no assembly'
                             % (experiment_id, f.get('accession')))
            assemblies.append(assembly)
        idr_qc_uris = set(idr_qc_uris)
        if not len(idr_qc_uris) == 1:
            logger.error('%s: Expected one unique IDR metric,'
                         ' found %d. Skipping.' % (experiment_id,
                                                   len(idr_qc_uris)))
            continue
        assemblies = set(assemblies)
        if not len(assemblies) == 1:
            logger.error('%s: Expected one unique assembly, found %d.'
                         ' Skipping.' % (experiment_id, len(assemblies)))
            continue
        # Grab unique value from set.
        idr_qc_uri = next(iter(idr_qc_uris))
        assembly = next(iter(assemblies))
        # Get IDR object.
        idr = common.encoded_get(server + idr_qc_uri,
                                 keypair)
        # Pull metrics of interest.
        Np = idr.get('Np', na)
        N1 = idr.get('N1', na)
        N2 = idr.get('N2', na)
        Nt = idr.get('Nt', na)
        Fp = idr.get('Fp', na)
        F1 = idr.get('F1', na)
        F2 = idr.get('F2', na)
        Ft = idr.get('Ft', na)
        quality_metric_of = idr.get('quality_metric_of', na)
        date = idr.get('date_created', na)
        rescue_ratio = idr.get('rescue_ratio', na)
        self_consistency_ratio = idr.get('self_consistency_ratio', na)
        reproducibility_test = idr.get('reproducibility_test', na)
        # Get Experiment object.
        experiment = common.encoded_get(server + experiment_id,
                                        keypair)
        experiment_link = '%sexperiments/%s' % (server,
                                                experiment.get('accession'))
        analysis_link = '%s%s' % (server, idr.get('step_run')[1:])
        # Get Award object.
        award = common.encoded_get(server + experiment.get('award'), keypair)
        # Grab project phase, e.g. ENCODE4.
        rfa = award.get('rfa', na)
        row = {'date': date,
               'analysis': analysis_link,
               'uuid': idr.get('uuid'),
               'experiment': experiment_link,
               'target': experiment['target'].split('/')[2],
               'biosample_term_name': experiment.get('biosample_term_name'),
               'biosample_type': experiment.get('biosample_type'),
               'replication': experiment.get('replication_type'),
               'lab': experiment['lab'].split('/')[2],
               'rfa': rfa,
               'assembly': assembly,
               'Nt': Nt,
               'Np': Np,
               'N1': N1,
               'N2': N2,
               'rescue_ratio': rescue_ratio,
               'self_consistency_ratio': self_consistency_ratio,
               'reproducibility_test': reproducibility_test,
               'Ft': Ft,
               'Fp': Fp,
               'F1': F1,
               'F2': F2,
               'state': 'done',
               'release': experiment['status'],
               'quality_metric_of': quality_metric_of
               }
        writer.writerow(row)
    if args.create_google_sheet:
        args.outfile.close()
        # Load CSV data, sort.
        idr_data = pd.read_table(temp_file)
        idr_data = idr_data.replace('not_available', '')
        idr_data.date = idr_data.date.apply(lambda x: pd.to_datetime(x))
        idr_data = idr_data.sort_values(
          by=['lab', 'biosample_term_name', 'target', 'experiment'],
          ascending=[True, True, True, True])
        idr_data.date = idr_data.date.astype('str')
        idr_data = idr_data.reset_index(drop=True)
        # Read sheet title and create unique page title.
        date = datetime.now().strftime('%m_%d_%Y')
        sheet_title = args.sheet_title
        page_title = '%s_IDR_FRIP_%s' % (args.assembly, date)
        # Open/create Google Sheet.
        gc = pygsheets.authorize(args.apikey)
        try:
            sh = gc.open(sheet_title)
        except pygsheets.exceptions.SpreadsheetNotFound:
            sh = gc.create(sheet_title)
        try:
            wks = sh.add_worksheet(page_title)
        except HttpError:
            wks = sh.worksheet_by_title(page_title)
        # Clear worksheet.
        wks.clear()
        # Add data from DataFrame.
        wks.set_dataframe(idr_data, copy_head=True, start='A1')
        # Apply formatting and conditions.
        header['repeatCell']['range']['sheetId'] = wks.id
        wks.client.sh_batch_update(wks.spreadsheet.id, header)
        # Format numbers.
        for col in number_format_columns:
            num = idr_data.columns.get_loc(col)
            number_format['repeatCell']['range']['startColumnIndex'] = num
            number_format['repeatCell']['range']['endColumnIndex'] = num + 1
            number_format['repeatCell']['range']['sheetId'] = wks.id
            wks.client.sh_batch_update(wks.spreadsheet.id, number_format)
        # Font size.
        for col in font_size_columns:
            num = idr_data.columns.get_loc(col)
            font_size_format['repeatCell']['range']['startColumnIndex'] = num
            font_size_format['repeatCell']['range']['endColumnIndex'] = num + 1
            font_size_format['repeatCell']['range']['sheetId'] = wks.id
            wks.client.sh_batch_update(wks.spreadsheet.id, font_size_format)
        # Add conditional formatting.
        for conditional in conditions:
            num = idr_data.columns.get_loc("reproducibility_test")
            conditional['addConditionalFormatRule']['rule']['ranges'][0]['startColumnIndex'] = num
            conditional['addConditionalFormatRule']['rule']['ranges'][0]['endColumnIndex'] = num + 1
            conditional['addConditionalFormatRule']['rule']['ranges'][0]['sheetId'] = wks.id
            wks.client.sh_batch_update(wks.spreadsheet.id, conditional)
        for k, v in notes_dict.items():
            num = idr_data.columns.get_loc(k)
            note['repeatCell']['range']['startColumnIndex'] = num
            note['repeatCell']['range']['endColumnIndex'] = num + 1
            note['repeatCell']['cell']['note'] = v
            note['repeatCell']['range']['sheetId'] = wks.id
            wks.client.sh_batch_update(wks.spreadsheet.id, note)
        # Optional. Smaller column width to match original.
        for i in range(wks.cols):
            wks.adjust_column_width(i, pixel_size=55)
        # Remove temp file.
        os.remove(temp_file)


if __name__ == '__main__':
    main()
