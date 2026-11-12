# HANDOFF: Exhibition Visitor 360 (portfolio)

Upload file ini di chat pertama akun baru dan bilang: "lanjutkan dari sini". Update bagian Status tiap selesai satu tahap.

## Tujuan
Project portfolio buat melamar Data Analyst / Analytics Engineer (contoh loker: Astra International via Lancesoft:
SQL, BigQuery, data quality, ETL, data mapping, dokumentasi teknis, CRM/CDP). Data dummy pameran B2B (fiktif, tanpa sektor tambang).
Portfolio dipublish di kemangdata.my.id (GitHub Pages, repo bfandora97/portfolio).

## Preferensi
Balasan singkat dan langsung, bahasa Indonesia santai. Jangan langkah panjang berlapis, kasih 1 langkah per balasan kalau bisa.

## Project (folder: Desktop\porfolio\exhibition-cdp)
Zip dari chat sebelumnya, isi: src/ (generate_data.py, etl.py, data_quality.py, common.py), sql/ (00_udfs sampai 07_reconciliation,
00_load_raw.sh, schemas/campaign_events.json), docs/, README.md, run.bat, run_all.py.
Kalau zip hilang, minta ulang dengan menjelaskan struktur di atas.
Hasil run (seed 42): DQ score 75.5% -> 99.0%, registrasi 12.934 -> 12.218, 6.000 orang asli -> 6.061 person ID (0% salah gabung).

## Keputusan
- 3 sumber: registrations (CRM), attendance (ERP), campaign_events.jsonl (GA4-style) + edition_summary (laporan resmi)
- Output utama: tabel visitor_360, DQ score before/after, reconciliation per edisi
- Segmen: Loyal (>=3 edisi hadir), Returning (2), New (1), Registered - No Show (0)
- Tools gratis: Python, BigQuery sandbox (tanpa billing, tabel expire ~60 hari), Looker Studio atau Power BI Desktop

## Status
- [x] Pipeline Python jalan di lokal (run.bat), data ada di data/raw dan data/clean
- [x] Project BigQuery `exhibition-cdp` (Sandbox) dan dataset `exhibition_cdp` (location US) sudah dibuat
- [ ] Upload 4 tabel raw lewat BigQuery Console (Create Table > Upload):
  - [ ] raw_registrations (SEDANG DIKERJAKAN: file registrations.csv sudah dipilih, auto detect OFF, header rows to skip = 1, tinggal klik Create table)
  - [ ] raw_attendance
  - [ ] raw_edition_summary
  - [ ] raw_campaign_events
- [ ] Jalankan sql/00_udfs.sql sampai sql/07_reconciliation.sql berurutan, screenshot hasilnya
- [ ] Dashboard (Looker Studio / Power BI) dari visitor_360
- [ ] Push ke GitHub, tulis case study di kemangdata.my.id

## Schema upload (Edit as text, Auto detect OFF, Header rows to skip = 1)
raw_registrations (registrations.csv):
[{"name":"registration_id","type":"STRING"},{"name":"edition_id","type":"STRING"},{"name":"full_name","type":"STRING"},{"name":"email","type":"STRING"},{"name":"phone","type":"STRING"},{"name":"company_name","type":"STRING"},{"name":"job_title","type":"STRING"},{"name":"registered_at","type":"STRING"},{"name":"source","type":"STRING"}]

raw_attendance (attendance.csv):
[{"name":"scan_id","type":"STRING"},{"name":"registration_id","type":"STRING"},{"name":"edition_id","type":"STRING"},{"name":"scan_date","type":"STRING"},{"name":"scan_time","type":"STRING"},{"name":"gate","type":"STRING"}]

raw_edition_summary (edition_summary.csv):
[{"name":"edition_id","type":"STRING"},{"name":"edition_name","type":"STRING"},{"name":"start_date","type":"DATE"},{"name":"days","type":"INTEGER"},{"name":"reported_registered","type":"INTEGER"},{"name":"reported_visitors","type":"INTEGER"}]

raw_campaign_events (campaign_events.jsonl, file format = JSONL): pakai isi file sql/schemas/campaign_events.json
(campaign_events.jsonl sekitar 14 MB, kalau Console menolak upload langsung, lewat Cloud Storage atau bq CLI: sql/00_load_raw.sh).

## Langkah berikutnya
Selesaikan upload 4 tabel raw, lalu jalankan SQL 00 sampai 07. Kalau ada error SQL, kirim pesan errornya.
