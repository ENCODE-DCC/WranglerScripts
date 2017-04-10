#!/usr/bin/env python2
# -*- coding: latin-1 -*-
'''Reports replicate mappings'''

import requests
import json
import csv
import copy
import logging
import sys
import os.path
import urlparse
import re
import time
# from threading import Lock, Thread
from multiprocessing import Pool
from functools import partial
import dxpy

EPILOG = '''
'''

CACHED_PLATFORMS = []
STATUS_TO_IGNORE = ['deleted', 'revoked', 'replaced', 'archived']
LAB_NAMES = ['encode-processing-pipeline']

fieldnames = [
    'experiment', 'experiment link', 'target_type', 'target',
    'biosample_name', 'biosample_type', 'biorep_id', 'lab', 'rfa',
    'assembly', 'bam', 'bam link', 'unfiltered bam', 'unfiltered bam link',
    'hiq_reads', 'loq_reads', 'mappable', 'fract_mappable', 'end',
    'r_lengths', 'map_length', 'crop_length', 'usable_frags', 'fract_usable',
    'NRF', 'PBC1', 'PBC2', 'frag_len', 'NSC', 'RSC', 'xcor plot',
    'library', 'library aliases', 'from fastqs', 'platform',
    'date_created', 'release status', 'internal status', 'dx_analysis']
writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, delimiter=',', quotechar='"')
# writer_lock = Lock()
# with writer_lock:
writer.writeheader()


def get_ENCODE(url, authid, authpw):
    '''force return from the server in JSON format'''
    '''GET an ENCODE object as JSON and return as dict'''
    if 'search' in url: #assume that a search query is complete except for &limit=all
        pass
    else:
        if '?' in url: # have to do this because it might be the first directive in the URL
            url += '&datastore=database'
        else:
            url += '?datastore=database'
    url += '&limit=all'
    logging.debug("GET %s" % (url))
    max_retries = 10
    retries = max_retries
    sleep_increment = 1
    while retries:
        try:
            response = requests.get(url, auth=(authid, authpw), headers={'accept': 'application/json'})
            response.raise_for_status()
        except:
            logging.debug('GET failed')
            logging.debug(response.text)
            logging.debug('Retry %d of %d' % ((max_retries-retries)+1, max_retries))
            retries -= 1
            time.sleep(sleep_increment*(max_retries-retries))
            continue
        else:
            break
    try:
        response.raise_for_status()
    except:
        logging.error('HTTP GET failed: %s %s %s' %(response.status_code, response.reason, url))

    logging.debug("GET response code: %s" %(response.status_code))
    try:
        # logging.debug("GET response json: %s" %(json.dumps(response.json(), indent=4, separators=(',', ': '))))
        return response.json()
    except:
        logging.debug("GET response text: %s" %(response.text))
        return {}


def processkeys(args):

    keysf = open(args.keyfile,'r')
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
    if not server.endswith("/"):
        server += "/"

    return server, authid, authpw


def flat_one(JSON_obj):
    try:
        return [JSON_obj[identifier] for identifier in \
                    ['accession', 'name', 'email', 'title', 'uuid', 'href'] \
                    if identifier in JSON_obj][0]
    except:
        return JSON_obj


def flat_ENCODE(JSON_obj):
    flat_obj = {}
    for key in JSON_obj:
        if isinstance(JSON_obj[key], dict):
            flat_obj.update({key:flat_one(JSON_obj[key])})
        elif isinstance(JSON_obj[key], list) and JSON_obj[key] != [] and isinstance(JSON_obj[key][0], dict):
            newlist = []
            for obj in JSON_obj[key]:
                newlist.append(flat_one(obj))
            flat_obj.update({key:newlist})
        else:
            flat_obj.update({key:JSON_obj[key]})
    return flat_obj


def pprint_ENCODE(JSON_obj):
    if ('type' in JSON_obj) and (JSON_obj['type'] == "object"):
        print json.dumps(JSON_obj['properties'], sort_keys=True, indent=4, separators=(',', ': '))
    else:
        print json.dumps(flat_ENCODE(JSON_obj), sort_keys=True, indent=4, separators=(',', ': '))


def get_platform_strings(fastqs, server, authid, authpw):
    platform_strings = []
    platform_uris = set([f.get('platform') for f in fastqs])
    for uri in platform_uris:
        if not uri:
            platform_strings.append('Missing')
            continue
        if uri not in [p.get('@id') for p in CACHED_PLATFORMS]:
            CACHED_PLATFORMS.append(
                get_ENCODE(urlparse.urljoin(server, uri), authid, authpw))
        platform_strings.append(next(p.get('title') for p in CACHED_PLATFORMS if p.get('@id') == uri))
    return platform_strings


def get_mapping_analysis(bam):
    try:
        job_alias = next(
            detail['dx_job_id'] for detail in bam['step_run']['dx_applet_details'])
    except:
        logging.error('Failed to find step_run.dx_applet_details in bam\n%s' % (bam))
        raise
    job_id = re.findall('job-\w*', job_alias)[0]
    analysis_id = dxpy.describe(job_id)['parentAnalysis']
    return dxpy.describe(analysis_id)


