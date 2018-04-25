import pytest
from mock import patch
from general_qc_report import (
    get_experiments_and_files,
    build_rows_from_experiment,
    build_rows_from_file
)
from constants import (
    REPORT_TYPE_DETAILS
)
import requests


def get_data_indy(url, keypair):
    r = requests.get(url)
    r = r.json()
    return r


@patch('common.encoded_get')
@patch('constants.REPORT_TYPE_DETAILS')
def test_functional_rna_mqm_report_get_data(replaced_details, replaced_get, base_url):
    REPORT_TYPE_DETAILS['rna_qc']['experiment_query'] = REPORT_TYPE_DETAILS['rna_qc']['experiment_query'] + '&accession=ENCSR000AIZ'
    REPORT_TYPE_DETAILS['rna_qc']['file_query'] = REPORT_TYPE_DETAILS['rna_qc']['file_query'] + '&accession=ENCFF513SFV&accession=ENCFF863OEM'
    replaced_details.return_value = REPORT_TYPE_DETAILS
    replaced_get.side_effect = get_data_indy
    exps, files = get_experiments_and_files(base_url, (None, None), 'rna_qc', 'GRCh38')
    assert len(exps) == 1, "wrong number of experiments received"
    assert len(files) == 2, "wrong number of files received"
    rows = build_rows_from_experiment(exps, files, 'rna_qc', base_url)
    assert len(rows) == 1, 'wrong number of rows built'
    assert all([col in rows[0] for col in REPORT_TYPE_DETAILS['rna_qc']['col_order']])
    assert rows[0]['Pearson correlation'] == 0.9737423


@patch('common.encoded_get')
@patch('constants.REPORT_TYPE_DETAILS')
def test_functional_rna_mapping_report_get_data(replaced_details, replaced_get, base_url):
    REPORT_TYPE_DETAILS['rna_mapping']['experiment_query'] = REPORT_TYPE_DETAILS['rna_mapping']['experiment_query'] + '&accession=ENCSR379YAE'
    REPORT_TYPE_DETAILS['rna_mapping']['file_query'] = REPORT_TYPE_DETAILS['rna_mapping']['file_query'] + '&accession=ENCFF475WLJ&accession=ENCFF153PYZ&accession=ENCFF522AQG&accession=ENCFF358IAU'
    replaced_details.return_value = REPORT_TYPE_DETAILS
    replaced_get.side_effect = get_data_indy
    experiments, files = get_experiments_and_files(base_url, (None, None), 'rna_mapping', 'GRCh38')
    assert len(experiments) == 1, 'wrong number of experiments received'
    assert len(files) == 4, 'wrong number of files received'
    rows = build_rows_from_file(experiments, files, 'rna_mapping', base_url)
    assert len(rows) == 4, 'wrong number of rows built'
