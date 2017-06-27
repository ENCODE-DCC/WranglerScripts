#!/usr/bin/env python

import os.path
import sys
import logging
import csv
import common

logger = logging.getLogger(__name__)

EPILOG = '''Notes:

Examples:

    %(prog)s
'''


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
                        ' (e.g. hg19 or GRCg38',
                        required=True)

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
                  'output_type']
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
                    '%s: Found %d IDR step runs. Skipping'
                    % (experiment_id, len(idr_step_runs)))
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
        output_type = idr.get('output_type', na)
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
               'output_type': output_type
               }
        writer.writerow(row)


if __name__ == '__main__':
    main()
