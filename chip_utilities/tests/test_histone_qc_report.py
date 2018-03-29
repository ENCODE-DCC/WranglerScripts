import pytest
from histone_qc_report import (
    HISTONE_QC_FIELDS,
    parse_json,
    make_url,
    HISTONE_PEAK_FILES_QUERY,
    EXPERIMENT_FIELDS_QUERY,
    LIMIT_ALL_JSON
)


@pytest.fixture
def base_url():
    return 'https://www.encodeproject.org'


@pytest.fixture
def histone_qc():
    return {
        "quality_metric_of": [
            "/files/ENCFF482MOP/"
        ],
        "uuid": "be6c1386-eb16-46db-a6fa-57164b5abd11",
        "Ft": 0.681145282904541,
        "@id": "/histone-chipseq-quality-metrics/be6c1386-eb16-46db-a6fa-57164b5abd11/",
        "npeak_overlap": 94053,
        "step_run": "/analysis-step-runs/bbd6e0ed-9081-4874-8f37-3323c6311ec7/",
        "assay_term_name": "ChIP-seq",
        "date_created": "2018-03-27T23:07:30.718507+00:00",
        "award": "/awards/U41HG006992/",
        "lab": "/labs/encode-processing-pipeline/",
        "nreads": 30399406,
        "nreads_in_peaks": 20706412,
        "submitted_by": "/users/6800d05f-7213-48b1-9ad8-254c73c5b83f/",
        "status": "released",
        "assay_term_id": "OBI:0000716"
    }


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
