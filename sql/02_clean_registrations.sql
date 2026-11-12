-- Dedup registrasi (1 orang = 1 baris per edisi) + golden record per orang.
CREATE OR REPLACE TABLE exhibition_cdp.clean_registrations AS
WITH ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY edition_id, person_id ORDER BY registered_at, registration_id) AS rn
  FROM exhibition_cdp.stg_registrations
),
golden AS (  -- nilai terbaru yang tidak kosong, dipakai untuk mengisi yang bolong
  SELECT
    person_id,
    ARRAY_AGG(name_clean ORDER BY registered_at DESC LIMIT 1)[OFFSET(0)] AS name_final,
    ARRAY_AGG(email_clean IGNORE NULLS ORDER BY registered_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS email_final,
    ARRAY_AGG(phone_clean IGNORE NULLS ORDER BY registered_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS phone_final,
    ARRAY_AGG(company_canonical IGNORE NULLS ORDER BY registered_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS company_final,
    ARRAY_AGG(job_title IGNORE NULLS ORDER BY registered_at DESC LIMIT 1)[SAFE_OFFSET(0)] AS job_title_final
  FROM exhibition_cdp.stg_registrations
  GROUP BY person_id
)
SELECT r.registration_id, r.edition_id, r.person_id, r.registered_at, r.source,
       g.name_final, g.email_final, g.phone_final, g.company_final, g.job_title_final
FROM ranked r
JOIN golden g USING (person_id)
WHERE r.rn = 1;