def get_analysis_url(analysis):
    if not analysis:
        return None
    project_uuid = analysis['project'].split('-')[1]
    analysis_uuid = analysis['id'].split('-')[1]
    analysis_url = "https://platform.dnanexus.com/projects/" + project_uuid + "/monitor/analysis/" + analysis_uuid
    return analysis_url


def get_crop_length(analysis):
    if not analysis:
        return None
    crop_length = next(stage['execution']['originalInput'].get('crop_length') for stage in analysis['stages'])
    return str(crop_length)


def write_rows(experiment, server, authid, authpw, args):
    rows = []
    row_template = {
        'experiment': experiment.get('accession'),
        'experiment link': urlparse.urljoin(server, '/experiments/%s' %(experiment.get('accession'))),
        'target_type': ','.join(experiment.get('target',{}).get('investigated_as') or []),
        'target': experiment.get('target',{}).get('name'),
        'biosample_name': experiment.get('biosample_term_name'),
        'biosample_type': experiment.get('biosample_type'),
        'lab': experiment.get('lab',{}).get('name'),
        'rfa': experiment.get('award',{}).get('rfa'),
        'internal status': experiment.get('internal_status')
    }
    original_files = get_ENCODE(urlparse.urljoin(server,'/search/?type=file&dataset=/experiments/%s/&file_format=fastq&file_format=bam&frame=embedded&format=json' %(experiment.get('accession'))),authid,authpw)['@graph']
    fastqs = [f for f in original_files if f.get('file_format') == 'fastq' and f.get('status') not in STATUS_TO_IGNORE]
    bams = \
        [f for f in original_files
         if f.get('file_format') == 'bam' and
         (not args.assembly or f.get('assembly') == args.assembly) and
         f.get('status') not in STATUS_TO_IGNORE and
         f['lab']['name'] in LAB_NAMES]
    filtered_bams = [f for f in bams if f.get('output_type') == 'alignments']
    unfiltered_bams = [f for f in bams if f.get('output_type') == 'unfiltered alignments']

    row = copy.deepcopy(row_template)

    if not bams:
        if not fastqs:
            row.update({'bam': "no fastqs"})
        else:
            row.update({'bam': "pending"})

            read_lengths =  set([str(f.get('read_length')) for f in fastqs])
            row.update({'r_lengths': ",".join(read_lengths)})

            paired_end_strs = []
            if any([f.get('run_type') == "single-ended" for f in fastqs]):
                paired_end_strs.append('SE')
            if any([f.get('run_type') == "paired-ended" for f in fastqs]):
                paired_end_strs.append('PE')
            if any([f.get('run_type') == "unknown" for f in fastqs]):
                paired_end_strs.append('unknown')
            row.update({'end': ",".join(paired_end_strs)})

            row.update({'platform': ",".join(get_platform_strings(fastqs, server, authid, authpw))})

        rows.append(row)
    else:
        for bam in filtered_bams:
            # derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in [obj.get('accession') for obj in bam.get('derived_from') or []]]
            derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in bam.get('derived_from') or []]
            derived_from_fastqs = [f for f in fastqs if f.get('accession') in derived_from_accessions]
            derived_from_fastq_accessions = [f.get('accession') for f in fastqs if f.get('accession') in derived_from_accessions]
            unfiltered_bam_accession = None
            unfiltered_bam_link = None
            for unfiltered_bam in unfiltered_bams:
                # ub_derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in [obj.get('accession') for obj in unfiltered_bam.get('derived_from') or []]]
                ub_derived_from_accessions = [os.path.basename(uri.rstrip('/')) for uri in unfiltered_bam.get('derived_from') or []]
                if set(derived_from_accessions) == set(ub_derived_from_accessions):
                    unfiltered_bam_accession = unfiltered_bam.get('accession')
                    unfiltered_bam_link = urlparse.urljoin(server, unfiltered_bam.get('href'))
                    break
            bioreps =       set([str(f.get('replicate').get('biological_replicate_number')) for f in derived_from_fastqs])
            library_uris =  set([str(f.get('replicate').get('library').get('@id'))                  for f in derived_from_fastqs])
            read_lengths =  set([str(f.get('read_length'))                                  for f in derived_from_fastqs])
            aliases = []
            libraries = []
            for uri in library_uris:
                library = get_ENCODE(urlparse.urljoin(server,'%s' %(uri)), authid, authpw)
                libraries.append(library.get('accession'))
                aliases.extend(library.get('aliases'))
            platform_strs = get_platform_strings(derived_from_fastqs, server, authid, authpw)
            try:
                xcor_plot_uri = next(qc['@id']+qc['cross_correlation_plot'].get('href') for qc in bam.get('quality_metrics') if qc.get('cross_correlation_plot'))
            except StopIteration:
                xcor_plot_link = 'Missing'
            else:
                xcor_plot_link = urlparse.urljoin(server, xcor_plot_uri)
            # mapping_analysis = get_mapping_analysis(bam)
            try:
                mapping_analysis = get_mapping_analysis(bam)
            except:
                mapping_analysis = None
            row.update({
                'biorep_id': ",".join(bioreps),
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
                'map_length': bam.get('mapped_read_length', ""),
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
            if isinstance(notes,dict):
                #this needs to support the two formats from the old accessionator and the new accession_analysis
                if 'qc' in notes.get('qc'): #new way
                    qc_from_notes = notes.get('qc')
                else:
                    qc_from_notes = notes
                raw_flagstats       = qc_from_notes.get('qc')
                filtered_flagstats  = qc_from_notes.get('filtered_qc')
                duplicates          = qc_from_notes.get('dup_qc')
                xcor                = qc_from_notes.get('xcor_qc')
                pbc                 = qc_from_notes.get('pbc_qc')

                try:
                    fract_mappable = float(raw_flagstats.get('mapped')[0])/float(raw_flagstats.get('in_total')[0])
                except:
                    fract_mappable = ''

                try:
                    paired_end = filtered_flagstats.get('read1')[0] or filtered_flagstats.get('read1')[1] or filtered_flagstats.get('read2')[0] or filtered_flagstats.get('read2')[1]
                except:
                    paired_end_str = ''
                    usable_frags = ''
                else:
                    if paired_end:
                        usable_frags = filtered_flagstats.get('in_total')[0]/2
                        paired_end_str = "PE"
                    else:
                        paired_end_str = "SE"
                        usable_frags = filtered_flagstats.get('in_total')[0]
                row.update({'end': paired_end_str})

                try:
                    fract_usable = float(filtered_flagstats.get('in_total')[0])/float(raw_flagstats.get('in_total')[0])
                except:
                    fract_usable = ''


                if raw_flagstats:
                    row.update({
                        'hiq_reads': raw_flagstats.get('in_total')[0],
                        'loq_reads': raw_flagstats.get('in_total')[1],
                        'mappable': raw_flagstats.get('mapped')[0],
                        'fract_mappable' : fract_mappable
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

            rows.append(row)
    for row in rows:
        writer.writerow(row)


def main():

    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__, epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--infile', help="Input file containing experiment accessions to report on (over-rides assay,rfa,lab,query_terms)", type=argparse.FileType('r'))
    parser.add_argument('--server', help="Full URL of the server.")
    parser.add_argument('--key', default='default', help="The keypair identifier from the keyfile.  Default is --key=default")
    parser.add_argument('--keyfile', default=os.path.expanduser("~/keypairs.json"), help="The keypair file.  Default is --keyfile=%s" %(os.path.expanduser("~/keypairs.json")))
    parser.add_argument('--authid', help="The HTTP auth ID.")
    parser.add_argument('--authpw', help="The HTTP auth PW.")
    parser.add_argument('--debug', default=False, action='store_true', help="Print debug messages.  Default is False.")
    parser.add_argument('--assembly', help="The genome assembly to report on", default=None)
    parser.add_argument('--assay', help="The assay_term_name to report on", default='ChIP-seq')
    parser.add_argument('--rfa', help='ENCODE2 or ENCODE3. Omit for all', default=None)
    parser.add_argument('--lab', help='ENCODE lab name, e.g. j-michael-cherry', default=None)
    parser.add_argument('--query_terms', help='Additional query terms in the form "&term=value"', default=None)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)

    server, authid, authpw = processkeys(args)
    keypair = (authid, authpw)
    if args.assembly in ['hg19','GRCh38','GRCh38-minimal']:
        organism_name = 'human'
    elif args.assembly in ['mm10','mm9','mm10-minimal']:
        organism_name = 'mouse'
    else:
        organism_name = ''

    query = "/search/?type=experiment"
    if args.infile:
        for expid in args.infile:
            expid = expid.rstrip()
            if expid.startswith('#'):
                continue
            else:
                query += "&accession=%s" % (expid)
    else:
        query += "&status!=deleted" \
                 "&status!=revoked" \
                 "&status!=replaced"
        if args.assay:
            query += '&assay_term_name=%s' % (args.assay)
        if args.rfa:
            query += '&award.rfa=%s' % (args.rfa)
        if args.lab:
            query += '&lab.name=%s' % (args.lab)
        if organism_name:
            query += '&replicates.library.biosample.donor.organism.name=%s' % (organism_name)
        if args.query_terms:
            query += args.query_terms

    query += "&field=assay_term_name" \
             "&field=accession" \
             "&field=biosample_term_name" \
             "&field=biosample_type" \
             "&field=lab.name" \
             "&field=award.rfa" \
             "&field=target.name" \
             "&field=target.investigated_as" \
             "&field=internal_status" \
             "&format=json" \
             "&limit=all"

    url = urlparse.urljoin(server, query)
    logging.debug(url)
    result = get_ENCODE(url, authid, authpw)
    experiments = result['@graph']

    pool = Pool(50)
    write_rows_func = partial(write_rows, server=server, authid=authid, authpw=authpw, args=args)
    pool.map(write_rows_func, experiments)
    # for experiment in experiments:
        # t = Thread(target=write_rows, args=(experiment, server, authid, authpw, args))
        # t.start()
        # write_rows(experiment, server, authid, authpw, args)


if __name__ == '__main__':
    main()
