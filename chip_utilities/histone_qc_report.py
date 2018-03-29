#!/usr/bin/env python
import argparse
import common
import logging
import os

LIMIT_ALL_JSON = '&limit=all&format=json'

HISTONE_PEAK_FILES_QUERY = (
    '/search/?type=File'
    '&output_type=replicated+peaks'
    '&output_type=stable+peaks'
    '&lab.title=ENCODE+Processing+Pipeline'
    '&file_format=bed'
    '&status=released'
    '&status=in+progress&status=uploading'
)

CHIP_EXPERIMENTS_QUERY = (
    '/search/?type=Experiment'
    '&assay_title=ChIP-seq'
    '&award.project=ENCODE'
    '&status=released'
    '&status=in+progress&status=submitted'
)

# Only download needed fields.
EXPERIMENT_FIELDS_QUERY = (
    '&field=@id'
    '&field=accession'
    '&field=status'
    '&field=award.rfa'
    '&field=target.name'
    '&field=biosample_term_name'
    '&field=biosample_type'
    '&field=replication_type'
    '&field=lab.name'
)

HISTONE_QC_FIELDS = [
    'nreads',
    'nreads_in_peaks',
    'npeak_overlap',
    'Fp',
    'Ft',
    'F1',
    'F2'
]


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


def get_data(url, keypair):
    logging.debug('Getting %s' % url)
    results = common.encoded_get(url, keypair)
    return results['@graph']


def get_experiments_and_files(base_url, keypair):
    experiment_url = make_url(base_url, CHIP_EXPERIMENTS_QUERY + EXPERIMENT_FIELDS_QUERY)
    experiment_data = get_data(experiment_url, keypair)
    file_url = make_url(base_url, HISTONE_PEAK_FILES_QUERY)
    file_data = get_data(file_url, keypair)
    return experiment_data, file_data


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
        required=True
    )
    return parser.parse_args()


def main():
    args = get_args()
    logging.basicConfig(level=args.log_level)
    authid, authpw, base_url = common.processkey(args.key, args.keyfile)
    keypair = (authid, authpw)

    experiment_data, file_data = get_experiments_and_files(base_url, keypair)


if __name__ == '__main__':
    main()
