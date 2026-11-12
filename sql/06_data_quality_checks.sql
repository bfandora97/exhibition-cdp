-- Cek kualitas data: jalankan per blok, simpan hasilnya sebagai screenshot untuk portfolio.

-- 1) Registrasi ganda (sebelum vs sesudah dedup)
SELECT
  (SELECT COUNT(*) FROM exhibition_cdp.raw_registrations) AS raw_rows,
  (SELECT COUNT(*) FROM exhibition_cdp.clean_registrations) AS clean_rows,
  (SELECT COUNT(DISTINCT person_id) FROM exhibition_cdp.clean_registrations) AS unique_persons;

-- 2) Email: siapa yang berubah setelah cleaning
SELECT
  COUNTIF(NULLIF(TRIM(email), '') IS NULL) AS email_blank_raw,
  COUNTIF(exhibition_cdp.clean_email(email) IS NULL AND NULLIF(TRIM(email), '') IS NOT NULL) AS email_invalid,
  COUNTIF(exhibition_cdp.clean_email(email) IS NOT NULL AND LOWER(TRIM(email)) != exhibition_cdp.clean_email(email))
    AS email_fixed_or_normalized
FROM exhibition_cdp.raw_registrations;

-- 3) Scan badge yang tidak bisa dipetakan ke registrasi (orphan)
SELECT COUNTIF(NOT is_matched) AS orphan_scans, COUNT(*) AS total_scans,
       ROUND(SAFE_DIVIDE(COUNTIF(NOT is_matched), COUNT(*)), 4) AS orphan_rate
FROM exhibition_cdp.stg_attendance;

-- 4) Event campaign yang tidak ketemu orangnya
SELECT COUNTIF(NOT is_matched) AS unmatched_events, COUNT(*) AS total_events
FROM exhibition_cdp.stg_campaign_events;

-- 5) Sanity: tidak boleh ada duplikat (edition_id, person_id) di tabel clean (hasil harus 0 baris)
SELECT edition_id, person_id, COUNT(*) AS n
FROM exhibition_cdp.clean_registrations
GROUP BY edition_id, person_id
HAVING COUNT(*) > 1;
