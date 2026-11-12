# Data Mapping: Source -> Visitor 360

## Aturan cleaning
| Field | Aturan |
|---|---|
| email | trim, lowercase, perbaiki typo domain (gmial.com -> gmail.com dst), validasi regex; tidak valid = NULL |
| phone | ambil digit, buang awalan 0/62, harus `8` + 8-11 digit, simpan sebagai `+62...` |
| company | uppercase, buang tanda baca dan PT/CV/Tbk jadi `company_key`; nama kanonik = bentuk paling sering (modus) |
| name | trim, rapikan spasi, Title Case |
| registration_id | trim + uppercase (agar cocok dengan scan badge) |

## Identity resolution
- Python: record yang berbagi email **atau** phone digabung (union-find). Tanpa email dan phone: nama + perusahaan.
- BigQuery: hierarki kunci `email -> email via phone -> phone -> nama|perusahaan`.
- Dedup: 1 orang = 1 baris per edisi (ambil registrasi paling awal).
- Golden record: field kosong diisi nilai terbaru dari edisi lain.

## Mapping kolom
| Source | Kolom | Target (`visitor_360`) | Catatan |
|---|---|---|---|
| registrations | full_name | full_name | cleaned |
| registrations | email | email | cleaned + golden |
| registrations | phone | phone | +62 format + golden |
| registrations | company_name | company | canonical + golden |
| registrations | job_title | job_title | golden |
| registrations | edition_id | editions_registered | count distinct |
| registrations | registered_at | first_registered, last_registered | min / max |
| attendance | registration_id + scan_date | editions_attended, days_attended, last_attended | via person_id, scan ganda dibuang |
| campaign_events | event_name | email_sent/open/click, wa_sent/read/reply, register_conversion | count per orang |
| (derived) | editions_attended | segment | >=3 Loyal, 2 Returning, 1 New, 0 Registered - No Show |
| (derived) | clicks + replies | engagement | >=2 High, 1 Medium, 0 Low |
| (derived) | attended / registered | show_up_rate | |

## Known limitations
- Scan dengan ID tidak dikenal tidak di-force match (dilaporkan sebagai orphan).
- Orang tanpa email dan phone di semua registrasinya bisa terpecah jadi >1 person ID.
- Versi SQL tidak menggabungkan 1 phone dengan 2 email berbeda (versi Python menggabungkan).
