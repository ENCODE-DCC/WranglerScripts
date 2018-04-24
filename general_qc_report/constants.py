'''
module containing constants used by qc reporting tools
'''
# GENERIC

LIMIT_ALL_JSON = '&limit=all&format=json'

REPORT_TYPES = [
    'histone_qc',
    'histone_mapping',
    'tf_mapping',
    'tf_qc',
    'rna_mapping',
    'rna_qc'
]

# Only download needed fields.
EXPERIMENT_FIELDS_QUERY = (
    '&field=@id'
    '&field=accession'
    '&field=status'
    '&field=award.rfa'
    '&field=date_created'
    '&field=target.name'
    '&field=biosample_term_name'
    '&field=biosample_type'
    '&field=replication_type'
    '&field=lab.name'
    '&field=replicates.library.size_range'
    '&field=assay_title'
)

FILE_FIELDS_QUERY = (
    '&field=@id'
    '&field=accession'
    '&field=date_created'
    '&field=status'
    '&field=dataset'
    '&field=assembly'
    '&field=step_run'
    '&field=quality_metrics'
    '&field=notes'
)

# HISTONE SPECIFIC

HISTONE_PEAK_FILES_QUERY = (
    '/search/?type=File'
    '&output_type=replicated+peaks'
    '&output_type=stable+peaks'
    '&lab.title=ENCODE+Processing+Pipeline'
    '&file_format=bed'
    '&status=released'
    '&status=in+progress'
    '&status=uploading'
)

HISTONE_CHIP_EXPERIMENTS_QUERY = (
    '/search/?type=Experiment'
    '&assay_title=ChIP-seq'
    '&target.investigated_as=histone'
    '&award.project=ENCODE'
    '&status=released'
    '&status=in+progress'
    '&status=submitted'
)

HISTONE_QC_FIELDS = [
    '@id',
    'nreads',
    'nreads_in_peaks',
    'npeak_overlap',
    'Fp',
    'Ft',
    'F1',
    'F2',
    'quality_metric_of'
]


# RNA SPECIFIC

RNA_MQM_EXPERIMENTS_QUERY = (
    '/search/?type=Experiment'
    '&award.project=ENCODE'
    '&award.project=Roadmap'
    '&replication_type!=unreplicated'
    '&assay_slims=Transcription'
    '&assay_title=polyA+RNA-seq'
    '&assay_title=total+RNA-seq'
    '&assay_title=small+RNA-seq'
    '&assay_title=single+cell+RNA-seq'
    '&assay_title=microRNA-seq'
    '&assay_title=CRISPRi+RNA-seq'
    '&assay_title=CRISPR+RNA-seq'
    '&assay_title=polyA+depleted+RNA-seq'
    '&assay_title=shRNA RNA-seq'
    '&status=released'
    '&status=in+progress'
    '&status=submitted'
)

RNA_QUANTIFICATION_FILES_QUERY = (
    '/search/?type=File'
    '&lab.title=ENCODE+Processing+Pipeline'
    '&output_type=gene+quantifications'
    '&file_format=tsv'
    '&status=released'
    '&status=in+progress'
    '&status=uploading'
)

RNA_MAPPING_FILES_QUERY = (
    '/search/?type=File'
    '&output_type=alignments'
    '&output_type=transcriptome+alignments'
    '&file_format=bam'
    '&status=released'
    '&status=in+progress'
    '&status=uploading'
    '&award.project=ENCODE'
    '&award.project=Roadmap'
    '&lab.title=ENCODE+Processing+Pipeline'
    '&quality_metrics.assay_term_name=RNA-seq'
    '&quality_metrics.assay_term_name=CRISPR+genome+editing+followed+by+RNA-seq'
    '&quality_metrics.assay_term_name=CRISPRi+followed+by+RNA-seq'
    '&quality_metrics.assay_term_name=direct+RNA-seq'
    '&quality_metrics.assay_term_name=microRNA-seq'
    '&quality_metrics.assay_term_name=shRNA+knockdown+followed+by+RNA-seq'
    '&quality_metrics.assay_term_name=single+cell+isolation+followed+by+RNA-seq'
    '&quality_metrics.assay_term_name=siRNA+knockdown+followed+by+RNA-seq'
    '&quality_metrics.assay_term_name=small+RNA-seq'
    '&frame=embedded'
)

RNA_MAD_QC_FIELDS = [
    '@id',
    'SD of log ratios',
    'Pearson correlation',
    'Spearman correlation',
    'MAD of log ratios',
    'quality_metric_of',
    'attachment'
]

RNA_MQM_REPORT_COLUMNS = [
    'experiment_accession',
    'experiment_status',
    'date',
    'assay_title',
    'lab',
    'rfa',
    'biosample_term_name',
    'biosample_type',
    'assembly',
    'target',
    'attachment',
    'MAD of log ratios',
    'Pearson correlation',
    'SD of log ratios',
    'Spearman correlation',
    'library_insert_size',
    'replication',
    'project',
    'analysis',
    'job_id',
    'quality_metric_of'
]

RNA_MQM_SORT_ORDER = [
    'lab',
    'biosample_term_name',
    'target',
    'experiment_accession'
]

# REPORT TYPE SPECIFICS

REPORT_TYPE_DETAILS = {
    'histone_qc': {
        'experiment_query': HISTONE_CHIP_EXPERIMENTS_QUERY,
        'experiment_fields': EXPERIMENT_FIELDS_QUERY,
        'file_query': HISTONE_PEAK_FILES_QUERY,
        'file_fields': FILE_FIELDS_QUERY,
        'qc_fields': HISTONE_QC_FIELDS,
        'file_no': 1,
        'qc_no': 1,
        'qc_type': ['HistoneChipSeqQualityMetric']
    },
    'rna_qc': {
        'experiment_query': RNA_MQM_EXPERIMENTS_QUERY,
        'experiment_fields': EXPERIMENT_FIELDS_QUERY,
        'file_query': RNA_QUANTIFICATION_FILES_QUERY,
        'file_fields': FILE_FIELDS_QUERY,
        'qc_fields': RNA_MAD_QC_FIELDS,
        'file_no': 2,
        'qc_no': 1,
        'qc_type': ['MadQualityMetric'],
        'col_order': RNA_MQM_REPORT_COLUMNS,
        'sort_order': RNA_MQM_SORT_ORDER
    }
}
