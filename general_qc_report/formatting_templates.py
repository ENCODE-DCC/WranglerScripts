import numpy as np

colors = np.array([[252, 1, 1],
                   [253, 154, 0],
                   [246, 205, 206],
                   [220, 220, 220],
                   [205, 216, 244],
                   [253, 231, 181],
                   [255, 255, 255],
                   [183, 225, 205],
                   [243, 200, 194]]) / 255.0


red = colors[0]
orange = colors[1]
pink = colors[2]
gray = colors[3]
blue = colors[4]
yellow = colors[5]
white = colors[6]
green = colors[7]
red2 = colors[8]


header = {
    "repeatCell": {
        "range": {
            "startRowIndex": 0,
            "endRowIndex": 1,
        },
        "cell": {
            "userEnteredFormat": {
                "textFormat": {
                    "fontSize": 9,
                    "bold": True
                }
            }
        },
        "fields": "userEnteredFormat(textFormat)"
    }
}

freeze_header = {
    "updateSheetProperties": {
        "properties": {
            "gridProperties": {"frozenRowCount": 1}
        },
        "fields": "gridProperties(frozenRowCount)"
    }
}

font_size_format = {
    "repeatCell": {
        "range": {
            "startRowIndex": 1,
            "startColumnIndex": 0
        },
        "cell": {
            "userEnteredFormat": {
                "textFormat": {
                    "fontSize": 9,
                }
            }
        },
        "fields": "userEnteredFormat(textFormat)"
    }
}

note = {
    "repeatCell": {
        "range": {
            "startRowIndex": 0,
            "endRowIndex": 1,
        },
        "cell": {
            "note": ""
        },
        "fields": "note"
    }
}

number_cols = {
    'three_decimal_cols': {'pattern': '0.000', 'cols': []},
    'two_decimal_cols': {'pattern': '0.00', 'cols': []},
    'million_cols': {'pattern': '0.0,,"M"', 'cols': []}
}

number_format = {
    "repeatCell": {
        "range": {
            "startRowIndex": 1
        },
        "cell": {
            "userEnteredFormat": {
                "numberFormat": {
                    "type": "NUMBER",
                    "pattern": "0.00"
                }

            }
        },
        "fields": "userEnteredFormat.numberFormat"
    }
}

font_size_format = {
    "repeatCell": {
        "range": {
            "startRowIndex": 1,
            "startColumnIndex": 0
        },
        "cell": {
            "userEnteredFormat": {
                "textFormat": {
                    "fontSize": 9,
                }
            }
        },
        "fields": "userEnteredFormat(textFormat)"
    }
}

condition_dict = {
    "addConditionalFormatRule": {
        "rule": {
            "ranges": [
                {
                    "startRowIndex": 1,
                }
            ],
            "booleanRule": {
                "condition": {
                    "type": "",
                    "values": []
                },
                "format": {
                    "backgroundColor": {
                        "red": "",
                        "green": "",
                        "blue": ""
                    },
                }
            }
        }, "index": 0
    }
}

tf_idr_notes_dict = {
    'Nt': 'Nt = number of peaks that pass IDR comparing peaks called on reads from each true (biological) replicate',
    'Np': 'Np = the number of peaks that pass IDR when comparing peaks called on psedoreplicates of the reads pooled from both true replicates',
    'N1': 'N1 = the number of peaks that pass IDR comparing pseudoreplicates of rep 1',
    'N2': 'N2 = the number of peaks that pass IDR comparing pseudoreplicates of rep 2',
    'rescue_ratio': 'rescue_ratio = (max(Np,Nt)) / (min(Np,Nt)) Estimates replicate similarity by comparing how similar the peak lists are from treating replicates separately vs. pooling them',
    'self_consistency_ratio': 'self_consistency_ratio = (max(N1,N2)) / (min(N1,N2)) Estimates replicate similarity by comparing how similar the peak lists are from pseudoreplication of each true replicate',
    'reproducibility_test': 'reproducibility_test Pass if both rescue and self_consistency ratios are < 2. Borderline if one is > 2. Fail if both are > 2.',
    'Ft': 'Ft = FRiP score based on peaks that pass IDR comparing peaks called on reads from each true (biological) replicate',
    'Fp': 'Fp = FRiP score based on peaks that pass IDR when comparing peaks called on psedoreplicates of the reads pooled from both true replicates',
    'F1': 'F1 = FRiP score based on peaks that pass IDR comparing pseudoreplicates of rep 1',
    'F2': 'F2 = FRiP score based on peaks that pass IDR comparing pseudoreplicates of rep 2'
}

