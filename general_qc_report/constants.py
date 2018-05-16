'''
module containing constants used by qc reporting tools
'''

from formatting_templates import (
    RNA_MAPPING_FORMATTING,
    RNA_QC_FORMATTING
)

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
    '&field=replicates.library.strand_specificity'
    '&field=replicates.library.depleted_in_term_name'
    '&field=replicates.library.spikeins_used'
    '&field=files.read_length'
    '&field=files.run_type'
    '&field=assay_title'
)

FILE_FIELDS_QUERY = (
    '&field=@id'
    '&field=accession'
    '&field=output_type'
    '&field=date_created'
    '&field=status'
    '&field=dataset'
    '&field=assembly'
    '&field=step_run'
    '&field=quality_metrics'
    '&field=notes'
    '&field=biological_replicates'
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
    'nreads',
    'nreads_in_peaks',
    'npeak_overlap',
    'Fp',
    'Ft',
    'F1',
    'F2',
    'quality_metric_of'
]

# RNA GENERIC

RNA_EXPERIMENTS_QUERY = (
    '/search/?type=Experiment'
    '&award.project=ENCODE'
    '&award.project=Roadmap'
    '&assay_slims=Transcription'
    '&assay_title=polyA+RNA-seq'
    '&assay_title=total+RNA-seq'
    '&assay_title=small+RNA-seq'
    '&assay_title=single+cell+RNA-seq'
    '&assay_title=microRNA-seq'
    '&assay_title=CRISPRi+RNA-seq'
    '&assay_title=CRISPR+RNA-seq'
    '&assay_title=polyA+depleted+RNA-seq'
    '&assay_title=shRNA+RNA-seq'
    '&assay_title=siRNA+RNA-seq'
    '&status=released'
    '&status=in+progress'
    '&status=submitted'
)

# RNA MQM SPECIFIC

RNA_MQM_EXPERIMENTS_QUERY = (
    RNA_EXPERIMENTS_QUERY + '&replication_type!=unreplicated'
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
    'assay_title',
    'lab',
    'rfa',
    'biosample_term_name',
    'biosample_type',
    'library_insert_size',
    'replication',
    'assembly',
    'target',
    'Pearson correlation',
    'SD of log ratios',
    'Spearman correlation',
    'MAD of log ratios',
    'attachment',
    'project',
    'analysis',
    'job_id',
    'quality_metric_of',
    'analysis_date'
]

RNA_MQM_SORT_ORDER = [
    'lab',
    'assay_title',
    'biosample_term_name',
    'target'
]

# RNA MAPPING SPECIFIC

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
)

# https://github.com/ENCODE-DCC/encoded/blob/dev/src/encoded/schemas/samtools_flagstats_quality_metric.json
RNA_FLAGSTATS_FIELDS = [
    'diff_chroms',
    'diff_chroms_qc_failed',
    'duplicates',
    'duplicates_qc_failed',
    'mapped',
    'mapped_pct',
    'mapped_qc_failed',
    'paired',
    'paired_properly',
    'paired_properly_pct',
    'paired_properly_qc_failed',
    'paired_qc_failed',
    'read1',
    'read1_qc_failed',
    'read2',
    'read2_qc_failed',
    'singletons',
    'singletons_pct',
    'singletons_qc_failed',
    'total',
    'total_qc_failed',
    'with_itself',
    'with_itself_qc_failed'
]

RNA_STAR_QM_FIELDS = [
    '% of reads mapped to multiple loci',
    '% of reads mapped to too many loci',
    '% of reads unmapped: other',
    '% of reads unmapped: too many mismatches',
    '% of reads unmapped: too short',
    'Average input read length',
    'Average mapped length',
    'Deletion average length',
    'Deletion rate per base',
    'Insertion average length',
    'Insertion rate per base',
    'Mapping speed, Million of reads per hour',
    'Mismatch rate per base, %',
    'Number of input reads',
    'Number of reads mapped to multiple loci',
    'Number of reads mapped to too many loci',
    'Number of splices: AT/AC',
    'Number of splices: Annotated (sjdb)',
    'Number of splices: GC/AG',
    'Number of splices: GT/AG',
    'Number of splices: Non-canonical',
    'Number of splices: Total',
    'Uniquely mapped reads %',
    'Uniquely mapped reads number'
]

