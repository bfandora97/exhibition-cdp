-- Reconciliation: angka sistem vs laporan resmi per edisi (raw vs clean).
WITH reg_raw AS (SELECT edition_id, COUNT(*) AS reg_raw_rows FROM exhibition_cdp.raw_registrations GROUP BY edition_id),
reg_clean AS (SELECT edition_id, COUNT(*) AS reg_clean_unique FROM exhibition_cdp.clean_registrations GROUP BY edition_id),
vis_raw AS (SELECT edition_id, COUNT(DISTINCT registration_id) AS visitors_raw FROM exhibition_cdp.raw_attendance GROUP BY edition_id),
vis_clean AS (SELECT edition_id, COUNT(DISTINCT person_id) AS visitors_clean FROM exhibition_cdp.clean_attendance_daily GROUP BY edition_id)
SELECT
  s.edition_id,
  rr.reg_raw_rows, rc.reg_clean_unique, s.reported_registered,
  rr.reg_raw_rows - s.reported_registered AS reg_diff_raw,
  rc.reg_clean_unique - s.reported_registered AS reg_diff_clean,
  vr.visitors_raw, vc.visitors_clean, s.reported_visitors,
  vr.visitors_raw - s.reported_visitors AS vis_diff_raw,
  vc.visitors_clean - s.reported_visitors AS vis_diff_clean
FROM exhibition_cdp.raw_edition_summary s
JOIN reg_raw rr USING (edition_id)
JOIN reg_clean rc USING (edition_id)
JOIN vis_raw vr USING (edition_id)
JOIN vis_clean vc USING (edition_id)
ORDER BY s.edition_id;