tf_mapping_notes_dict = {
    'bam': 'Accession of the bam file after mapping. "no fastqs" -> no fastqs have been submitted. "pending" -> fastqs have been submitted but mapping has not been done pending metadata review.',
    'hiq_reads': 'Number of reads input to the mapping pipeline.',
    'mappable': 'Number of reads mapping to a unique genomic location.',
    'r_lengths': '<30 Red, <50 Orange (ENCODE3 standard), Mixed read lengths Yellow.',
    'map_length': '<30 Red, <50 Orange (ENCODE3 standard), Blank means bam has no mapped_read_length property, assumed to be native length of the fastqs.',
    'usable_frags': 'Number of non-duplicated reads surviving the filter. ENCODE2: >10M for narrow marks, >20M for broad. ENCODE3: should be >20M-25M for narrow marks, >45M-50M for broad marks.',
    'NRF': 'Non redundant fraction (indicates library complexity). 0.0-0.7 very poor, 0.7-0.8 poor, 0.8-0.9 moderate, >0.9 high. Number of distinct unique mapping reads (i.e. after removing duplicates) / Total number of reads.',
    'PBC1': 'PCR Bottlenecking coefficient 1 (indicates library complexity). 0 - 0.5 (red): severe, 0.5 - 0.8 (orange): moderate, 0.8 - 0.9 (pink): mild, > 0.9: no bottlenecking. = M1/M_DISTINCT, M1: number of genomic locations where exactly one read maps uniquely, M_DISTINCT: number of distinct genomic locations to which some read maps uniquely.',
    'PBC2': 'PCR Bottlenecking coefficient 2 (indicates library complexity). 0 - 1 (red): severe, 1 - 3 (orange): moderate, 3 -10 (pink): mild, > 10 : no bottlenecking. = M1/M2, M1: number of genomic locations where only one read maps uniquely, M2: number of genomic locations where 2 reads map uniquely.',
    'frag_len': 'Fragment length/strandshift. This is the estimated fragment length/strand shift for each dataset as estimated by strand cross-correlation analysis.',
    'NSC': 'Normalized strand cross-correlation (A data quality measure). FRAGLEN_CC / MIN_CC. Ratio of strand cross-correlation at estimated fragment length to the minimum cross-correlation over all shifts. Values are always >1. NSC < 1.05 is flagged as potential low signal-to-noise. Could be due to: low enrichment, few number of peaks due to biology of factor, broad chromatin mark. orange: < 1.02 (very low), pink: 1.02 < NSC < 1.05 (low), grey: 1.05 < NSC < 1.1 (moderate), >= 1.1 (high).',
    'RSC': 'Relative cross correlation coefficient. Ratio of strand cross-correlation at fragment length and at read length. Enriched datasets should have values > 1 or very close to 1 (> 0.8).'
}


note = {
    "repeatCell": {
        "range": {
            "startRowIndex": 0,
            "endRowIndex": 1,
        },
        "cell": {
            "note": ""
        },
        "fields": "note"
    }
}


RNA_MAPPING_FORMATTING = {
    'header': {'template': header},
    'freeze_header': {'template': freeze_header},
    'note': {},
    'font': {'template': font_size_format},
    'number': {
        'template': number_format,
        'numeric_cols_pattern': [
            ('read_depth', '0.0,,"M"'),
            ('num_reads_mapped_passing_qc', '0.0,,"M"'),
            ('num_of_total_reads_passing_qc', '0.0,,"M"'),
            ('num_of_total_reads_failing_qc', '0.0,,"M"'),
            ('num_of_paired_reads_passing_qc', '0.0,,"M"'),
            ('num_reads_properly_paired_passing_qc', '0.0,,"M"'),
            ('num_reads_mapped_failing_qc', '0.0,,"M"'),
            ('num_of_properly_paired_reads_failing_qc', '0.0,,"M"'),
            ('star_number_of_input_reads', '0.0,,"M"'),
            ('star_uniquely_mapped_reads_number', '0.0,,"M"'),
            ('star_number_of_reads_mapped_to_multiple_loci', '0.0,,"M"')
        ]
    },
    'conditional': {
        'template': condition_dict,
        'conditions': {
            'read_depth': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
            'num_reads_mapped_passing_qc': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
             'num_of_total_reads_passing_qc': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
            'num_of_paired_reads_passing_qc': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
            'num_reads_properly_paired_passing_qc': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
            'star_number_of_input_reads': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
            'star_uniquely_mapped_reads_number': [
                ('NUMBER_LESS', ['20000000'], pink),
                ('NUMBER_BETWEEN', ['20000000', '30000000'], orange),
                ('NUMBER_GREATER', ['30000000'], green)
            ],
            'read_length': [
                ('NUMBER_LESS', ['50'], pink),
                ('TEXT_CONTAINS', [','], yellow)
            ],
            'replication': [
                ('TEXT_CONTAINS', ['unreplicated'], pink)
            ]
        }
    },
    'additional': {}
}
