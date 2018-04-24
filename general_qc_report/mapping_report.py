#!/usr/bin/env python2
# -*- coding: latin-1 -*-
'''Reports replicate mappings'''

import requests
import json
import csv
import copy
import logging
import sys
import numpy as np
import os.path
import pandas as pd
import pygsheets
import urlparse
import re
import time
from multiprocessing import Pool
from functools import partial
import dxpy

from datetime import datetime
from googleapiclient.errors import HttpError
from pygsheets.exceptions import RequestError

EPILOG = '''
'''

# To authorize access to Google Drive/Sheets for particular account: Find
# client_secret file from Google and run
# gc = pygsheets.authorize(outh_file='client_secret_xxxx.json')
# This creates the sheets.googleapis.com-python.json that --apikey argument
# must point to.

# Independent of keypairs file for --released flag. 
PUBLIC_SERVER = 'https://www.encodeproject.org/'

# Conditional formatting rules for Google Sheet.
colors = np.array([[252, 1, 1],
                   [253, 154, 0],
                   [246, 205, 206],
                   [220, 220, 220],
                   [205, 216, 244],
                   [253, 231, 181],
                   [255, 255, 255]]) / 255.0

red = colors[0]
orange = colors[1]
pink = colors[2]
gray = colors[3]
blue = colors[4]
yellow = colors[5]
white = colors[6]


header = {
    "repeatCell": {
        "range": {
            "startRowIndex": 0,
            "endRowIndex": 1,
        },
        "cell": {
            "userEnteredFormat": {
                "textFormat": {
                    "fontSize": 9,
                    "bold": True
                }
            }
        },
        "fields": "userEnteredFormat(textFormat)"
    }
}

freeze_header = {
    "updateSheetProperties": {
        "properties": {
            "gridProperties": {"frozenRowCount": 1}
        },
        "fields": "gridProperties(frozenRowCount)"
    }
}

number_cols = {
    'three_decimal_cols': {'pattern': '0.000', 'cols': ['fract_mappable',
                                                        'fract_usable']},
    'two_decimal_cols': {'pattern': '0.00', 'cols': ['NRF',
                                                     'PBC1',
                                                     'PBC2',
                                                     'NSC',
                                                     'RSC']},
    'million_cols': {'pattern': '0.0,,"M"', 'cols': ['hiq_reads',
                                                     'mappable',
                                                     'picard_read_pairs_examined',
                                                     'picard_unpaired_reads_examined',
                                                     'usable_frags']}
}

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


