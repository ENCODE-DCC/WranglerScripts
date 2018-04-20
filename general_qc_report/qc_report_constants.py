'''
module containing constants used by qc reporting tools
'''

LIMIT_ALL_JSON = '&limit=all&format=json'

HISTONE_PEAK_FILES_QUERY = ('/search/?type=File'
                            '&output_type=replicated+peaks'
                            '&output_type=stable+peaks'
                            '&lab.title=ENCODE+Processing+Pipeline'
                            '&file_format=bed'
                            '&status=released'
                            '&status=in+progress'
                            '&status=uploading')

HISTONE_CHIP_EXPERIMENTS_QUERY = ('/search/?type=Experiment'
                                  '&assay_title=ChIP-seq'
                                  '&target.investigated_as=histone'
                                  '&award.project=ENCODE'
                                  '&status=released'
                                  '&status=in+progress'
                                  '&status=submitted')

# Only download needed fields.
EXPERIMENT_FIELDS_QUERY = ('&field=@id'
                           '&field=accession'
                           '&field=status'
                           '&field=award.rfa'
                           '&field=date_created'
                           '&field=target.name'
                           '&field=biosample_term_name'
                           '&field=biosample_type'
                           '&field=replication_type'
                           '&field=lab.name')

FILE_FIELDS_QUERY = ('&field=@id'
                     '&field=accession'
                     '&field=date_created'
                     '&field=status'
                     '&field=dataset'
                     '&field=assembly'
                     '&field=step_run'
                     '&field=quality_metrics'
                     '&field=notes')

HISTONE_QC_FIELDS = [
    'nreads', 'nreads_in_peaks', 'npeak_overlap', 'Fp', 'Ft', 'F1', 'F2',
    'quality_metric_of'
]
