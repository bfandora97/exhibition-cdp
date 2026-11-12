-- Cleaning registrasi + identity resolution sederhana (BigQuery).
-- Hierarki kunci orang: email valid -> (phone yang pernah dipasangkan dengan email) -> phone -> nama|perusahaan
-- Catatan: versi Python (src/etl.py) memakai union-find sehingga bisa menggabungkan lebih banyak kasus.
CREATE OR REPLACE TABLE exhibition_cdp.stg_registrations AS
WITH base AS (
  SELECT
    UPPER(TRIM(registration_id)) AS registration_id,
    edition_id,
    INITCAP(REGEXP_REPLACE(TRIM(full_name), r'\s+', ' ')) AS name_clean,
    exhibition_cdp.clean_email(email) AS email_clean,
    exhibition_cdp.clean_phone(phone) AS phone_clean,
    NULLIF(REGEXP_REPLACE(TRIM(company_name), r'\s+', ' '), '') AS company_ws,
    exhibition_cdp.company_key(company_name) AS company_key,
    NULLIF(REGEXP_REPLACE(TRIM(job_title), r'\s+', ' '), '') AS job_title,
    SAFE_CAST(registered_at AS TIMESTAMP) AS registered_at,
    source
  FROM exhibition_cdp.raw_registrations
),
canon AS (  -- nama perusahaan kanonik = modus per company_key
  SELECT company_key, company_ws AS company_canonical
  FROM (
    SELECT company_key, company_ws,
           ROW_NUMBER() OVER (PARTITION BY company_key ORDER BY n DESC, company_ws) AS rn
    FROM (
      SELECT company_key, company_ws, COUNT(*) AS n
      FROM base
      WHERE company_key != '' AND company_ws IS NOT NULL
      GROUP BY company_key, company_ws
    )
  )
  WHERE rn = 1
),
phone_map AS (  -- phone yang pernah muncul bersama email -> pakai email itu untuk baris yang emailnya kosong
  SELECT phone_clean, MIN(email_clean) AS email_via_phone
  FROM base
  WHERE phone_clean IS NOT NULL AND email_clean IS NOT NULL
  GROUP BY phone_clean
),
keyed AS (
  SELECT
    b.*, c.company_canonical,
    COALESCE(b.email_clean, p.email_via_phone, b.phone_clean,
             CONCAT(LOWER(b.name_clean), '|', b.company_key)) AS person_key
  FROM base b
  LEFT JOIN canon c ON b.company_key = c.company_key
  LEFT JOIN phone_map p ON b.phone_clean = p.phone_clean
)
SELECT
  registration_id, edition_id, name_clean, email_clean, phone_clean,
  company_key, company_canonical, job_title, registered_at, source, person_key,
  CONCAT('P', LPAD(CAST(DENSE_RANK() OVER (ORDER BY person_key) AS STRING), 6, '0')) AS person_id
FROM keyed;
