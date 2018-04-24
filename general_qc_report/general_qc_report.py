#!/usr/bin/env python

import argparse
import common
import dxpy
import logging
import pandas as pd
import os

from constants import (
    LIMIT_ALL_JSON,
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


def logger_warn_skip(expected_no, expected_type, experiment_id, len_data):
    logging.warn(
        'Expected %d unique %s in experiment %s. '
        'Found %d. Skipping!' % (expected_no, expected_type, experiment_id, len_data)
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


def filter_related_experiments(dataset, exp_data):
    return [e for e in exp_data if e.get('@id') == dataset]


def filter_quality_metrics_from_file(f, report_type):
    return [
        qc
        for qc in f.get('quality_metrics')
        if qc['@type'][0] in REPORT_TYPE_DETAILS[report_type]['qc_type']
    ]


def collapse_quality_metrics(q):
    if not isinstance(q, list):
        raise ValueError('Must pass in in list of objects')
    if len([field for qc in q for field in qc]) != len({field for qc in q for field in qc}):
        logging.warn(q)
        raise ValueError('Overlapping fields in object')
    new_q = {}
    [new_q.update(qc) for qc in q]
    return new_q


def get_job_id_from_file(f):
    job_id = f.get('step_run').get('dx_applet_details', [])[0].get('dx_job_id')
    if ':' in job_id:
        job_id = job_id.split(':')[1]
    return job_id


def get_dx_details_from_job_id(job_id):
    try:
        d = dxpy.describe(job_id)
        dx_details = {
            'job_id': job_id,
            'analysis': d.get('analysis'),
            'project': d.get('project'),
            'output': d.get('output')
        }
    except Exception as e:
        if any([x in str(e) for x in ['project-F3KkvG801gkPgbpfFbKqy28P', 'project-F3KkvG801gkPgbpfFbKqy28P']]):
            logging.warn('Project is gone!')
            dx_details = {}
        else:
            raise e
    return dx_details


def frip_in_output(output):
    return any(['frip' in k for k in output])


def parse_experiment_file_qc(e, f, q, report_type, base_url):
    job_id = get_job_id_from_file(f)
    dx_details = get_dx_details_from_job_id(job_id)
    output = dx_details.pop('output', {})
    has_frip = frip_in_output(output)
    qc_parsed = parse_json(q, REPORT_TYPE_DETAILS[report_type]['qc_fields'])
    qc_parsed['mad_plot'] = (
        '=image("%s%s%s", 1)' % (base_url, qc_parsed.get('@id'), qc_parsed.get('attachment').get('href'))
        if qc_parsed.get('attachment') and isinstance(qc_parsed.get('attachment'), dict)
        else None
        )
    qc_parsed.pop('attachment', None)
    row = {
        'analysis_date': f.get('date_created'),
        'assay_title': e.get('assay_title'),
        'experiment_accession': e.get('accession'),
        'experiment_status': e.get('status'),
        'target': e.get('target', {}).get('name'),
        'library_insert_size': ', '.join({
            lib
            for r in e.get('replicates', {})
            for lib in r.get('library', {}).values()
            if lib
        }),
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


def build_rows_from_experiment(experiment_data, file_data, report_type, base_url):
    '''
    Builds records that can be passed to a dataframe.
    For every experiment:
        1. Find every related file in file_data.
        2. Assert file_no file in group.
        3. Assert not more than qc_no QC metrics.
        4. Parse dx_job_id from file, get analysis_id.
        5. Parse QC metric (or return Nones)
        6. Append record to list.
    '''
    file_no = REPORT_TYPE_DETAILS[report_type]['file_no']
    qc_no = REPORT_TYPE_DETAILS[report_type]['qc_no']
    data = []
    for e in experiment_data:
        f = filter_related_files(e['@id'], file_data)
        if len(f) != file_no:
            logger_warn_skip(file_no, 'related file', e['@id'], len(f))
            continue
        f = f[0]
        q = filter_quality_metrics_from_file(f, report_type)
        if len(q) > qc_no:
            logger_warn_skip(qc_no, 'quality metric', e['@id'], len(q))
            continue
        q = q[0] if q else {}
        data.append(parse_experiment_file_qc(e, f, q, report_type, base_url))
    return data


def build_rows_from_file(experiment_data, file_data, report_type, base_url):
    '''
    Builds records that can be passed in to dataframe.
    For every file:
        1. Find experiment it belongs to (file.dataset == experiment.@id).
           Should just be one.
        2. Pull all unique QC metrics out of file.
        3. Parse experiment, file, and qc metrics.
    '''
    qc_no = REPORT_TYPE_DETAILS[report_type]['qc_no']
    data = []
    for f in file_data:
        e = filter_related_experiments(f['dataset'], experiment_data)
        if len(e) != 1:
            logger_warn_skip('one', 'related experiment', f['accession'], len(e))
            continue
        e = e[0]
        q = filter_quality_metrics_from_file(f, report_type)
        if len(q) != qc_no:
            logger_warn_skip(qc_no, 'quality_metric', f['accession'], len(q))
            continue
        q = collapse_quality_metrics(q)
        qc_fields = [
            field
            for item in REPORT_TYPE_DETAILS[report_type]['qc_fields']
            for field in item
        ]
        
        qc_parsed = parse_json(q, qc_fields)
             

def get_row_builder(report_type):
    if REPORT_TYPE_DETAILS[report_type]['row_builder'] == 'from_experiment':
        return build_rows_from_experiment
    elif REPORT_TYPE_DETAILS[report_type]['row_builder'] == 'from_file':
        return build_rows_from_file
    else:
        raise KeyError('Invalid row builder')


def format_dataframe(df, report_type):
    if REPORT_TYPE_DETAILS[report_type].get('col_order'):
        df = df[REPORT_TYPE_DETAILS[report_type].get('col_order')]
    if REPORT_TYPE_DETAILS[report_type].get('sort_order'):
        df = df.sort_values(by=REPORT_TYPE_DETAILS[report_type].get('sort_order'))
    return df


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
    build_rows = get_row_builder(args.report_type)
    rows = build_rows(experiment_data, file_data, args.report_type, base_url)
    df = pd.DataFrame(rows)
    df = format_dataframe(df, args.report_type)
    df.to_csv(
        '%s_report_%s.tsv' % (args.report_type, args.assembly),
        sep='\t',
        index=False
    )


if __name__ == '__main__':
    main()
