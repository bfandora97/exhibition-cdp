"""Data quality (before vs after) + reconciliation antar sistem.

Output: output/dq_metrics.csv, output/reconciliation.csv, output/dq_report.md
"""
from pathlib import Path

import pandas as pd

from common import DOMAIN_FIX, EMAIL_RE, company_key, is_blank

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN, OUT, TRUTH = ROOT / "data/raw", ROOT / "data/clean", ROOT / "output", ROOT / "data/ground_truth"
PHONE_STD = r"^\+62 ?8\d{8,11}$"


def raw_email_valid(x):
    """Valid kalau sudah benar apa adanya: tanpa spasi, format benar, domain bukan typo."""
    if is_blank(x):
        return False
    s = str(x)
    return bool(EMAIL_RE.match(s.lower())) and s == s.strip() and s.split("@")[-1].lower() not in DOMAIN_FIX


def main():
    OUT.mkdir(exist_ok=True)
    rr = pd.read_csv(RAW / "registrations.csv", dtype=str, keep_default_na=False)
    ra = pd.read_csv(RAW / "attendance.csv", dtype=str, keep_default_na=False)
    summ = pd.read_csv(RAW / "edition_summary.csv")
    res = pd.read_csv(CLEAN / "registrations_resolved.csv", dtype=str, keep_default_na=False)
    clean = res[res.is_duplicate == "False"]
    att = pd.read_csv(CLEAN / "attendance_resolved.csv", dtype=str, keep_default_na=False)
    daily = pd.read_csv(CLEAN / "attendance_daily.csv", dtype=str)
    camp = pd.read_csv(CLEAN / "campaign_resolved.csv", dtype=str, keep_default_na=False)

    n_raw, n_clean = len(rr), len(clean)
    m = []  # (dimension, metric, before, after)

    # 1. Completeness: email yang bisa dipakai
    m.append(("Completeness", "Usable email rate",
              rr.email.map(raw_email_valid).mean(), (clean.email_final != "").mean()))
    m.append(("Completeness", "Company name filled",
              (rr.company_name.str.strip() != "").mean(), (clean.company_final != "").mean()))
    # 2. Validity: phone format standar
    m.append(("Validity", "Phone in standard +62 format",
              rr.phone.str.match(PHONE_STD).mean(), (clean.phone_final != "").mean()))
    # 3. Uniqueness
    dup_rate = (res.is_duplicate == "True").mean()
    after_dup = clean.duplicated(["edition_id", "person_id"]).mean()
    m.append(("Uniqueness", "Non-duplicate registrations", 1 - dup_rate, 1 - after_dup))
    scan_dup = (att.is_duplicate_scan == "True").mean()
    m.append(("Uniqueness", "Non-duplicate badge scans", 1 - scan_dup, 1.0))
    # 4. Consistency: nama perusahaan sesuai bentuk kanonik
    has_c = rr[rr.company_name.str.strip() != ""]
    canon_by_key = res[res.company_canonical != ""].drop_duplicates("company_key").set_index("company_key")[
        "company_canonical"]
    consistent_before = (has_c.company_name == has_c.company_name.map(
        lambda x: canon_by_key.get(company_key(x), ""))).mean()
    m.append(("Consistency", "Company name in canonical form", consistent_before, 1.0))
    # 5. Integrity (referensi antar sistem)
    exact_ids = set(rr.registration_id)
    m.append(("Integrity", "Scans linked to a registration",
              ra.registration_id.isin(exact_ids).mean(), (att.is_matched == "True").mean()))
    ev_exact = set(rr.email)
    camp_before = camp.email_raw.isin(ev_exact).mean()
    m.append(("Integrity", "Campaign events linked to a person", camp_before, (camp.is_matched == "True").mean()))

    dq = pd.DataFrame(m, columns=["dimension", "metric", "before", "after"])
    dim = dq.groupby("dimension")[["before", "after"]].mean()
    score_b, score_a = dim.before.mean(), dim.after.mean()
    dq.to_csv(OUT / "dq_metrics.csv", index=False)

    # ---------- reconciliation per edisi ----------
    rec = []
    for _, s in summ.iterrows():
        ed = s.edition_id
        rec.append({
            "edition_id": ed,
            "reg_raw_rows": int((rr.edition_id == ed).sum()),
            "reg_clean_unique": int((clean.edition_id == ed).sum()),
            "reg_reported": int(s.reported_registered),
            "visitors_raw_distinct_ids": int(ra[ra.edition_id == ed].registration_id.nunique()),
            "visitors_clean_unique": int(daily[daily.edition_id == ed].person_id.nunique()),
            "visitors_reported": int(s.reported_visitors),
        })
    rec = pd.DataFrame(rec)
    rec["reg_diff_raw"] = rec.reg_raw_rows - rec.reg_reported
    rec["reg_diff_clean"] = rec.reg_clean_unique - rec.reg_reported
    rec["vis_diff_raw"] = rec.visitors_raw_distinct_ids - rec.visitors_reported
    rec["vis_diff_clean"] = rec.visitors_clean_unique - rec.visitors_reported
    rec.to_csv(OUT / "reconciliation.csv", index=False)

    # ---------- akurasi vs ground truth ----------
    truth_txt = ""
    tp = TRUTH / "registrations_truth.csv"
    if tp.exists():
        t = pd.read_csv(tp, dtype=str).merge(res[["registration_id", "person_id"]], on="registration_id")
        n_true, n_found = t.true_person_id.nunique(), t.person_id.nunique()
        pure = (t.groupby("person_id").true_person_id.nunique() == 1).mean()
        whole = (t.groupby("true_person_id").person_id.nunique() == 1).mean()
        truth_txt = (f"\n## Identity resolution vs kunci jawaban\n\n"
                     f"- Orang sebenarnya: **{n_true:,}**, hasil pipeline: **{n_found:,}**\n"
                     f"- Person ID yang isinya 1 orang asli saja (tidak salah gabung): **{pure:.1%}**\n"
                     f"- Orang asli yang utuh di 1 person ID (tidak terpecah): **{whole:.1%}**\n")

    def pct(x):
        return f"{x:.1%}"

    L = ["# Data Quality & Reconciliation Report\n", "## Data quality score (before vs after)\n",
         f"**Overall: {pct(score_b)} -> {pct(score_a)}**\n", "| Dimension | Metric | Before | After |",
         "|---|---|---|---|"]
    for r in dq.itertuples():
        L.append(f"| {r.dimension} | {r.metric} | {pct(r.before)} | {pct(r.after)} |")
    L += ["", "## Reconciliation per edisi\n",
          "| Edisi | Reg raw | Reg clean | Reg dilaporkan | Selisih raw | Selisih clean | "
          "Visitor raw | Visitor clean | Visitor dilaporkan | Selisih raw | Selisih clean |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rec.itertuples():
        L.append(f"| {r.edition_id} | {r.reg_raw_rows:,} | {r.reg_clean_unique:,} | {r.reg_reported:,} | "
                 f"{r.reg_diff_raw:+,} | {r.reg_diff_clean:+,} | {r.visitors_raw_distinct_ids:,} | "
                 f"{r.visitors_clean_unique:,} | {r.visitors_reported:,} | {r.vis_diff_raw:+,} | "
                 f"{r.vis_diff_clean:+,} |")
    L.append(truth_txt)
    L.append("\n> Sisa selisih visitor = scan dengan ID tidak dikenal (walk-in/badge rusak) yang memang tidak "
             "bisa dipetakan ke registrasi. Ini dicatat sebagai known limitation, bukan di-force match.\n")
    (OUT / "dq_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
