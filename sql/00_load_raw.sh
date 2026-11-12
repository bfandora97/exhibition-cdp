#!/usr/bin/env bash
# Load data mentah ke BigQuery. Jalankan dari root project. Butuh Google Cloud SDK (perintah `bq`).
# Alternatif tanpa CLI: upload lewat BigQuery Console, SET SEMUA KOLOM CSV JADI STRING
# (kalau autodetect, phone bisa jadi angka dan nol di depan hilang).
set -e
bq --location=US mk --dataset --force exhibition_cdp 2>/dev/null || true

bq load --replace --source_format=CSV --skip_leading_rows=1 --allow_quoted_newlines \
  exhibition_cdp.raw_registrations data/raw/registrations.csv \
  registration_id:STRING,edition_id:STRING,full_name:STRING,email:STRING,phone:STRING,company_name:STRING,job_title:STRING,registered_at:STRING,source:STRING

bq load --replace --source_format=CSV --skip_leading_rows=1 \
  exhibition_cdp.raw_attendance data/raw/attendance.csv \
  scan_id:STRING,registration_id:STRING,edition_id:STRING,scan_date:STRING,scan_time:STRING,gate:STRING

bq load --replace --source_format=CSV --skip_leading_rows=1 \
  exhibition_cdp.raw_edition_summary data/raw/edition_summary.csv \
  edition_id:STRING,edition_name:STRING,start_date:DATE,days:INT64,reported_registered:INT64,reported_visitors:INT64

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  exhibition_cdp.raw_campaign_events data/raw/campaign_events.jsonl sql/schemas/campaign_events.json
