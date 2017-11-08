#!/usr/bin/env python2

import common
import dxpy
import logging
import os
import re
import pprint

EPILOG = '''Notes:

Examples:

    %(prog)s
'''


def get_args():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    def t_or_f(arg):
        ua = str(arg).upper()
        if ua == 'TRUE'[:len(ua)]:
            return True
        elif ua == 'FALSE'[:len(ua)]:
            return False
        else:
            assert not (True or False), "Cannot parse %s to boolean" % (arg)

    parser.add_argument('folder', help='Folder in which to look for files to rename.', nargs='*', default='/fastqs/')
    parser.add_argument('--debug', help="Print debug messages", default=False, action='store_true')
    parser.add_argument('--project', help="DX project name or ID", default=dxpy.WORKSPACE_ID)
    parser.add_argument('--key', help="The local keypair identifier from the local keyfile. Default is 'default'", default='www')
    parser.add_argument('--keyfile', help="The local keypair filename.", default=os.path.expanduser("~/keypairs.json"))
    parser.add_argument('--dry_run', help="Just report what will be done", default=False, action='store_true')

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


def resolve_project(identifier, privs='r'):
    project = dxpy.find_one_project(name=identifier, level='VIEW', name_mode='exact', return_handler=True, zero_ok=True)
    if project == None:
        try:
            project = dxpy.get_handler(identifier)
        except:
            logging.error('Could not find a unique project with name or id %s' %(identifier))
            raise ValueError(identifier)
    logging.debug('Project %s access level is %s' %(project.name, project.describe()['level']))
    if privs == 'w' and project.describe()['level'] == 'VIEW':
        logging.error('Output project %s is read-only' %(identifier))
        raise ValueError(identifier)
    return project


def main():
    args = get_args()

    authid, authpw, server = common.processkey(args.key, args.keyfile)
    keypair = (authid, authpw)
    project = resolve_project(args.project)
    SRR_files = dxpy.find_data_objects(
                    name="SRR???????_?.fastq.gz", name_mode='glob',
                    classname='file', recurse=True, return_handler=True,
                    folder=args.folder, project=args.project)
    for srr_dxfile in SRR_files:
        m = re.search('(SRR.{7})_(\d)', srr_dxfile.name)
        if m:
            srr_basename = m.group(1)
            end_num = m.group(2)
        else:
            assert m
        srr_encfiles = common.encoded_get('/'.join([server,'search/?type=File&external_accession=%s&status!=deleted&status!=replaced&status!=revoked' % (srr_basename)]), keypair)['@graph']
        if not srr_encfiles:
            logging.error('%s object not found at ENCODE.  Skipping.' % (srr_basename))
            continue
        elif len(srr_encfiles) > 1:
            logging.error('%s multiple matching objects found at ENCODE.  Skipping.' % (srr_basename))
            continue
        else:
            srr_encfile = srr_encfiles[0]
        # experiment = common.encoded_get('/'.join([server, srr_encfile.get('dataset')]), keypair)
        # replicate = common.encoded_get('/'.join([server, srr_encfile.get('replicate')]), keypair)
        # biorep_n = replicate.get('biological_replicate_number')
        all_fastqs = common.encoded_get('/'.join([
            server,
            'search/?type=File&file_format=fastq&derived_from=/files/%s/&status!=deleted&status!=revoked&status!=replaced' % (srr_basename)
        ]), keypair)['@graph']
        if not all_fastqs:
            print("%s: no fastq(s) found.  Skipping." % (srr_dxfile.name))
            continue
        if end_num == '1':
            fastqs = [f for f in all_fastqs if f.get('run_type') == 'single-ended' or f.get('paired_end') == end_num]
        elif end_num in ['2', '3']:
            fastqs = [f for f in all_fastqs if f.get('run_type') == 'paired-ended' and f.get('paired_end') == '2']
        if not fastqs:
            print("%s: no fastq(s) found for paired_end %s.  Skipping" % (srr_basename, end_num))
            continue
        elif len(fastqs) > 1:
            print("%s: ambiguous matches to %s.  Skipping" % (srr_basename, [f.get('accession') for f in fastqs]))
            continue
        else:
            fastq = fastqs[0]
            newname = '%s.fastq.gz' % (fastq.get('accession'))
            if args.dry_run:
                print('dry_run: Could rename %s to %s' % (srr_dxfile.name, newname))
            else:
                srr_dxfile.set_properties({'srr_filename': srr_dxfile.name})
                srr_dxfile.rename(newname)
                print('%s renamed to %s' % (srr_dxfile.name, newname))


if __name__ == '__main__':
    main()
