# Where the raw file comes from

The CFPB Consumer Complaint Database is published by the US Consumer Financial
Protection Bureau. It is public domain and free to download.

Landing page:
  https://www.consumerfinance.gov/data-research/consumer-complaints/

Full CSV export (about 1.5 GB zipped, larger once unzipped):
  https://files.consumerfinance.gov/ccdb/complaints.csv.zip

Save the unzipped file to this folder as `complaints.csv`.

Downloaded on: ____________
File size on disk: ____________
Row count reported by src/01_profile.py: ____________

The database is refreshed daily, so anyone re-running this repo later will get
a slightly different row count. Record yours above so the figures in the README
can be traced back to a specific download.
