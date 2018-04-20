#!/usr/bin/env python2

import common
import pprint

DEPRECATED_STATUSES = ['deleted', 'revoked', 'replaced']

authid, authpw, server = common.processkey()
# server = "https://test.encodedcc.org"
# authid = "JQYGP4PB"
# authpw = "pfk2f3f3stivzbct"
keypair = (authid, authpw)

experiments = common.encoded_get(
    'https://www.encodeproject.org/search/?'
    'type=Experiment&'
    'award.project=ENCODE',
    keypair)['@graph']

print "Got %d experiments" % (len(experiments))

all_GRCh38_bams = common.encoded_get(
    'https://www.encodeproject.org/search/?'
    'type=File&'
    'file_format=bam&'
    'assembly=GRCh38',
    keypair)['@graph']

print "Got %d bams" % (len(all_GRCh38_bams))

assay_titles = {}

for exp in experiments:
    bams = [f for f in all_GRCh38_bams if f['dataset'] == exp['@id']]
    if bams:
        # print "%s %s: %d GRCh38 bams" % (exp['accession'], exp['assay_title'], len(GRCh38_bams))
        if exp['assay_title'] in assay_titles:
            assay_titles[exp['assay_title']] += 1
            assay_titles[exp['assay_title']+'-files'].extend([f['accession'] for f in bams])
        else:
            assay_titles.update({
                exp['assay_title']: 1,
                exp['assay_title']+'-files' : [f['accession'] for f in bams]})
        for bam in bams:
            url = server+bam['@id']
            # print "\t%s %s %s" % (bam['accession'], bam['status'], url)
            # r = common.encoded_patch(url, keypair, {'assembly': "GRCh38-minimal"}, return_response=True)
            # try:
            #     r.raise_for_status()
            # except:
            #     print "PATCH error %s" % (r.text)
pprint.pprint(assay_titles)
