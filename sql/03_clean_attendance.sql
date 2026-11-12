-- Scan badge: normalisasi ID, petakan ke person_id, tandai scan ganda & scan tanpa registrasi.
CREATE OR REPLACE TABLE exhibition_cdp.stg_attendance AS
WITH a AS (
  SELECT scan_id,
         UPPER(TRIM(registration_id)) AS registration_id_clean,
         edition_id,
         SAFE_CAST(scan_date AS DATE) AS scan_date,
         scan_time,
         gate
  FROM exhibition_cdp.raw_attendance
)
SELECT
  a.*,
  m.person_id,
  m.person_id IS NOT NULL AS is_matched,
  ROW_NUMBER() OVER (PARTITION BY a.registration_id_clean, a.scan_date, a.gate ORDER BY a.scan_time, a.scan_id) > 1
    AS is_duplicate_scan
FROM a
LEFT JOIN exhibition_cdp.stg_registrations m ON a.registration_id_clean = m.registration_id;

-- 1 baris = 1 orang hadir di 1 hari pada 1 edisi
CREATE OR REPLACE TABLE exhibition_cdp.clean_attendance_daily AS
SELECT DISTINCT person_id, edition_id, scan_date
FROM exhibition_cdp.stg_attendance
WHERE is_matched AND NOT is_duplicate_scan;
