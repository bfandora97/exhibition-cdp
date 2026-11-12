# Panduan Dashboard (Power BI atau Looker Studio)

**Sumber data:** `data/clean/visitor_360.csv`, `output/dq_metrics.csv`, `output/reconciliation.csv`
(atau tabel BigQuery `exhibition_cdp.visitor_360`).

## Halaman 1: Visitor Overview
- Kartu: total orang unik, % Loyal, show-up rate rata-rata
- Donut: jumlah per `segment`
- Bar: top 10 `company` berdasarkan jumlah visitor
- Slicer: `engagement`, `job_title`

## Halaman 2: Campaign Engagement
- Open rate email = `SUM(email_open) / SUM(email_sent)`
- Click rate = `SUM(email_click) / SUM(email_sent)`
- WA read rate = `SUM(wa_read) / SUM(wa_sent)`
- Bar: engagement per `segment` (apakah Loyal lebih responsif?)

## Halaman 3: Data Quality
- Bar before vs after dari `dq_metrics.csv` (per metric)
- Kartu: overall DQ score before dan after
- Tabel `reconciliation.csv`: selisih raw vs clean per edisi

## Measure contoh (DAX)
```
Loyal % = DIVIDE(CALCULATE(COUNTROWS(visitor_360), visitor_360[segment] = "Loyal"), COUNTROWS(visitor_360))
Open Rate = DIVIDE(SUM(visitor_360[email_open]), SUM(visitor_360[email_sent]))
Show-up Rate = AVERAGE(visitor_360[show_up_rate])
```

## Publish
Power BI link publik butuh lisensi berbayar. Alternatif gratis: Looker Studio (konek ke BigQuery, share via link),
atau taruh screenshot + file .pbix di GitHub.
