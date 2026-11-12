# Data Quality & Reconciliation Report

## Data quality score (before vs after)

**Overall: 75.5% -> 99.0%**

| Dimension | Metric | Before | After |
|---|---|---|---|
| Completeness | Usable email rate | 86.2% | 97.8% |
| Completeness | Company name filled | 98.3% | 99.5% |
| Validity | Phone in standard +62 format | 23.4% | 97.9% |
| Uniqueness | Non-duplicate registrations | 94.5% | 100.0% |
| Uniqueness | Non-duplicate badge scans | 92.4% | 100.0% |
| Consistency | Company name in canonical form | 79.4% | 100.0% |
| Integrity | Scans linked to a registration | 95.7% | 98.7% |
| Integrity | Campaign events linked to a person | 82.2% | 98.1% |

## Reconciliation per edisi

| Edisi | Reg raw | Reg clean | Reg dilaporkan | Selisih raw | Selisih clean | Visitor raw | Visitor clean | Visitor dilaporkan | Selisih raw | Selisih clean |
|---|---|---|---|---|---|---|---|---|---|---|
| NFE2024 | 2,582 | 2,458 | 2,456 | +126 | +2 | 1,930 | 1,783 | 1,795 | +135 | -12 |
| NFE2025 | 2,572 | 2,415 | 2,415 | +157 | +0 | 1,863 | 1,755 | 1,762 | +101 | -7 |
| NFE2026 | 2,525 | 2,384 | 2,381 | +144 | +3 | 1,826 | 1,702 | 1,714 | +112 | -12 |
| PPI2025 | 2,657 | 2,514 | 2,514 | +143 | +0 | 1,974 | 1,829 | 1,847 | +127 | -18 |
| PPI2026 | 2,598 | 2,447 | 2,445 | +153 | +2 | 1,955 | 1,813 | 1,827 | +128 | -14 |

## Identity resolution vs kunci jawaban

- Orang sebenarnya: **6,000**, hasil pipeline: **6,061**
- Person ID yang isinya 1 orang asli saja (tidak salah gabung): **100.0%**
- Orang asli yang utuh di 1 person ID (tidak terpecah): **99.0%**


> Sisa selisih visitor = scan dengan ID tidak dikenal (walk-in/badge rusak) yang memang tidak bisa dipetakan ke registrasi. Ini dicatat sebagai known limitation, bukan di-force match.
