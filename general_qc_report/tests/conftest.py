import pytest

@pytest.fixture
def base_url():
    return 'https://www.encodeproject.org/'


@pytest.fixture
def assembly():
    return 'GRCh38'


@pytest.fixture
def keypair():
    return ('ABC', '123')


@pytest.fixture
def histone_qc():
    return {
        "@type": [
            "HistoneChipSeqQualityMetric",
            "QualityMetric",
            "Item"
        ],
        "quality_metric_of": [
            "/files/ENCFF660DGD/"
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


@pytest.fixture
def file_query():
    return {
        "@graph": [
            {
                "@id": "/files/ENCFF660DGD/",
                "@type": [
                    "File",
                    "Item"
                ],
                "notes": '{"dx-createdBy": {"job": "job-FBZp3z80369GYzY2Jz7FX8Qq", "executable": "applet-F9YvJzj0369JPFjp7zFkkvXg", "user": "user-mkajco"}, "qc": {"npeaks_in": 131917, "npeaks_rejected": 38043, "npeaks_out": 93874}, "dx-parentAnalysis": "analysis-FBZp3z80369GYzY2Jz7FX8Qg", "dx-id": "file-FBZy98j0bY1G7j3xFJ0pGJ2F"}',
                "quality_metrics": [
                     {
                         "@type": [
                             "HistoneChipSeqQualityMetric",
                             "QualityMetric",
                             "Item"
                         ],
                         "quality_metric_of": [
                             "/files/ENCFF660DGD/"
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
                ],
                "assembly": "GRCh38",
                "status": "released",
                "dataset": "/experiments/ENCSR656SIB/",
                "accession": "ENCFF660DGD",
                "step_run": {
                    "schema_version": "4",
                    "@id": "/analysis-step-runs/8936804d-d3b8-4207-a40b-c207bed96ae4/",
                    "dx_applet_details": [{'dx_job_id': 'dnanexus:job-123'}],
                    "date_created": "2018-03-15T03:29:17.649046+00:00",
                    "status": "released",
                    "@type": [],
                    "analysis_step_version": "/analysis-step-versions/histone-overlap-peaks-step-v-1-1/",
                    "submitted_by": "/users/85978cd9-131e-48e2-a389-f752ab05b0a6/",
                    "uuid": "8936804d-d3b8-4207-a40b-c207bed96ae4",
                    "aliases": [
                        "dnanexus:job-FBZp3z80369GYzY2Jz7FX8Qq"
                    ]
                }
            },
            {
                "@id": "/files/ENCFF111DMJ/",
                "@type": [
                    "File",
                    "Item"
                ],
                "notes": '{"dx-createdBy": {"job": "job-FBB6BKQ03699JBZqGQFVb3JZ", "executable": "applet-F9YvJzj0369JPFjp7zFkkvXg", "user": "user-keenangraham"}, "qc": {"npeaks_in": 185535, "npeaks_rejected": 36732, "npeaks_out": 148803}, "dx-parentAnalysis": "analysis-FBB6BKQ03699JBZqGQFVb3JQ", "dx-id": "file-FBB8GK001838fKvY2qK8K5q6"}',
                "quality_metrics": [ ],
                "assembly": "GRCh38",
                "status": "released",
                "dataset": "/experiments/ENCSR486GER/",
                "accession": "ENCFF111DMJ",
                "step_run": {
                    "schema_version": "4",
                    "@id": "/analysis-step-runs/8a136540-234d-4a87-b481-8c238bd559a5/",
                    "dx_applet_details": [{'dx_job_id': 'dnanexus:job-321'}],
                    "aliases": [],
                    "analysis_step_version": "/analysis-step-versions/histone-unreplicated-partition-concordance-step-v-1-0/",
                    "status": "released",
                    "@type": [],
                    "date_created": "2018-03-01T20:03:52.764975+00:00",
                    "uuid": "8a136540-234d-4a87-b481-8c238bd559a5",
                    "submitted_by": "/users/7e95dcd6-9c35-4082-9c53-09d14c5752be/"
                }
            }
        ]
    }


@pytest.fixture
def experiment_query():
    return {
        "@graph": [
            {
                "biosample_term_name": "HepG2",
                "accession": "ENCSR656SIB",
                "replication_type": "isogenic",
                "@id": "/experiments/ENCSR656SIB/",
                "award": {
                    "rfa": "ENCODE3"
                },
                "status": "released",
                "target": {
                    "name": "FLAG-ZBED5-human"
                },
                "@type": [
                    "Experiment",
                    "Dataset",
                    "Item"
                ],
                "lab": {
                    "name": "richard-myers"
                },
                "biosample_type": "cell line"
            },
            {
                "biosample_term_name": "Parathyroid adenoma",
                "accession": "ENCSR486GER",
                "replication_type": "unreplicated",
                "@id": "/experiments/ENCSR486GER/",
                "award": {
                    "rfa": "ENCODE3"
                },
                "status": "released",
                "target": {
                    "name": "H3K4me1-human"
                },
                "@type": [
                    "Experiment",
                    "Dataset",
                    "Item"
                ],
                "lab": {
                    "name": "bradley-bernstein"
                },
                "biosample_type": "tissue"
            }
        ]
    }


@pytest.fixture
def dx_describe():
    return {
        'analysis': 'analysis-123456',
        'project': 'project-123',
        'output': {'frip': 123}
    }


@pytest.fixture
def test_args():
    import argparse
    args = argparse.Namespace()
    args.__dict__.update({
        'assembly': 'GRCh38',
        'report_type': 'histone_qc',
        'output_type': 'google_sheets'
    })
    return args
