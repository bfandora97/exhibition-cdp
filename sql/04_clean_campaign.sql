-- Event campaign (JSON nested): dedup event_id, bersihkan email/phone, petakan ke person_id.
CREATE OR REPLACE TABLE exhibition_cdp.stg_campaign_events AS
WITH dedup AS (
  SELECT * EXCEPT (rn)
  FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_timestamp) AS rn
    FROM exhibition_cdp.raw_campaign_events
  )
  WHERE rn = 1
),
ev AS (
  SELECT event_id, event_name, event_timestamp, channel, edition_id,
         event_params.campaign_id AS campaign_id,
         exhibition_cdp.clean_email(user_properties.email) AS email_clean,
         exhibition_cdp.clean_phone(user_properties.phone) AS phone_clean
  FROM dedup
),
email_map AS (
  SELECT email_clean, MIN(person_id) AS person_id
  FROM exhibition_cdp.stg_registrations WHERE email_clean IS NOT NULL GROUP BY email_clean
),
phone_map AS (
  SELECT phone_clean, MIN(person_id) AS person_id
  FROM exhibition_cdp.stg_registrations WHERE phone_clean IS NOT NULL GROUP BY phone_clean
)
SELECT ev.*,
       COALESCE(em.person_id, pm.person_id) AS person_id,
       COALESCE(em.person_id, pm.person_id) IS NOT NULL AS is_matched
FROM ev
LEFT JOIN email_map em ON ev.email_clean = em.email_clean
LEFT JOIN phone_map pm ON ev.phone_clean = pm.phone_clean;
