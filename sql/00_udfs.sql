-- Fungsi cleaning reusable (BigQuery Standard SQL). Dataset: exhibition_cdp
-- Logikanya sama dengan src/common.py

CREATE OR REPLACE FUNCTION exhibition_cdp.clean_email(raw STRING) RETURNS STRING AS ((
  SELECT IF(REGEXP_CONTAINS(fixed, r'^[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)*\.[a-z]{2,}$'), fixed, NULL)
  FROM (
    SELECT CONCAT(
      SPLIT(e, '@')[SAFE_OFFSET(0)], '@',
      CASE SPLIT(e, '@')[SAFE_OFFSET(1)]
        WHEN 'gmial.com'  THEN 'gmail.com'
        WHEN 'gmai.com'   THEN 'gmail.com'
        WHEN 'gmail.co'   THEN 'gmail.com'
        WHEN 'gmail.con'  THEN 'gmail.com'
        WHEN 'gmaill.com' THEN 'gmail.com'
        WHEN 'yahooo.com' THEN 'yahoo.com'
        WHEN 'yaho.com'   THEN 'yahoo.com'
        WHEN 'outlok.com' THEN 'outlook.com'
        ELSE SPLIT(e, '@')[SAFE_OFFSET(1)]
      END) AS fixed
    FROM (SELECT LOWER(NULLIF(TRIM(raw), '')) AS e)
  )
));

CREATE OR REPLACE FUNCTION exhibition_cdp.clean_phone(raw STRING) RETURNS STRING AS ((
  SELECT IF(REGEXP_CONTAINS(rest, r'^8[0-9]{8,11}$'), CONCAT('+62', rest), NULL)
  FROM (
    SELECT CASE
             WHEN STARTS_WITH(d, '62') THEN SUBSTR(d, 3)
             WHEN STARTS_WITH(d, '0')  THEN SUBSTR(d, 2)
             ELSE d
           END AS rest
    FROM (SELECT REGEXP_REPLACE(IFNULL(raw, ''), r'\D', '') AS d)
  )
));

CREATE OR REPLACE FUNCTION exhibition_cdp.company_key(raw STRING) RETURNS STRING AS (
  TRIM(REGEXP_REPLACE(
    REGEXP_REPLACE(REGEXP_REPLACE(UPPER(IFNULL(raw, '')), r'[.,]', ' '), r'\b(PT|CV|TBK)\b', ' '),
    r'\s+', ' '))
);
