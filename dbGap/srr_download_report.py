#!/usr/bin/env python2

import dxpy
import csv
import sys

fieldnames = \
    ['SRR', 'sra_size', 'sra_md5', 'fastq_filename', 'fastq_size', 'fastq_md5']
writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
writer.writeheader()

for dxobj in dxpy.find_data_objects(classname="file", folder='/fastqs/',
                                    return_handler=True):
    file = dxobj.describe()
    job = dxpy.DXJob(file['createdBy']['job']).describe()
    index = job['output']['fastq_filenames'].index(file['name'])
    row = {
        'SRR': job['input']['SRR'],
        'sra_size': job['output']['sra_size'],
        'sra_md5': job['output']['sra_md5'],
        'fastq_filename': file['name'],
        'fastq_size': file['size'],
        'fastq_md5': job['output']['fastq_md5s'][index]
    }
    writer.writerow(row)
