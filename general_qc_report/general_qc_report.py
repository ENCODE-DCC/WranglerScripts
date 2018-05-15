#!/usr/bin/env python

import argparse
import common
import dxpy
import logging
import numpy as np
import pandas as pd
import os

from constants import (
    LIMIT_ALL_JSON,
    REPORT_TYPES,
    REPORT_TYPE_DETAILS
)

from output import get_outputter


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
    logging.warn('Getting files and experiments from portal')
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
        ),
       additional='&limit=500&format=json'
    )
    file_data = get_data(file_url, keypair)
    return experiment_data, file_data


def get_references_data(base_url, keypair, report_type):
    logging.warn('Getting references from portal')
    references_data = []
    if REPORT_TYPE_DETAILS[report_type].get('get_references', False):
        references_url = make_url(
            base_url,
            (
                REPORT_TYPE_DETAILS[report_type]['references_query'] +
                REPORT_TYPE_DETAILS[report_type]['references_fields']
            )
        )
        references_data = get_data(references_url, keypair)
    return references_data


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


def is_nonoverlapping(q, report_type):
    qc_fields = REPORT_TYPE_DETAILS[report_type]['qc_fields']
    if not isinstance(q, list):
        raise KeyError('Must pass in in list of objects')
    list_of_fields = [field for qc in q for field in qc if field in qc_fields]
    set_of_fields = set(list_of_fields)
    if len(list_of_fields) != len(set_of_fields):
        raise ValueError('Overlapping fields in object')


def collapse_quality_metrics(q, report_type=None):
    if report_type is not None:
        is_nonoverlapping(q, report_type)
    new_q = {}
    [new_q.update(qc) for qc in q]
    return new_q


def get_job_id_from_file(f):
    job_id = f.get('step_run').get('dx_applet_details', [])[0].get('dx_job_id')
    if ':' in job_id:
        job_id = job_id.split(':')[1]
    return job_id


def get_dx_details_from_job_id(job_id, skip_dnanexus):
    try:
        d = {} if skip_dnanexus else dxpy.describe(job_id)
    except Exception as e:
        if any([
                x in str(e) for x in [
                    'project-F3KkvG801gkPgbpfFbKqy28P',
                    'project-F3KkvG801gkPgbpfFbKqy28P'
                ]
        ]):
            logging.warn('Project is gone!')
            d = {}
        else:
            raise e
    dx_details = {
            'job_id': job_id,
            'analysis': d.get('analysis'),
            'project': d.get('project'),
            'output': d.get('output', {})
        }
    return dx_details


def frip_in_output(output):
    return any(['frip' in k for k in output])


def resolve_spikein_description(row, references_data):
    spikein_details = {
        description
        for spikein in row.get('spikeins_used', [])
        for description in [
                r.get('description')
                for r in references_data
                if r.get('@id') == spikein
        ]
    }
    row['spikeins_used'] = ', '.join(row['spikeins_used'])
    row['spikein_description'] = ', '.join(spikein_details)
    return row


def process_qc(base_url, qc_parsed, output_type):
    # Make attachment image with link.
    if all([qc_parsed.get('attachment'),
            isinstance(qc_parsed.get('attachment'), dict),
            qc_parsed.get('@id')]):
        url = base_url + qc_parsed.get('@id') + qc_parsed.get('attachment').get('href')
        qc_parsed['attachment'] = '=hyperlink("%s", image("%s", 2))' % (url, url) if output_type == 'google_sheets' else url
        qc_parsed.pop('@id', None)
    return qc_parsed


def parse_experiment_file_qc(e, f, q, report_type, base_url, args, references_data):
    job_id = get_job_id_from_file(f)
    dx_details = get_dx_details_from_job_id(job_id, args.skip_dnanexus)
    output = dx_details.pop('output', {})
    has_frip = frip_in_output(output)
    qc_parsed = parse_json(q, REPORT_TYPE_DETAILS[report_type]['qc_fields'])
    qc_processed = process_qc(base_url, qc_parsed, args.output_type)
    row = {
        'analysis_date': f.get('date_created'),
        'assay_title': e.get('assay_title'),
        'output_type': f.get('output_type'),
        'experiment_accession': e.get('accession'),
        'experiment_status': e.get('status'),
        'target': e.get('target', {}).get('name'),
        'read_length': ', '.join({
            str(f.get('read_length'))
            for f in e.get('files', [])
            if f.get('read_length')
        }),
        'run_type': ', '.join({
            f.get('run_type')
            for f in e.get('files', [])
            if f.get('run_type')
        }),
        'library_insert_size': ', '.join({
            r.get('library', {}).get('size_range')
            for r in e.get('replicates', [])
            if r.get('library', {}).get('size_range')
        }),
        'spikeins_used': list({
            s
            for r in e.get('replicates', [])
            for s in r.get('library', {}).get('spikeins_used')
            if r.get('library', {}).get('spikeins_used')
        }),
        'strand_specificity': ', '.join({
            str(r.get('library', {}).get('strand_specificity'))
            for r in e.get('replicates', [])
            if r.get('library', {}).get('strand_specificity') is not None
        }),
        'depleted_in_term_name': ', '.join({
            t
            for r in e.get('replicates', [])
            for t in r.get('library', {}).get('depleted_in_term_name', [])
            if r.get('library', {}).get('depleted_in_term_name')
        }),
        'biosample_term_name': e.get('biosample_term_name'),
        'biosample_type': e.get('biosample_type'),
        'replication': e.get('replication_type'),
        'lab': e.get('lab', {}).get('name'),
        'rfa': e.get('award', {}).get('rfa'),
        'assembly': f.get('assembly'),
        'biological_replicates': ', '.join({
            str(r)
            for r in f.get('biological_replicates', [])
            if f.get('biological_replicates', [])
        }),
        'has_frip': has_frip
    }
    row = resolve_spikein_description(row, references_data)
    row.update(qc_processed)
    row.update(dx_details)
    return row


