# ENCODE ChIP-seq utilities

### Creating formatted mapping and IDR reports in Google Sheets (*must use Python 2*)

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

4. Run mapping and IDR report:

```bash
$ python mapping_report.py --key www --assembly GRCh38 --create_google_sheet
$ python idr_report_experiments.py --all --key www --assembly GRCh38 --create_google_sheet
```

5. Examine results posted to Google Sheets.