RNA_MAPPING_FINAL_COLUMN_NAMES_MAPPING = {
    'diff_chroms': 'num_reads_with_mate_mapped_to_diff_chr_passing_qc',
    'diff_chroms_qc_failed': 'num_reads_with_mate_mapped_to_diff_chr_failing_qc',
    'duplicates': 'num_reads_with_duplicates_passing_qc',
    'duplicates_qc_failed': 'num_reads_with_duplicates_failing_qc',
    'mapped': 'num_reads_mapped_passing_qc',
    'mapped_pct': 'pct_reads_mapped_passing_qc',
    'mapped_qc_failed': 'num_reads_mapped_failing_qc',
    'paired': 'num_of_paired_reads_passing_qc',
    'paired_properly': 'num_reads_properly_paired_passing_qc',
    'paired_properly_pct': 'pct_of_properly_paired_reads_passing_qc',
    'paired_properly_qc_failed': 'num_of_properly_paired_reads_failing_qc',
    'paired_qc_failed': 'num_of_paired_reads_failing_qc',
    'read1': 'num_of_read1_reads_passing_qc',
    'read1_qc_failed': 'num_of_read1_reads_failing_qc',
    'read2': 'num_of_read2_reads_passing_qc',
    'read2_qc_failed': 'num_of_read2_reads_failing_qc',
    'singletons': 'num_of_singletons_passing_qc',
    'singletons_pct': 'pct_of_singletons_passing_qc',
    'singletons_qc_failed': 'num_of_singletons_failing_qc',
    'total': 'num_of_total_reads_passing_qc',
    'total_qc_failed': 'num_of_total_reads_failing_qc',
    'with_itself': 'num_of_reads_with_itself_and_mate_mapped_passing_qc',
    'with_itself_qc_failed': 'num_of_reads_with_itself_and_mate_mapped_failing_qc',
    '% of reads mapped to multiple loci': 'star_pct_of_reads_mapped_to_multiple_loci',
    '% of reads mapped to too many loci': 'star_pct_of_reads_mapped_to_too_many_loci',
    '% of reads unmapped: other': 'star_pct_of_reads_unmapped_other',
    '% of reads unmapped: too many mismatches': 'star_pct_of_reads_unmapped_too_many_mismatches',
    '% of reads unmapped: too short': 'star_pct_of_reads_unmapped_too_short',
    'Average input read length': 'star_average_input_read_length',
    'Average mapped length': 'star_average_mapped_length',
    'Deletion average length': 'star_deletion_average_length',
    'Deletion rate per base': 'star_deletion_rate_per_base',
    'Insertion average length': 'star_insertion_average_length',
    'Insertion rate per base': 'star_insertion_rate_per_base',
    'Mapping speed, Million of reads per hour': 'star_mapping_speed_million_of_reads_per_hour',
    'Mismatch rate per base, %': 'star_mismatch_rate_per_base_pct',
    'Number of input reads': 'star_number_of_input_reads',
    'Number of reads mapped to multiple loci': 'star_number_of_reads_mapped_to_multiple_loci',
    'Number of reads mapped to too many loci': 'star_number_of_reads_mapped_to_too_many_loci',
    'Number of splices: AT/AC': 'star_number_of_splices_AT_AC',
    'Number of splices: Annotated (sjdb)': 'star_number_of_splices_annotated_sjdb',
    'Number of splices: GC/AG': 'star_number_of_splices_GC_AG',
    'Number of splices: GT/AG': 'star_number_of_splices_GT_AG',
    'Number of splices: Non-canonical': 'star_number_of_splices_non_canonical',
    'Number of splices: Total': 'star_number_of_splices_total',
    'Uniquely mapped reads %': 'star_uniquely_mapped_reads_pct',
    'Uniquely mapped reads number': 'star_uniquely_mapped_reads_number'
}

RNA_MAPPING_SORT_ORDER = [
    'lab',
    'assay_title',
    'biosample_term_name',
    'target',
    'experiment_accession',
    'biological_replicates',
    'output_type'
]

RNA_MAPPING_COLUMN_ORDER = [
    'experiment_accession',
    'assay_title',
    'library_insert_size',
    'biosample_type',
    'biosample_term_name',
    'target',
    'replication',
    'lab',
    'rfa',
    'experiment_status',
    'assembly',
    'file_accession',
    'biological_replicates',
    'spikeins_used',
    'spikein_description',
    'output_type',
    'read_length',
    'run_type',
    'strand_specificity',
    'depleted_in_term_name',
    'read_depth',
    'num_reads_mapped_passing_qc',
    'pct_reads_mapped_passing_qc',
    'num_of_total_reads_passing_qc',
    'num_of_total_reads_failing_qc',
    'num_of_paired_reads_passing_qc',
    'num_reads_properly_paired_passing_qc',
    'pct_of_properly_paired_reads_passing_qc',
    'num_reads_mapped_failing_qc',
    'num_of_properly_paired_reads_failing_qc',
    'star_number_of_input_reads',
    'star_uniquely_mapped_reads_number',
    'star_uniquely_mapped_reads_pct',
    'star_average_input_read_length',
    'star_average_mapped_length',
    'star_number_of_reads_mapped_to_multiple_loci',
    'star_pct_of_reads_mapped_to_multiple_loci',
    'star_pct_of_reads_unmapped_too_short',
    'analysis',
    'analysis_date',
    ]

# REFERENCES SPECIFIC

REFERENCES_FILESET_QUERY = '/search/?type=Reference'

REFERENCES_FIELDS_QUERY = (
    '&field=@id'
    '&field=description'
)

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
        'qc_type': ['HistoneChipSeqQualityMetric'],
        'row_builder': 'from_experiment'
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
        'sort_order': RNA_MQM_SORT_ORDER,
        'row_builder': 'from_experiment',
        'formatting': RNA_QC_FORMATTING
    },
    'rna_mapping': {
        'experiment_query': RNA_EXPERIMENTS_QUERY,
        'experiment_fields': EXPERIMENT_FIELDS_QUERY,
        'file_query': RNA_MAPPING_FILES_QUERY,
        'file_fields': FILE_FIELDS_QUERY,
        'qc_fields': [RNA_FLAGSTATS_FIELDS, RNA_STAR_QM_FIELDS],
        'qc_no_max': 2,
        'qc_no_min': 1,
        'qc_type': ['SamtoolsFlagstatsQualityMetric', 'StarQualityMetric'],
        'row_builder': 'from_file',
        'sort_order': RNA_MAPPING_SORT_ORDER,
        'rename_columns': RNA_MAPPING_FINAL_COLUMN_NAMES_MAPPING,
        'formatting': RNA_MAPPING_FORMATTING,
        'col_order': RNA_MAPPING_COLUMN_ORDER,
        'get_references': True,
        'references_query': REFERENCES_FILESET_QUERY,
        'references_fields': REFERENCES_FIELDS_QUERY
    }
}
