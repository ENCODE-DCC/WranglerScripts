# ENCODE general QC report

### Creating formatted reports in Google Sheets (*must use Python 2*)

1. Install dependencies:
```bash
pip install pygsheets
pip install pandas
```

2. Ask for ENCODE account credentials and client_secret file (client_secret_xxxx.json) allowing scripts to use Google API.

3. Authorize scripts to access Google Drive/Sheets for particular account:

```python
import pygsheets

gc = pygsheets.authorize(outh_file='client_secret_xxxx.json')

# Follow OAuth procedure.
```

Drop resulting sheets.googleapis.com-python.json in home folder (or specify path with --apikey argument).

4. Run reporting tool example command:

```bash
$ python general_qc_report.py --key prod --assembly GRCh38 --report_type rna_qc --sheet_title ENCODE_QC -o google_sheets -s
```

Options:

| command  | description |
| ------------- | ------------- |
| `-h, --help` | Show help message  |
| `-d, --debug`  | Print debug messages  |
| `--key KEY` | The keypair identifier from the keyfile  |
| `--keyfile KEYFILE`  | The keyfile  |
| `--assembly` `{GRCh38, hg19 , mm10}` | Genome assembly  |
| `-r, --report_type` `{histone_qc, histone_mapping, tf_mapping, tf_qc, rna_mapping, rna_qc}`  | Report type  |
| `--sheet_title SHEET_TITLE` | Name of Google Sheet  |
| `--api_key API_KEY`  | Path to secret credential for Google Sheets  |
| `-o, --output_type` `{tsv,google_sheets}`  | Output to TSV or Google Sheets (requires authentication)  |
| `-s, --skip_dnanexus` | Skip requests from DNAnexus (much faster) |

5. Examine results posted to Google Sheets.
