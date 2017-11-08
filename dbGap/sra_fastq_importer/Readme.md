# SRA FASTQ Importer
SRA FASTQ Importer retrieves reads in FASTQ or FASTA format from SRA, using the NCBI SRA toolkit and running the 'fastq-dump' command.

## What does this app do?
This app runs SRA toolkit's fastq-dump using an SRA accession number. Optionally, the user may select to additionally run prefetch and vdb-validate before fastq-dump.
The user may select from standard options for how the files should be output, including whether or not files should be gzipped, whether files should be in FASTA or FASTQ format, etc. Advanced options allow users to provide command line arguments for fastq-dump directly, e.g. -X 5 to retrieve max 5 reads.

See fastq-dump manual for more details:
https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?view=toolkit_doc&f=fastq-dump

## What are typical use cases for this app?
Retrieve an entire run from SRA in FASTQ format for downstream analysis, or download a few reads for testing purposes.

## What data are required for this app to run?
This app takes as input an SRR accession number per run.
If you only have a SRP accession, you can retrieve the SRR accessions from SRA Entrez, by visiting:
https://www.ncbi.nlm.nih.gov/sra/

After searching the SRP accession, click on "Send to" in the upper-right corner, then select "Run Selector" and click "Go".
The Run Selector page will appear for the given experiment. You can find the SRR accession number on the left-hand side of each run.

## What does this app output?
The main output is one or two paired FASTQ files. The user can optionally specify whether these files should be split into pairs, should be gzipped, or should be output in FASTA instead of FASTQ format.

<!--
For more info, see https://wiki.dnanexus.com/Developer-Portal.
-->
