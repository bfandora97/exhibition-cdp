-- Tabel akhir: 1 baris = 1 orang (Visitor 360). Dipakai langsung oleh Power BI / Looker Studio.
CREATE OR REPLACE TABLE exhibition_cdp.visitor_360 AS
WITH p AS (
  SELECT person_id,
         ANY_VALUE(name_final) AS full_name,
         ANY_VALUE(email_final) AS email,
         ANY_VALUE(phone_final) AS phone,
         ANY_VALUE(company_final) AS company,
         ANY_VALUE(job_title_final) AS job_title,
         COUNT(DISTINCT edition_id) AS editions_registered,
         MIN(registered_at) AS first_registered,
         MAX(registered_at) AS last_registered
  FROM exhibition_cdp.clean_registrations
  GROUP BY person_id
),
att AS (
  SELECT person_id,
         COUNT(DISTINCT edition_id) AS editions_attended,
         COUNT(*) AS days_attended,
         MAX(scan_date) AS last_attended
  FROM exhibition_cdp.clean_attendance_daily
  GROUP BY person_id
),
cmp AS (
  SELECT person_id,
         COUNTIF(event_name = 'email_sent') AS email_sent,
         COUNTIF(event_name = 'email_open') AS email_open,
         COUNTIF(event_name = 'email_click') AS email_click,
         COUNTIF(event_name = 'wa_sent') AS wa_sent,
         COUNTIF(event_name = 'wa_read') AS wa_read,
         COUNTIF(event_name = 'wa_reply') AS wa_reply,
         COUNTIF(event_name = 'register_conversion') AS register_conversion
  FROM exhibition_cdp.stg_campaign_events
  WHERE is_matched
  GROUP BY person_id
)
SELECT
  p.*,
  IFNULL(att.editions_attended, 0) AS editions_attended,
  IFNULL(att.days_attended, 0) AS days_attended,
  att.last_attended,
  IFNULL(cmp.email_sent, 0) AS email_sent,
  IFNULL(cmp.email_open, 0) AS email_open,
  IFNULL(cmp.email_click, 0) AS email_click,
  IFNULL(cmp.wa_sent, 0) AS wa_sent,
  IFNULL(cmp.wa_read, 0) AS wa_read,
  IFNULL(cmp.wa_reply, 0) AS wa_reply,
  IFNULL(cmp.register_conversion, 0) AS register_conversion,
  CASE
    WHEN IFNULL(att.editions_attended, 0) >= 3 THEN 'Loyal'
    WHEN IFNULL(att.editions_attended, 0) = 2 THEN 'Returning'
    WHEN IFNULL(att.editions_attended, 0) = 1 THEN 'New'
    ELSE 'Registered - No Show'
  END AS segment,
  ROUND(SAFE_DIVIDE(IFNULL(att.editions_attended, 0), p.editions_registered), 2) AS show_up_rate,
  CASE
    WHEN IFNULL(cmp.email_click, 0) + IFNULL(cmp.wa_reply, 0) >= 2 THEN 'High'
    WHEN IFNULL(cmp.email_click, 0) + IFNULL(cmp.wa_reply, 0) = 1 THEN 'Medium'
    ELSE 'Low'
  END AS engagement
FROM p
LEFT JOIN att ON p.person_id = att.person_id
LEFT JOIN cmp ON p.person_id = cmp.person_id;
