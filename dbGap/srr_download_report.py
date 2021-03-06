#!/usr/bin/env python2

import sys
import logging
import csv
import dxpy

EPILOG = '''Notes:

Examples:

    %(prog)s
'''


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('SRRs', help='List of SRR ids.', nargs='*', default=None)
    parser.add_argument('--infile', help='File containing SRR ids', type=argparse.FileType('rU'), default=sys.stdin)
    parser.add_argument('--outfile', help='tsv table of files with metadata', type=argparse.FileType('wb'), default=sys.stdout)
    parser.add_argument('--project', help="Output project name or ID", default=dxpy.WORKSPACE_ID)
    parser.add_argument('--debug', help="Print debug messages", default=False, action='store_true')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            format='%(levelname)s:%(message)s', level=logging.DEBUG)
        logging.debug("Logging level set to DEBUG")
    else:  # use the defaulf logging level
        logging.basicConfig(
            format='%(levelname)s:%(message)s')
        logging.info("Logging level set to detault")

    return args


def main():
    args = get_args()
    # applets = list(dxpy.find_data_objects(classname='applet', name='dbgap_sra_to_fastq*', name_mode='glob', project=args.project, return_handler=True))
    # assert applets
    srrs = args.SRRs or args.infile
    fieldnames = ['SRR', 'sra_size', 'sra_md5', 'fastq_id', 'fastq_alias', 'fastq_size', 'fastq_name', 'fastq_md5']
    writer = csv.DictWriter(args.outfile, fieldnames, delimiter='\t')
    writer.writeheader()
    # jobs = []
    # for applet in applets:
    #     jobs.extend(list(dxpy.find_executions(executable=applet, describe=True, first_page_size=1000)))
    for row in srrs:
        if row.startswith('#'):
            continue
        srr = row.strip()
        srr_jobs = [j.get('describe') for j in dxpy.find_executions(describe=True, name="%s_sra_to_fastq" % (srr))]
        # srr_jobs = [j['describe'] for j in jobs if j['describe'].get('state') == 'done' and srr in j['describe']['input']['SRR']]
        if not srr_jobs:
            writer.writerow({'SRR': "%s: not downloaded" % (srr)})
        else:
            if not any([job.get('state') == 'done' for job in srr_jobs]):
                for job in srr_jobs:
                    writer.writerow({'SRR': "%s: job %s %s" %(srr, job.get('id'), job.get('state'))})
            else:
                for job in [j for j in srr_jobs if j.get('state') == 'done']:
                    outrow = {
                        'SRR': job['input'].get('SRR'),
                        'sra_size': job['output'].get('sra_size'),
                        'sra_md5': job['output'].get('sra_md5')
                    }
                    for i, fastq in enumerate(job['output'].get('fastq')):
                        fh = dxpy.DXFile(job['output'].get('fastq')[i])
                        try:
                            file_size = fh.describe().get('size')
                            file_name = fh.name
                        except dxpy.exceptions.ResourceNotFound:
                            file_size = 'deleted'
                            file_name = 'deleted'
                        outrow.update({
                            'fastq_id': fh.get_id(),
                            'fastq_alias': ":".join(["dnanexus", fh.get_id()]),
                            'fastq_size': file_size,
                            # 'fastq_name': job['output'].get('fastq_filenames')[i],
                            'fastq_name': file_name,
                            'fastq_md5': job['output'].get('fastq_md5s')[i]
                        })
                        writer.writerow(outrow)


if __name__ == '__main__':
    main()
