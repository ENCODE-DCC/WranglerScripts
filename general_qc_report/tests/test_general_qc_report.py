import pytest
from constants import (
    HISTONE_QC_FIELDS,
    HISTONE_PEAK_FILES_QUERY,
    EXPERIMENT_FIELDS_QUERY,
    LIMIT_ALL_JSON,
    REPORT_TYPES,
    REPORT_TYPE_DETAILS
)
from general_qc_report import (
    parse_json,
    make_url,
    get_data,
    get_experiments_and_files,
    build_rows_from_experiment,
    build_rows_from_file,
    get_dx_details_from_job_id,
    get_job_id_from_file,
    filter_related_files,
    filter_related_experiments,
    frip_in_output,
    get_row_builder,
    collapse_quality_metrics,
    is_nonoverlapping,
    process_qc,
    build_url_from_accession,
    calculate_read_depth,
    contains_columns,
    add_read_depth,
    resolve_spikein_description
)
from mock import patch


@pytest.mark.parametrize(
    'key, value', [
        ('F1', None),
        ('F2', None),
        ('Fp', None),
        ('Ft', 0.681145282904541),
        ('npeak_overlap', 94053),
        ('nreads', 30399406),
        ('nreads_in_peaks', 20706412),
        ('Ft', 0.681145282904541)
    ]
)
def test_parse_json(key, value, histone_qc):
    parsed_qc = parse_json(histone_qc, HISTONE_QC_FIELDS)
    assert parsed_qc[key] == value


def test_make_url(base_url):
    assert make_url(base_url, HISTONE_PEAK_FILES_QUERY, '') == (
        base_url + HISTONE_PEAK_FILES_QUERY
    )
    assert make_url(base_url, HISTONE_PEAK_FILES_QUERY) == (
        base_url + HISTONE_PEAK_FILES_QUERY + LIMIT_ALL_JSON
    )
    assert make_url(base_url, HISTONE_PEAK_FILES_QUERY, [LIMIT_ALL_JSON]) == (
        base_url + HISTONE_PEAK_FILES_QUERY + LIMIT_ALL_JSON
    )
    assert make_url(base_url, HISTONE_PEAK_FILES_QUERY, [EXPERIMENT_FIELDS_QUERY, LIMIT_ALL_JSON]) == (
        base_url + HISTONE_PEAK_FILES_QUERY + EXPERIMENT_FIELDS_QUERY + LIMIT_ALL_JSON
    )


@patch('common.encoded_get')
def test_get_data(mock_get, base_url, keypair):
    mock_get.return_value = {'@graph': [{'test': 1}]}
    results = get_data(base_url, keypair)
    assert results[0]['test'] == 1


@patch('common.encoded_get')
def test_get_experiments_and_files(mock_get, base_url, keypair, test_args, file_query, experiment_query):
    mock_get.side_effect = [file_query, experiment_query]
    f, e = get_experiments_and_files(
        base_url,
        keypair,
        test_args.report_type,
        test_args.assembly
    )
    assert len(f) == len(e) == 2


@patch('dxpy.describe')
def test_get_dx_details_from_job_id(mock_dx, dx_describe, test_args):
    mock_dx.return_value = dx_describe
    dx_details = get_dx_details_from_job_id('123', skip_dnanexus=False)
    assert dx_details.get('job_id') == '123'
    assert 'frip' in dx_details.get('output')


@patch('dxpy.describe')
def test_get_dx_details_from_job_id_skip_dnanexus(mock_dx, dx_describe):
    mock_dx.return_value = dx_describe
    dx_details = get_dx_details_from_job_id('123', skip_dnanexus=True)
    assert dx_details.get('job_id') == '123'
    assert dx_details.get('output') == {}
    assert dx_details.get('project') is None


def test_get_job_id_from_file(file_query):
    job_id = get_job_id_from_file(file_query['@graph'][0])
    assert job_id == 'job-123'


def test_frip_in_output(dx_describe):
    output = dx_describe.pop('output', None)
    assert frip_in_output(output) is True


def test_filter_related_files(experiment_query, file_query):
    experiment_id = experiment_query['@graph'][0]['@id']
    f = filter_related_files(experiment_id, file_query['@graph'])
    assert len(f) == 1
    assert f[0]['accession'] == 'ENCFF660DGD'


def test_filter_related_experiments(experiment_query, file_query):
    dataset = file_query['@graph'][0]['dataset']
    e = filter_related_experiments(dataset, experiment_query['@graph'])
    assert len(e) == 1
    assert e[0]['@id'] == '/experiments/ENCSR656SIB/'


