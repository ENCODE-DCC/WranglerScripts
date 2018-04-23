#!/usr/bin/env python

import argparse
import common
import dxpy
import logging
import pandas as pd
import os

from constants import (
    LIMIT_ALL_JSON,
    EXPERIMENT_FIELDS_QUERY,
    FILE_FIELDS_QUERY,
    HISTONE_PEAK_FILES_QUERY,
    HISTONE_CHIP_EXPERIMENTS_QUERY,
    HISTONE_QC_FIELDS,
    RNA_EXPERIMENTS_QUERY,
    RNA_QUANTIFICATION_FILES_QUERY,
    RNA_MAPPING_FILES_QUERY,
    REPORT_TYPES,
    REPORT_TYPE_DETAILS
)


def make_url(base_url, query, additional=LIMIT_ALL_JSON):
    '''
    Returns full URL.
    '''
    end = additional if isinstance(additional, str) else ''.join(additional)
    return base_url + query + end


def parse_json(json_object, fields):
    '''
    Returns object filtered by fields.
    '''
    return {
        field: json_object.get(field)
        for field in fields
    }


def logger_warn_skip(expected_type, experiment_id, len_data):
    logging.warn(
        'Expected one unique %s in experiment %s. '
        'Found %d. Skipping!' % (expected_type, experiment_id, len_data)
    )


def get_data(url, keypair):
    '''
    Makes GET request.
    '''
    logging.debug('Getting %s' % url)
    results = common.encoded_get(url, keypair)
    return results['@graph']


def get_experiments_and_files(base_url, keypair, report_type, assembly):
    '''
    Returns all relevant experiment and files.
    '''
    experiment_url = make_url(
        base_url,
        (
            REPORT_TYPE_DETAILS[report_type]['experiment_query'] +
            REPORT_TYPE_DETAILS[report_type]['experiment_fields'] +
            '&assembly=%s' % assembly
        )
    )
    experiment_data = get_data(experiment_url, keypair)
    file_url = make_url(
        base_url,
        (
            REPORT_TYPE_DETAILS[report_type]['file_query'] +
            REPORT_TYPE_DETAILS[report_type]['file_fields'] +
            '&assembly=%s' % assembly
        )
    )
    file_data = get_data(file_url, keypair)
    return experiment_data, file_data


def filter_related_files(experiment_id, file_data):
    return [f for f in file_data if f.get('dataset') == experiment_id]


def get_job_id_from_file(f):
    job_id = f.get('step_run').get('dx_applet_details', [])[0].get('dx_job_id')
    if job_id:
        job_id = job_id.split(':')[1]
    return job_id


def get_dx_details_from_job_id(job_id):
    d = dxpy.describe(job_id)
    return {
        'job_id': job_id,
        'analysis': d.get('analysis'),
        'project': d.get('project'),
        'output': d.get('output')
    }


def frip_in_output(output):
    return any(['frip' in k for k in output])


def parse_experiment_file_qc(e, f, q):
    job_id = get_job_id_from_file(f)
    dx_details = get_dx_details_from_job_id(job_id)
    output = dx_details.pop('output', None)
    has_frip = frip_in_output(output)
    qc_parsed = parse_json(q, HISTONE_QC_FIELDS)
    row = {
        'date': f.get('date_created'),
        'experiment_accession': e.get('accession'),
        'experiment_status': e.get('status'),
        'target': e.get('target', {}).get('name'),
        'biosample_term_name': e.get('biosample_term_name'),
        'biosample_type': e.get('biosample_type'),
        'replication': e.get('replication_type'),
        'lab': e.get('lab', {}).get('name'),
        'rfa': e.get('award', {}).get('rfa'),
        'assembly': f.get('assembly'),
        'has_frip': has_frip
    }
    row.update(qc_parsed)
    row.update(dx_details)
    return row


def build_rows(experiment_data, file_data):
    '''
    Builds records that can be passed to a dataframe.
    For every experiment:
        1. Find every related file in file_data.
        2. Assert one file in group.
        3. Assert not more than one QC metric.
        4. Parse dx_job_id from file, get analysis_id.
        5. Parse QC metric (or return Nones)
        6. Append record to list.
    '''
    data = []
    for e in experiment_data:
        f = filter_related_files(e['@id'], file_data)
        if len(f) != 1:
            logger_warn_skip('related file', e['@id'], len(f))
            continue
        f = f[0]
        q = f.get('quality_metrics')
        if len(q) > 1:
            logger_warn_skip('quality metric', e['@id'], len(q))
            continue
        q = q[0] if q else {}
        data.append(parse_experiment_file_qc(e, f, q))
    return data


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-d', '--debug',
        help='Print debug messages.',
        action='store_const',
        dest='log_level',
        const=logging.DEBUG,
        default=logging.WARNING
    )
    parser.add_argument(
        '--key',
        help='The keypair identifier from the keyfile.',
        default='www'
    )
    parser.add_argument(
        '--keyfile',
        help='The keyfile.',
        default=os.path.expanduser('~/keypairs.json')
    )
    parser.add_argument(
        '--assembly',
        help='Genome assembly.',
        choices=['GRCh38', 'hg19', 'mm10'],
        required=True
    )
    parser.add_argument(
        '-r', '--report_type',
        help='Report type.',
        choices=REPORT_TYPES,
        required=True
    )
    return parser.parse_args()


def main():
    args = get_args()
    logging.basicConfig(level=args.log_level)
    authid, authpw, base_url = common.processkey(args.key, args.keyfile)
    keypair = (authid, authpw)
    experiment_data, file_data = get_experiments_and_files(
        base_url,
        keypair,
        args.report_type,
        args.assembly
    )
    rows = build_rows(experiment_data, file_data)
    df = pd.DataFrame(rows)
    df.to_csv('histone_qc_report_%s.tsv' % args.assembly, sep='\t', index=False)


if __name__ == '__main__':
    main()
