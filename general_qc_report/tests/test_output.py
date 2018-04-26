import pytest
import pandas as pd
from datetime import datetime
from output import (
    output_to_tsv,
    output_to_google_sheets,
    apply_formatting_to_dataframe,
    get_formatter,
    set_sheet_id,
    set_column_for_formatting,
    get_template,
    send_dataframe_to_google_sheet,
    get_outputter,
    make_page_title,
    google_connection,
    open_and_clear_sheet
)
from mock import patch


@pytest.fixture
def template():
    return {
        'a': 1,
        'b': 2
    }


@pytest.fixture
def note():
    return {
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


@pytest.fixture
def conditional():
    return {
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


def test_get_outputter():
    assert get_outputter('tsv') is output_to_tsv
    assert get_outputter('google_sheets') is output_to_google_sheets
    with pytest.raises(KeyError):
        get_outputter('blah')


def test_get_template(template):
    new_temp = get_template(template)
    assert new_temp is not template
    assert new_temp == template


def test_make_page_title():
    now = datetime.now().strftime('%m_%d_%Y')
    page_title = make_page_title('histone_qc', 'hg19')
    assert page_title == 'histone_qc_report_hg19_{}'.format(now)


@patch('pygsheets.authorize')
def test_make_google_connection(pyg_mocked):
    gc = google_connection('api_xyz')
    assert pyg_mocked.called

    