@patch('dxpy.describe')
def test_build_rows(mock_dx, experiment_query, file_query,
                    references_query, test_args, base_url,
                    dx_describe):
    mock_dx.return_value = dx_describe
    rows = build_rows_from_experiment(
        experiment_query['@graph'],
        file_query['@graph'],
        references_query['@graph'],
        test_args.report_type,
        base_url,
        test_args
    )
    assert len(rows) == 2


@patch('dxpy.describe')
def test_build_rows_missing_file(mock_dx, experiment_query, file_query,
                                 references_query, test_args, base_url,
                                 dx_describe):
    mock_dx.return_value = dx_describe
    rows = build_rows_from_experiment(
        experiment_query['@graph'],
        file_query['@graph'][:1],
        references_query['@graph'],
        test_args.report_type,
        base_url,
        test_args
    )
    assert len(rows) == 1


@patch('dxpy.describe')
def test_build_rows_skip_multiple_qc(mock_dx, experiment_query, file_query,
                                     references_query, histone_qc, test_args,
                                     base_url, dx_describe):
    mock_dx.return_value = dx_describe
    file = file_query['@graph'][0]
    file['quality_metrics'] = [histone_qc, histone_qc]
    rows = build_rows_from_experiment(
        experiment_query['@graph'],
        [file],
        references_query['@graph'],
        test_args.report_type,
        base_url,
        test_args
    )
    assert len(rows) == 0


def test_report_type_constants():
    assert 'histone_qc' in REPORT_TYPES
    assert 'rna_replication' in REPORT_TYPES


def test_row_builder_returns_correct_function():
    assert get_row_builder('rna_replication') is build_rows_from_experiment
    assert get_row_builder('rna_mapping') is build_rows_from_file


def test_row_builder_raises_error():
    with pytest.raises(KeyError):
        get_row_builder('blah')


def test_collapse_quality_metrics():
    assert collapse_quality_metrics([]) == {}
    assert collapse_quality_metrics([{'a': 1}, {'b': 2}]) == {'a': 1, 'b': 2}
    assert collapse_quality_metrics([{'a': 1}, {'a': 2}]) == {'a': 2}


@patch('constants.REPORT_TYPE_DETAILS')
def test_is_nonoverlapping(replaced_details):
    REPORT_TYPE_DETAILS['rna_replication']['qc_fields'] = ['a', 'b', 'c']
    replaced_details.return_value = REPORT_TYPE_DETAILS
    is_nonoverlapping([{'a': 1}, {'b': 2}, {'c': 3}], 'rna_replication')
    with pytest.raises(KeyError):
        is_nonoverlapping({'a': 1}, 'rna_qc')
    with pytest.raises(ValueError):
        is_nonoverlapping([{'a': 1}, {'a': 2}, {'c': 3}], 'rna_replication')


def test_process_qc(base_url):
    qc = process_qc(
        base_url,
        {
            '@id': '/123/',
            'attachment': {
                'href': '@@download/abc'
            }
        },
        'google_sheets'
    )
    qc1 = process_qc(base_url, {}, 'google_sheets')
    assert qc['attachment'] == (
        '=hyperlink("https://www.encodeproject.org//123/@@download/abc",'
        ' image("https://www.encodeproject.org//123/@@download/abc", 2))'
    )
    assert '@id' not in qc
    assert qc1 == {}


def test_build_url_from_accession(base_url):
    accession = 'ENC123'
    url = build_url_from_accession(accession, base_url, 'tsv')
    assert url == base_url + accession
    link = build_url_from_accession(accession, base_url, 'google_sheets')
    assert link == '=hyperlink("https://www.encodeproject.org/ENC123", "ENC123")'


def test_calculate_read_depth():
    import pandas as pd
    assert calculate_read_depth(20, 20) == 40
    assert pd.isnull(calculate_read_depth('', 20))


def test_contains_columns(test_df):
    assert contains_columns(test_df, ['a', 'b'])
    assert not contains_columns(test_df, ['c'])


def test_add_read_depth(test_rna_mapping_df):
    import pandas as pd
    from pandas.util.testing import (
        assert_frame_equal,
    )
    df = add_read_depth(test_rna_mapping_df)
    assert 'read_depth' in df.columns
    assert not assert_frame_equal(test_rna_mapping_df, df)
    assert all(df['read_depth'] == pd.Series([3, 7]))


def test_resolve_spikein_description(references_query):
    row = {
        '@id': '/experiments/ENCSR974RYS/',
        'spikeins_used': ['/references/ENCSR535LMC/']
    }
    references_data = references_query['@graph']
    row = resolve_spikein_description(row, references_data)
    assert row['spikeins_used'] == '/references/ENCSR535LMC/'
    assert row['spikein_description'] == 'profile C1_1 ERCC spike-in concentrations used for C1 fluidigm'
    assert '@id' in row