font_size_format = {
    "repeatCell": {
        "range": {
            "startRowIndex": 1,
            "startColumnIndex": 0
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

condition_dict = {
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [
                {
                    "startRowIndex": 1,
                }
            ],
            "booleanRule": {
                "condition": {
                    "type": "",
                    "values": []
                },
                "format": {
                    "backgroundColor": {
                        "red": "",
                        "green": "",
                        "blue": ""
                    },
                }
            }
        }, "index": 0
    }
}

# https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#ConditionType
condition_cols = {'target': {'conditions': [('CUSTOM_FORMULA', ['=if(OR((if(iferror(search("control",C2)),TRUE,FALSE)),(if(iferror(search("broad histone mark",C2)),TRUE,FALSE))),TRUE,FALSE)'], blue)]},
                  'r_lengths': {'conditions': [('NUMBER_LESS', ['30'], red),
                                               ('NUMBER_LESS',
                                                ['50'], orange),
                                               ('TEXT_CONTAINS', [','], yellow)]},
                  'map_length': {'conditions': [('NUMBER_LESS', ['30'], red),
                                                ('NUMBER_LESS', ['50'], orange)]},
                  'crop_length': {'conditions': [('NUMBER_LESS', ['30'], red),
                                                 ('NUMBER_LESS', ['50'], orange)]},
                  'usable_frags': {'conditions': [('CUSTOM_FORMULA', [
                                                   '=if(AND(OR((if(iferror(search("control",C2)),TRUE,FALSE)),(if(iferror(search("broad histone mark",C2)),TRUE,FALSE))),Y2<20000000),TRUE,FALSE)'], red),
                                                  ('CUSTOM_FORMULA', [
                                                   '=if(AND(OR((if(iferror(search("control",C2)),TRUE,FALSE)),(if(iferror(search("broad histone mark",C2)),TRUE,FALSE))),AND(20000000<=Y2,Y2<45000000)),TRUE,FALSE)'], orange),
                                                  ('CUSTOM_FORMULA', [
                                                   '=if(AND(AND(NOT(if(iferror(search("control",C2)),TRUE,FALSE)),NOT(if(iferror(search("broad histone mark",C2)),TRUE,FALSE))),Y2<10000000),TRUE,FALSE)'], red),
                                                  ('CUSTOM_FORMULA', [
                                                   '=if(AND(AND(NOT(if(iferror(search("control",C2)),TRUE,FALSE)),NOT(if(iferror(search("broad histone mark",C2)),TRUE,FALSE))),AND(10000000<=Y2,Y2<20000000)),TRUE,FALSE)'], orange),
                                                  ('BLANK', [], white)]},
                  'NRF': {'conditions': [('NUMBER_LESS', ['0.7'], red),
                                         ('NUMBER_BETWEEN', [
                                          '0.7', '0.8'], orange),
                                         ('NUMBER_BETWEEN', ['0.8', '0.9'], pink)]},
                  'PBC1': {'conditions': [('NUMBER_LESS', ['0.5'], red),
                                          ('NUMBER_BETWEEN', ['0.5', '0.8'], orange)]},
                  'PBC2': {'conditions': [('NUMBER_LESS', ['1'], red),
                                          ('NUMBER_BETWEEN', [
                                           '1', '3'], orange),
                                          ('NUMBER_BETWEEN', ['3', '10'], pink)]},
                  'NSC': {'conditions': [('NUMBER_LESS', ['1.02'], orange),
                                         ('NUMBER_BETWEEN', [
                                          '1.02', '1.05'], pink),
                                         ('NUMBER_BETWEEN', ['1.05', '1.1'], gray)]},
                  'RSC': {'conditions': [('NUMBER_LESS', ['0.8'], orange),
                                         ('NUMBER_LESS', ['1'], pink)]}
                  }

notes_dict = {'bam': 'Accession of the bam file after mapping. "no fastqs" -> no fastqs have been submitted. "pending" -> fastqs have been submitted but mapping has not been done pending metadata review.',
              'hiq_reads': 'Number of reads input to the mapping pipeline.',
              'mappable': 'Number of reads mapping to a unique genomic location.',
              'r_lengths': '<30 Red, <50 Orange (ENCODE3 standard), Mixed read lengths Yellow.',
              'map_length': '<30 Red, <50 Orange (ENCODE3 standard), Blank means bam has no mapped_read_length property, assumed to be native length of the fastqs.',
              'usable_frags': 'Number of non-duplicated reads surviving the filter. ENCODE2: >10M for narrow marks, >20M for broad. ENCODE3: should be >20M-25M for narrow marks, >45M-50M for broad marks.',
              'NRF': 'Non redundant fraction (indicates library complexity). 0.0-0.7 very poor, 0.7-0.8 poor, 0.8-0.9 moderate, >0.9 high. Number of distinct unique mapping reads (i.e. after removing duplicates) / Total number of reads.',
              'PBC1': 'PCR Bottlenecking coefficient 1 (indicates library complexity). 0 - 0.5 (red): severe, 0.5 - 0.8 (orange): moderate, 0.8 - 0.9 (pink): mild, > 0.9: no bottlenecking. = M1/M_DISTINCT, M1: number of genomic locations where exactly one read maps uniquely, M_DISTINCT: number of distinct genomic locations to which some read maps uniquely.',
              'PBC2': 'PCR Bottlenecking coefficient 2 (indicates library complexity). 0 - 1 (red): severe, 1 - 3 (orange): moderate, 3 -10 (pink): mild, > 10 : no bottlenecking. = M1/M2, M1: number of genomic locations where only one read maps uniquely, M2: number of genomic locations where 2 reads map uniquely.',
              'frag_len': 'Fragment length/strandshift. This is the estimated fragment length/strand shift for each dataset as estimated by strand cross-correlation analysis.',
              'NSC': 'Normalized strand cross-correlation (A data quality measure). FRAGLEN_CC / MIN_CC. Ratio of strand cross-correlation at estimated fragment length to the minimum cross-correlation over all shifts. Values are always >1. NSC < 1.05 is flagged as potential low signal-to-noise. Could be due to: low enrichment, few number of peaks due to biology of factor, broad chromatin mark. orange: < 1.02 (very low), pink: 1.02 < NSC < 1.05 (low), grey: 1.05 < NSC < 1.1 (moderate), >= 1.1 (high).',
              'RSC': 'Relative cross correlation coefficient. Ratio of strand cross-correlation at fragment length and at read length. Enriched datasets should have values > 1 or very close to 1 (> 0.8).'}

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

CACHED_PLATFORMS = []
STATUS_TO_IGNORE = ['deleted', 'revoked', 'replaced', 'archived']
LAB_NAMES = ['encode-processing-pipeline']


def get_ENCODE(url, authid, authpw):
    '''
    Force return from the server in JSON format,
    GET an ENCODE object as JSON and return as dict.
    '''
    # Assume that a search query is complete except for &limit=all.
    if 'search' in url:
        pass
    else:
        # Have to do this because it might be the first directive in the URL.
        if '?' in url:
            url += '&datastore=database'
        else:
            url += '?datastore=database'
    url += '&limit=all'
    logging.debug('GET %s' % (url))
    max_retries = 10
    retries = max_retries
    sleep_increment = 6
    while retries:
        try:
            response = requests.get(url,
                                    auth=(authid, authpw) if all([authid, authpw]) else None,
                                    headers={'accept': 'application/json'})
        except requests.HTTPError:
            logging.warning('GET %s failed with %s' % (url, response.text))
            logging.warning('Retry %d of %d' %
                            ((max_retries - retries) + 1, max_retries))
            retries -= 1
            time.sleep(sleep_increment * (max_retries - retries))
            continue
        except Exception as e:
            logging.warning('GET %s failed with %s' % (url, e))
            logging.warning('Retry %d of %d' %
                            ((max_retries - retries) + 1, max_retries))
            retries -= 1
            time.sleep(sleep_increment * (max_retries - retries))
            continue
        else:
            return response.json()
    try:
        raise
    except Exception as e:
        logging.error('Max retries, giving up.  GET %s failed: %s' % (url, e))
        return {}


def processkeys(args):

    keysf = open(args.keyfile, 'r')
    keys_json_string = keysf.read()
    keysf.close()
    keys = json.loads(keys_json_string)
    key_dict = keys[args.key]
    if not args.authid:
        authid = key_dict['key']
    else:
        authid = args.authid
    if not args.authpw:
        authpw = key_dict['secret']
    else:
        authpw = args.authpw
    if not args.server:
        server = key_dict['server']
    else:
        server = args.server
    if not server.endswith('/'):
        server += '/'
    return server, authid, authpw


def flat_one(JSON_obj):
    try:
        return [JSON_obj[identifier] for identifier in
                ['accession', 'name', 'email', 'title', 'uuid', 'href']
                if identifier in JSON_obj][0]
    except:
        return JSON_obj


def flat_ENCODE(JSON_obj):
    flat_obj = {}
    for key in JSON_obj:
        if isinstance(JSON_obj[key], dict):
            flat_obj.update({key: flat_one(JSON_obj[key])})
        elif (isinstance(JSON_obj[key], list)
              and JSON_obj[key] != []
              and isinstance(JSON_obj[key][0], dict)):
            newlist = []
            for obj in JSON_obj[key]:
                newlist.append(flat_one(obj))
            flat_obj.update({key: newlist})
        else:
            flat_obj.update({key: JSON_obj[key]})
    return flat_obj


def pprint_ENCODE(JSON_obj):
    if ('type' in JSON_obj) and (JSON_obj['type'] == 'object'):
        print json.dumps(JSON_obj['properties'],
                         sort_keys=True,
                         indent=4,
                         separators=(',', ': '))
    else:
        print json.dumps(flat_ENCODE(JSON_obj),
                         sort_keys=True,
                         indent=4,
                         separators=(',', ': '))


def get_platform_strings(fastqs, server, authid, authpw):
    platform_strings = []
    platform_uris = set([f.get('platform')['@id'] for f in fastqs])
    for uri in platform_uris:
        if not uri:
            platform_strings.append('Missing')
            continue
        if uri not in [p.get('@id') for p in CACHED_PLATFORMS]:
            CACHED_PLATFORMS.append(
                get_ENCODE(urlparse.urljoin(server, uri), authid, authpw))
        platform_strings.append(next(p.get('title')
                                     for p in CACHED_PLATFORMS
                                     if p.get('@id') == uri))
    return platform_strings


def get_mapping_analysis(bam):
    try:
        job_alias = next(detail['dx_job_id'] for detail
                         in bam['step_run']['dx_applet_details'])
    except:
        logging.error(
            'Failed to find step_run.dx_applet_details in bam %s'
            % (bam.get('accession')))
        raise
    job_id = re.findall('job-\w*', job_alias)[0]
    analysis_id = dxpy.describe(job_id)['parentAnalysis']
    return dxpy.describe(analysis_id)


def get_analysis_url(analysis):
    if not analysis:
        return None
    project_uuid = analysis['project'].split('-')[1]
    analysis_uuid = analysis['id'].split('-')[1]
    analysis_url = 'https://platform.dnanexus.com/projects/' + \
        project_uuid + '/monitor/analysis/' + analysis_uuid
    return analysis_url


def get_crop_length(analysis):
    if not analysis:
        return None
    crop_length = next(stage['execution']['originalInput'].get('crop_length')
                       for stage in analysis['stages'])
    return str(crop_length)


# def dup_parse(dxlink):
#     desc = dxpy.describe(dxlink)
#     with dxpy.DXFile(desc['id'], mode='r') as dup_file:
#         if not dup_file:
#             return None

#         lines = iter(dup_file.read().splitlines())

#         for line in lines:
#             if line.startswith('## METRICS CLASS'):
#                 headers = lines.next().rstrip('\n').lower()
#                 metrics = lines.next().rstrip('\n')
#                 break

#         headers = headers.split('\t')
#         metrics = metrics.split('\t')
#         headers.pop(0)
#         metrics.pop(0)

#         dup_qc = dict(zip(headers, metrics))
#     return dup_qc


# def get_picard_reads_examined(analysis):
#     if not analysis:
#         return None
#     dup_qc_file = next(stage['execution']['output'].get('dup_file_qc') for stage in analysis['stages'])
#     dup_qc = dup_parse(dup_qc_file)
#     if dup_qc:
#         return {
#             'unpaired_reads_examined': dup_qc.get('UNPAIRED_READS_EXAMINED')
#             'read_pairs_examined': dup_qc.get('READ_PAIRS_EXAMINED')
#         }
#     else:
#         return None
def get_rows(experiment, server, authid, authpw, args):
    rows = []
    row_template = {
        'experiment': experiment.get('accession'),
        'experiment link': urlparse.urljoin(server, '/experiments/%s' % (experiment.get('accession'))),
        'target_type': ','.join(experiment.get('target', {}).get('investigated_as') or []),
        'target': experiment.get('target', {}).get('name'),
        'biosample_name': experiment.get('biosample_term_name'),
        'biosample_type': experiment.get('biosample_type'),
        'lab': experiment.get('lab', {}).get('name'),
        'rfa': experiment.get('award', {}).get('rfa'),
        'internal status': experiment.get('internal_status')
    }
    original_files = get_ENCODE(
        urlparse.urljoin(server,
                         '/search/?type=file&dataset=/experiments/%s/&'
                         'file_format=fastq&file_format=bam&frame=embed'
                         'ded&format=json'
                         % (experiment.get('accession'))), authid, authpw)['@graph']
    fastqs = [f for f in original_files if f.get(
        'file_format') == 'fastq' and f.get('status') not in STATUS_TO_IGNORE]
    bams = [f for f in original_files
            if f.get('file_format') == 'bam'
            and (not args.assembly
                 or f.get('assembly') == args.assembly)
            and f.get('status') not in STATUS_TO_IGNORE
            and f['lab']['name'] in LAB_NAMES]
    filtered_bams = [f for f in bams if f.get('output_type') == 'alignments']
    unfiltered_bams = [f for f in bams
                       if f.get('output_type') == 'unfiltered alignments']
    if not bams:
        row = copy.deepcopy(row_template)
        if not fastqs:
            row.update({'bam': 'no fastqs'})
        else:
            row.update({'bam': 'pending'})
            read_lengths = set([str(f.get('read_length')) for f in fastqs])
            row.update({'r_lengths': ','.join(read_lengths)})
            paired_end_strs = []
            if any([f.get('run_type') == 'single-ended' for f in fastqs]):
                paired_end_strs.append('SE')
            if any([f.get('run_type') == 'paired-ended' for f in fastqs]):
                paired_end_strs.append('PE')
            if any([f.get('run_type') == 'unknown' for f in fastqs]):
                paired_end_strs.append('unknown')
            row.update({'end': ','.join(paired_end_strs)})
            row.update({'platform': ','.join(
                get_platform_strings(fastqs, server, authid, authpw))})
        rows.append(row)
    else:
        for bam in filtered_bams:
            row = copy.deepcopy(row_template)
            # derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in [obj.get('accession') for obj in bam.get('derived_from') or []]]
            derived_from_accessions = [os.path.basename(uri.rstrip('/')) for
                                       uri in bam.get('derived_from') or []]
            derived_from_fastqs = [f for f in fastqs
                                   if f.get('accession') in derived_from_accessions]
            derived_from_fastq_accessions = [f.get('accession') for f in fastqs
                                             if f.get('accession') in derived_from_accessions]
            unfiltered_bam_accession = None
            unfiltered_bam_link = None
            for unfiltered_bam in unfiltered_bams:
                # ub_derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in [obj.get('accession') for obj in unfiltered_bam.get('derived_from') or []]]
                ub_derived_from_accessions = [os.path.basename(uri.rstrip('/'))
                                              for uri in unfiltered_bam.get('derived_from')
                                              or []]
                if set(derived_from_accessions) == set(ub_derived_from_accessions):
                    unfiltered_bam_accession = unfiltered_bam.get('accession')
                    unfiltered_bam_link = urlparse.urljoin(server,
                                                           unfiltered_bam.get('href'))
                    break
            bioreps = set([str(f.get('replicate').get('biological_replicate_number'))
                           for f in derived_from_fastqs])
            library_uris = set([str(f.get('replicate').get('library').get('@id'))
                                for f in derived_from_fastqs])
            read_lengths = set([str(f.get('read_length'))
                                for f in derived_from_fastqs])
            aliases = []
            libraries = []
            for uri in library_uris:
                library = get_ENCODE(urlparse.urljoin(
                    server, '%s' % (uri)), authid, authpw)
                if library.get('accession'):
                    libraries.append(library.get('accession'))
                    aliases.extend(library.get('aliases'))
            platform_strs = get_platform_strings(derived_from_fastqs,
                                                 server,
                                                 authid,
                                                 authpw)
            try:
                xcor_plot_uri = next(qc['@id'] + qc['cross_correlation_plot'].get('href')
                                     for qc in bam.get('quality_metrics') if qc.get('cross_correlation_plot'))
            except StopIteration:
                xcor_plot_link = 'Missing'
            else:
                xcor_plot_link = urlparse.urljoin(server, xcor_plot_uri)
            # mapping_analysis = get_mapping_analysis(bam)
            try:
                mapping_analysis = None if args.released else get_mapping_analysis(bam)
            except:
                mapping_analysis = None
            row.update({
                'biorep_id': ','.join(bioreps),
                'assembly': bam.get('assembly'),
                'platform': ','.join(platform_strs),
                'bam': bam.get('accession'),
                'bam link': urlparse.urljoin(server, bam.get('href')),
                'unfiltered bam': unfiltered_bam_accession,
                'unfiltered bam link': unfiltered_bam_link,
                'xcor plot': xcor_plot_link,
                'library': ','.join(libraries),
                'library aliases': ','.join(aliases),
                'r_lengths': ','.join(read_lengths),
                'from fastqs': ','.join(derived_from_fastq_accessions),
                'date_created': bam.get('date_created'),
                'release status': bam.get('status'),
                'dx_analysis': get_analysis_url(mapping_analysis),
                'map_length': bam.get('mapped_read_length', ''),
                'crop_length': get_crop_length(mapping_analysis)
            })
            try:
                notes = json.loads(bam.get('notes'))
            except:
                notes = None
            quality_metrics = bam.get('quality_metrics')
            # if quality_metrics:
            #   filter_qc = next(m for m in quality_metrics if "ChipSeqFilterQualityMetric" in m['@type'])
            #   xcor_qc = next(m for m in quality_metrics if "SamtoolsFlagstatsQualityMetric" in m['@type'])
            # elif isinstance(notes,dict):
            if isinstance(notes, dict):
                # This needs to support the two formats from the old
                # accessionator and the new accession_analysis.
                if 'qc' in notes.get('qc'):  # new way
                    qc_from_notes = notes.get('qc')
                else:
                    qc_from_notes = notes
                raw_flagstats = qc_from_notes.get('qc')
                filtered_flagstats = qc_from_notes.get('filtered_qc')
                duplicates = qc_from_notes.get('dup_qc')
                xcor = qc_from_notes.get('xcor_qc')
                pbc = qc_from_notes.get('pbc_qc')
                try:
                    fract_mappable = (float(raw_flagstats.get('mapped')[0])
                                      / float(raw_flagstats.get('in_total')[0]))
                except:
                    fract_mappable = ''
                try:
                    paired_end = (filtered_flagstats.get('read1')[0]
                                  or filtered_flagstats.get('read1')[1]
                                  or filtered_flagstats.get('read2')[0]
                                  or filtered_flagstats.get('read2')[1])
                except:
                    paired_end_str = ''
                    usable_frags = ''
                else:
                    if paired_end:
                        usable_frags = (
                            filtered_flagstats.get('in_total')[0] / 2)
                        paired_end_str = 'PE'
                    else:
                        paired_end_str = 'SE'
                        usable_frags = filtered_flagstats.get('in_total')[0]
                row.update({'end': paired_end_str})

                try:
                    fract_usable = (float(filtered_flagstats.get('in_total')[0])
                                    / float(raw_flagstats.get('in_total')[0]))
                except:
                    fract_usable = ''

                if raw_flagstats:
                    row.update({
                        'hiq_reads': raw_flagstats.get('in_total')[0],
                        'loq_reads': raw_flagstats.get('in_total')[1],
                        'mappable': raw_flagstats.get('mapped')[0],
                        'fract_mappable': fract_mappable
                    })
                if filtered_flagstats:
                    row.update({
                        'usable_frags': usable_frags,
                        'fract_usable': fract_usable
                    })
                if pbc:
                    row.update({
                        'NRF': pbc.get('NRF'),
                        'PBC1': pbc.get('PBC1'),
                        'PBC2': pbc.get('PBC2')
                    })
                if xcor:
                    row.update({
                        'frag_len': xcor.get('estFragLen'),
                        'NSC': xcor.get('phantomPeakCoef'),
                        'RSC': xcor.get('relPhantomPeakCoef')
                    })
                if duplicates:
                    row.update({
                        'picard_read_pairs_examined': duplicates.get('read_pairs_examined'),
                        'picard_unpaired_reads_examined': duplicates.get('unpaired_reads_examined')
                    })
            rows.append(row)
    return rows

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=EPILOG,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--infile',
                        help='Input file containing experiment accessions to'
                        ' report on (overrides assay, rfa, lab, query_terms).',
                        type=argparse.FileType('r'))
    parser.add_argument('--server',
                        help='Full URL of the server.')
    parser.add_argument('--key',
                        default='default',
                        help='The keypair identifier from the keyfile.'
                        ' Default is --key=default.')
    parser.add_argument('--keyfile',
                        default=os.path.expanduser('~/keypairs.json'),
                        help='The keypair file. Default is --keyfile=%s'
                        % (os.path.expanduser('~/keypairs.json')))
    parser.add_argument('--authid',
                        help='The HTTP auth ID.')
    parser.add_argument('--authpw',
                        help='The HTTP auth PW.')
    parser.add_argument('--debug',
                        default=False,
                        action='store_true',
                        help='Print debug messages. Default is False.')
    parser.add_argument('--assembly',
                        help='The genome assembly to report on.',
                        default=None)
    parser.add_argument('--assay',
                        help='The assay_term_name to report on.',
                        default='ChIP-seq')
    parser.add_argument('--rfa',
                        help='ENCODE2 or ENCODE3. Omit for all.',
                        default=None)
    parser.add_argument('--lab',
                        help='ENCODE lab name, e.g. j-michael-cherry.',
                        default=None)
    parser.add_argument('--query_terms',
                        help='Additional query terms in the form "&term=value".',
                        default=None)
    parser.add_argument('--outfile',
                        help='CSV output.',
                        type=argparse.FileType('wb'),
                        default=sys.stdout)
    parser.add_argument('--create_google_sheet',
                        help='Create Google Sheet with conditional formatting.'
                        ' Default is False. Requires API key.',
                        default=False,
                        action='store_true')
    parser.add_argument('--sheet_title',
                        help='Name of Google Sheet.',
                        default='ENCODE ChIP QC')
    parser.add_argument('--apikey',
                        help='Path to secret credential for Google Sheets.',
                        default=os.path.expanduser(
                            '~/sheets.googleapis.com-python.json'))
    parser.add_argument('--released',
                        help='Bypasses authentication and only shows released results.',
                        default=False,
                        action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(
            format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(
            format='%(levelname)s:%(message)s', level=logging.WARNING)
    if args.released:
        keypair, authid, authpw = None, None, None
        server = PUBLIC_SERVER
    else:
        server, authid, authpw = processkeys(args)
        keypair = (authid, authpw)
    if args.assembly in ['hg19', 'GRCh38', 'GRCh38-minimal']:
        organism_name = 'human'
    elif args.assembly in ['mm10', 'mm9', 'mm10-minimal']:
        organism_name = 'mouse'
    else:
        organism_name = ''
    query = '/search/?type=experiment'
    if args.infile:
        for expid in args.infile:
            expid = expid.rstrip()
            if expid.startswith('#'):
                continue
            else:
                query += '&accession=%s' % (expid)
    else:
        query += '&status!=deleted'\
                 '&status!=revoked'\
                 '&status!=archived'\
                 '&status!=replaced'
        if args.assay:
            query += '&assay_term_name=%s' % (args.assay)
        if args.rfa:
            query += '&award.rfa=%s' % (args.rfa)
        if args.lab:
            query += '&lab.name=%s' % (args.lab)
        if organism_name:
            query += '&replicates.library.biosample.donor.organism.name=%s' % (
                organism_name)
        if args.query_terms:
            query += args.query_terms
    query += '&field=assay_term_name'\
             '&field=accession'\
             '&field=biosample_term_name'\
             '&field=biosample_type'\
             '&field=lab.name'\
             '&field=award.rfa'\
             '&field=target.name'\
             '&field=target.investigated_as'\
             '&field=internal_status'\
             '&format=json'\
             '&limit=all'
    url = urlparse.urljoin(server, query)
    logging.debug(url)
    result = get_ENCODE(url, authid, authpw)
    experiments = result['@graph']
    fieldnames = [
        'experiment',
        'experiment link',
        'target_type',
        'target',
        'biosample_name',
        'biosample_type',
        'biorep_id',
        'lab',
        'rfa',
        'assembly',
        'bam',
        'bam link',
        'unfiltered bam',
        'unfiltered bam link',
        'hiq_reads',
        'loq_reads',
        'mappable',
        'fract_mappable',
        'end',
        'r_lengths',
        'map_length',
        'crop_length',
        'picard_read_pairs_examined',
        'picard_unpaired_reads_examined',
        'usable_frags',
        'fract_usable',
        'NRF',
        'PBC1',
        'PBC2',
        'frag_len',
        'NSC',
        'RSC',
        'xcor plot',
        'library',
        'library aliases',
        'from fastqs',
        'platform',
        'date_created',
        'release status',
        'internal status',
        'dx_analysis']
    if args.create_google_sheet:
        # Force creation of temporary CSV that can be loaded into a DataFrame,
        # written to Google Sheets, then deleted.
        temp_file = 'temp_mapping_%s.tsv' % (args.assembly)
        args.outfile = open(temp_file, 'w')
    writer = csv.DictWriter(args.outfile,
                            fieldnames=fieldnames,
                            delimiter='\t',
                            quotechar='"')
    writer.writeheader()
    pool = Pool(100)
    get_rows_func = partial(get_rows,
                            server=server,
                            authid=authid,
                            authpw=authpw,
                            args=args)
    for rows in pool.imap_unordered(get_rows_func, experiments):
        for row in rows:
            writer.writerow(row)
    if args.create_google_sheet:
        args.outfile.close()
        # Load CSV data, sort.
        mapping_data = pd.read_table(temp_file)
        mapping_data = mapping_data.fillna('')
        mapping_data = mapping_data.sort_values(
            by=['lab', 'biosample_name', 'target', 'experiment'],
            ascending=[True, True, True, True])
        mapping_data = mapping_data.reset_index(drop=True)
        # Read sheet title and create unique page title.
        date = datetime.now().strftime('%m_%d_%Y')
        sheet_title = (
            args.sheet_title if not args.released
            else '{} Released'.format(args.sheet_title)
        )
        page_title = '%s_mapping_%s' % (args.assembly, date)
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
        wks.set_dataframe(mapping_data, copy_head=True, fit=True, start='A1')
        # Apply formatting and conditions.
        header['repeatCell']['range']['sheetId'] = wks.id
        wks.client.sh_batch_update(wks.spreadsheet.id, header)
        # Freeze header.
        freeze_header['updateSheetProperties']['properties']['sheetId'] = wks.id
        wks.client.sh_batch_update(wks.spreadsheet.id, freeze_header)
        # Resize font.
        font_size_format['repeatCell']['range']['sheetId'] = wks.id
        wks.client.sh_batch_update(wks.spreadsheet.id, font_size_format)
        # Add notes.
        batch_notes = []
        for k, v in notes_dict.items():
            # Don't overwrite template.
            blank_note = copy.deepcopy(note)
            num = mapping_data.columns.get_loc(k)
            blank_note['repeatCell']['range']['startColumnIndex'] = num
            blank_note['repeatCell']['range']['endColumnIndex'] = num + 1
            blank_note['repeatCell']['cell']['note'] = v
            blank_note['repeatCell']['range']['sheetId'] = wks.id
            batch_notes.append(blank_note)
        wks.client.sh_batch_update(wks.spreadsheet.id, batch_notes)
        # Format numbers.
        batch_numbers = []
        for k, v in number_cols.items():
            # Apply pattern to every column in cols.
            for col in v['cols']:
                # Don't overwrite template.
                blank_number_format = copy.deepcopy(number_format)
                num = mapping_data.columns.get_loc(col)
                blank_number_format['repeatCell']['range']['startColumnIndex'] = num
                blank_number_format['repeatCell']['range']['endColumnIndex'] = num + 1
                blank_number_format['repeatCell']['range']['sheetId'] = wks.id
                blank_number_format['repeatCell']['cell']['userEnteredFormat']['numberFormat']['pattern'] = v['pattern']
                batch_numbers.append(blank_number_format)
        wks.client.sh_batch_update(wks.spreadsheet.id, batch_numbers)
        # Apply conditional formatting.
        batch_conditions = []
        for k, v in condition_cols.items():
            for condition in v['conditions']:
                # Don't overwrite template.
                blank_condition = copy.deepcopy(condition_dict)
                # More descriptive names.
                condition_type = condition[0]
                condition_values = condition[1]
                condition_color = condition[2]
                # Fill in specifics.
                blank_condition['addConditionalFormatRule']['rule']['booleanRule']['condition']['type'] = condition_type
                # Don't do this for conditions (e.g. BLANK) that don't require values.
                if condition_values:
                    # Must loop through because NUMBER_BETWEEN condition requires two objects.
                    for value in condition_values:
                        blank_condition['addConditionalFormatRule']['rule']['booleanRule']['condition']['values'].append({
                            "userEnteredValue": value})
                blank_condition['addConditionalFormatRule']['rule']['booleanRule']['format']['backgroundColor']['red'] = condition_color[0]
                blank_condition['addConditionalFormatRule']['rule']['booleanRule'][
                    'format']['backgroundColor']['green'] = condition_color[1]
                blank_condition['addConditionalFormatRule']['rule']['booleanRule'][
                    'format']['backgroundColor']['blue'] = condition_color[2]
                # Find column number.
                num = mapping_data.columns.get_loc(k)
                blank_condition['addConditionalFormatRule']['rule']['ranges'][0]['startColumnIndex'] = num
                blank_condition['addConditionalFormatRule']['rule']['ranges'][0]['endColumnIndex'] = num + 1
                blank_condition['addConditionalFormatRule']['rule']['ranges'][0]['sheetId'] = wks.id
                batch_conditions.append(blank_condition)
        wks.client.sh_batch_update(wks.spreadsheet.id, batch_conditions)
        # Resize all columns.
        for i in range(wks.cols):
            try:
                wks.adjust_column_width(i, pixel_size=38)
                time.sleep(0.5)
            except RequestError:
                # Try again if response takes too long.
                wks.adjust_column_width(i, pixel_size=38)
        tiny_columns = ['experiment link',
                        'bam link',
                        'unfiltered bam',
                        'unfiltered bam link',
                        'loq_reads',
                        'end',
                        'xcor plot',
                        'dx_analysis']
        # Resize tiny columns.
        for i in [mapping_data.columns.get_loc(x) for x in tiny_columns]:
            wks.adjust_column_width(i, pixel_size=25)
        accession_columns = ['experiment',
                             'bam',
                             'library',
                             'library aliases',
                             'from fastqs',
                             'target']
        # Resize accession columns.
        for i in [mapping_data.columns.get_loc(x) for x in accession_columns]:
            wks.adjust_column_width(i, pixel_size=90)
        # Remove temp file.
        os.remove(temp_file)

    # for experiment in experiments:
        # t = Thread(target=write_rows, args=(experiment, server, authid, authpw, args))
        # t.start()
        # write_rows(experiment, server, authid, authpw, args)


if __name__ == '__main__':
    main()