def build_rows_from_experiment(experiment_data, file_data, references_data, report_type, base_url, args):
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
        data.append(parse_experiment_file_qc(e, f, q, report_type, base_url, args, references_data))
    return data


def build_rows_from_file(experiment_data, file_data, references_data, report_type, base_url, args):
    '''
    Builds records that can be passed in to dataframe.
    For every file:
        1. Find experiment it belongs to (file.dataset == experiment.@id).
           Should just be one.
        2. Pull all unique QC metrics out of file.
        3. Parse experiment, file, and qc metrics.
    '''
    # Flatten list of lists.
    qc_fields = [
        field
        for item in REPORT_TYPE_DETAILS[report_type]['qc_fields']
        for field in item
    ]
    # Set global qc_fields to flattened list.
    REPORT_TYPE_DETAILS[report_type]['qc_fields'] = qc_fields
    qc_no_min = REPORT_TYPE_DETAILS[report_type]['qc_no_min']
    qc_no_max = REPORT_TYPE_DETAILS[report_type]['qc_no_max']
    data = []
    for f in file_data:
        e = filter_related_experiments(f['dataset'], experiment_data)
        if len(e) != 1:
            logger_warn_skip(1, 'related experiment', f['accession'], len(e))
            continue
        e = e[0]
        q = filter_quality_metrics_from_file(f, report_type)
        if not qc_no_min <= len(q) <= qc_no_max:
            logger_warn_skip(qc_no_max, 'quality_metric', f['accession'], len(q))
            continue
        # Collapse list of quality metrics to one object.
        q = collapse_quality_metrics(q, report_type)
        row = parse_experiment_file_qc(e, f, q, report_type, base_url, args, references_data)
        row.update({'file_accession': f.get('accession')})
        data.append(row)
    return data


def get_row_builder(report_type):
    if REPORT_TYPE_DETAILS[report_type]['row_builder'] == 'from_experiment':
        return build_rows_from_experiment
    elif REPORT_TYPE_DETAILS[report_type]['row_builder'] == 'from_file':
        return build_rows_from_file
    else:
        raise KeyError('Invalid row builder')


def build_url_from_accession(accession, base_url, output_type):
    url = '%s%s' % (base_url, accession)
    if output_type == 'google_sheets':
        return '=hyperlink("%s", "%s")' % (url, accession)
    return url


def calculate_read_depth(star_unique, star_multi):
    try:
        return star_unique + star_multi
    except TypeError:
        return np.nan


def contains_columns(df, columns):
    return all([
        col in df.columns
        for col in columns
    ])


def add_read_depth(df):
    # RNA mapping read_depth.
    star_unique = 'star_uniquely_mapped_reads_number'
    star_multi = 'star_number_of_reads_mapped_to_multiple_loci'
    if contains_columns(df, [star_unique, star_multi]):
        df['read_depth'] = df[[star_unique, star_multi]].apply(
            lambda x: calculate_read_depth(x[0], x[1]),
            axis=1
        )
    return df


def format_dataframe(df, report_type, base_url, output_type):
    # Rename columns.
    if REPORT_TYPE_DETAILS[report_type].get('rename_columns'):
        df = df.rename(columns=REPORT_TYPE_DETAILS[report_type].get('rename_columns'))
    # Collapse list to string.
    if 'quality_metric_of' in df.columns:
        df['quality_metric_of'] = df['quality_metric_of'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) else x
        )
    # Make links from accessions.
    if 'experiment_accession' in df.columns:
        df['experiment_accession'] = df['experiment_accession'].apply(
            lambda accession: build_url_from_accession(accession, base_url, output_type)
        )
    if 'file_accession' in df.columns:
        df['file_accession'] = df['file_accession'].apply(
            lambda accession: build_url_from_accession(accession, base_url, output_type)
        )
    # Add read_depth if needed.
    df = add_read_depth(df)
    # Sort and select columns at end.
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
    parser.add_argument(
        '--sheet_title',
        help='Name of Google Sheet.',
        default='ENCODE QC'
    )
    parser.add_argument(
        '--api_key',
        help='Path to secret credential for Google Sheets.',
        default=os.path.expanduser('~/sheets.googleapis.com-python.json')
    )
    parser.add_argument(
        '-o', '--output_type',
        help='Output to TSV or Google Sheets (requires authentication)',
        choices=['tsv', 'google_sheets'],
        default='tsv'
    )
    parser.add_argument(
        '-s', '--skip_dnanexus',
        help='Skip requests from DNAnexus (much faster)',
        action='store_true'
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
    references_data = get_references_data(base_url, keypair, args.report_type)
    build_rows = get_row_builder(args.report_type)
    rows = build_rows(
        experiment_data,
        file_data,
        references_data,
        args.report_type,
        base_url,
        args
    )
    df = pd.DataFrame(rows)
    df = format_dataframe(df, args.report_type, base_url, args.output_type)
    outputter = get_outputter(args.output_type)
    outputter(df, args)


if __name__ == '__main__':
    main()
