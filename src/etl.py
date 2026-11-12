"""ETL: bersihkan 3 sumber -> identity resolution -> tabel Visitor 360.

Input : data/raw/*
Output: data/clean/*  (registrations_resolved, registrations_clean, attendance_resolved,
        attendance_daily, campaign_resolved, visitor_360)
"""
import json
from pathlib import Path

import pandas as pd

from common import (clean_email, clean_phone, collapse_ws, company_key, has, none_if_na)

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"


def read_csv(name):
    return pd.read_csv(RAW / name, dtype=str, keep_default_na=False)


def resolve_persons(df):
    """Identity resolution (union-find): record yang berbagi email ATAU phone = orang yang sama."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for r in df.itertuples():
        node = ("r", r.registration_id)
        find(node)
        linked = False
        if has(r.email_clean):
            union(node, ("e", r.email_clean))
            linked = True
        if has(r.phone_clean):
            union(node, ("p", r.phone_clean))
            linked = True
        if not linked:  # fallback terakhir: nama + perusahaan
            union(node, ("n", r.name_clean.lower(), r.company_key))
    ids, roots = [], {}
    for r in df.itertuples():
        root = find(("r", r.registration_id))
        if root not in roots:
            roots[root] = f"P{len(roots) + 1:06d}"
        ids.append(roots[root])
    return ids


def build_registrations():
    df = read_csv("registrations.csv")
    df["registration_id"] = df.registration_id.str.strip().str.upper()
    df["name_clean"] = df.full_name.map(lambda x: collapse_ws(x).title())
    em = df.email.map(clean_email)
    df["email_clean"] = [e for e, _ in em]
    df["email_status"] = [s for _, s in em]
    df["phone_clean"] = df.phone.map(clean_phone)
    df["company_key"] = df.company_name.map(company_key)
    df["company_ws"] = df.company_name.map(collapse_ws)
    for c in ["email_clean", "phone_clean"]:
        df[c] = none_if_na(df[c])

    # nama perusahaan kanonik = modus per company_key
    counts = (df[df.company_key != ""].groupby(["company_key", "company_ws"]).size().reset_index(name="n")
              .sort_values(["company_key", "n", "company_ws"], ascending=[True, False, True]))
    canon = counts.drop_duplicates("company_key").set_index("company_key")["company_ws"]
    df["company_canonical"] = none_if_na(df.company_key.map(canon))
    df["job_title_clean"] = none_if_na(df.job_title.map(collapse_ws).replace("", None))
    df["registered_at"] = pd.to_datetime(df.registered_at)

    df = df.sort_values(["registered_at", "registration_id"]).reset_index(drop=True)
    df["person_id"] = resolve_persons(df)
    df["is_duplicate"] = df.duplicated(["edition_id", "person_id"], keep="first")

    # golden record per orang: ambil nilai terbaru yang tidak kosong, isi yang bolong
    def latest(col):
        return df.dropna(subset=[col]).groupby("person_id")[col].last()

    df["email_final"] = df.email_clean.fillna(df.person_id.map(latest("email_clean")))
    df["phone_final"] = df.phone_clean.fillna(df.person_id.map(latest("phone_clean")))
    df["company_final"] = df.company_canonical.fillna(df.person_id.map(latest("company_canonical")))
    df["job_title_final"] = df.job_title_clean.fillna(df.person_id.map(latest("job_title_clean")))
    return df


def build_attendance(regs):
    df = read_csv("attendance.csv")
    df["registration_id_clean"] = df.registration_id.str.strip().str.upper()
    df["person_id"] = df.registration_id_clean.map(regs.set_index("registration_id")["person_id"])
    df["is_matched"] = df.person_id.notna()
    df = df.sort_values(["scan_date", "scan_time", "scan_id"]).reset_index(drop=True)
    df["is_duplicate_scan"] = df.duplicated(["registration_id_clean", "scan_date", "gate"], keep="first")
    ok = df[df.is_matched & ~df.is_duplicate_scan]
    daily = ok[["person_id", "edition_id", "scan_date"]].drop_duplicates().reset_index(drop=True)
    return df, daily


def build_campaign(regs):
    with open(RAW / "campaign_events.jsonl", encoding="utf-8") as f:
        df = pd.json_normalize([json.loads(line) for line in f])
    df = df.rename(columns={"user_properties.email": "email_raw", "user_properties.phone": "phone_raw",
                            "event_params.campaign_id": "campaign_id"})
    df["is_duplicate_event"] = df.duplicated("event_id", keep="first")
    df["email_clean"] = none_if_na(pd.Series([clean_email(x)[0] for x in df.email_raw], index=df.index))
    df["phone_clean"] = none_if_na(df.phone_raw.map(clean_phone))
    e_map = regs.dropna(subset=["email_clean"]).drop_duplicates("email_clean").set_index("email_clean")["person_id"]
    p_map = regs.dropna(subset=["phone_clean"]).drop_duplicates("phone_clean").set_index("phone_clean")["person_id"]
    df["person_id"] = df.email_clean.map(e_map).fillna(df.phone_clean.map(p_map))
    df["is_matched"] = df.person_id.notna()
    return df


def segment(n):
    if n >= 3:
        return "Loyal"
    if n == 2:
        return "Returning"
    if n == 1:
        return "New"
    return "Registered - No Show"


def build_visitor_360(regs_clean, daily, camp):
    r = regs_clean.sort_values("registered_at")
    people = r.groupby("person_id").agg(
        full_name=("name_clean", "last"), email=("email_final", "last"), phone=("phone_final", "last"),
        company=("company_final", "last"), job_title=("job_title_final", "last"),
        editions_registered=("edition_id", "nunique"), first_registered=("registered_at", "min"),
        last_registered=("registered_at", "max")).reset_index()
    att = daily.groupby("person_id").agg(
        editions_attended=("edition_id", "nunique"), days_attended=("scan_date", "count"),
        last_attended=("scan_date", "max")).reset_index()
    c = camp[camp.is_matched & ~camp.is_duplicate_event]
    cmp_ = c.pivot_table(index="person_id", columns="event_name", values="event_id", aggfunc="count",
                         fill_value=0).reset_index()
    for col in ["email_sent", "email_open", "email_click", "wa_sent", "wa_read", "wa_reply", "register_conversion"]:
        if col not in cmp_:
            cmp_[col] = 0
    v = people.merge(att, on="person_id", how="left").merge(cmp_, on="person_id", how="left")
    num = ["editions_attended", "days_attended", "email_sent", "email_open", "email_click", "wa_sent", "wa_read",
           "wa_reply", "register_conversion"]
    v[num] = v[num].fillna(0).astype(int)
    v["segment"] = v.editions_attended.map(segment)
    v["show_up_rate"] = (v.editions_attended / v.editions_registered).round(2)
    v["engagement"] = (v.email_click + v.wa_reply).map(lambda x: "High" if x >= 2 else "Medium" if x == 1 else "Low")
    return v


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    regs = build_registrations()
    regs_clean = regs[~regs.is_duplicate]
    att, daily = build_attendance(regs)
    camp = build_campaign(regs)
    v360 = build_visitor_360(regs_clean, daily, camp)

    regs.to_csv(CLEAN / "registrations_resolved.csv", index=False)
    regs_clean.to_csv(CLEAN / "registrations_clean.csv", index=False)
    att.to_csv(CLEAN / "attendance_resolved.csv", index=False)
    daily.to_csv(CLEAN / "attendance_daily.csv", index=False)
    camp.to_csv(CLEAN / "campaign_resolved.csv", index=False)
    v360.to_csv(CLEAN / "visitor_360.csv", index=False)

    print(f"registrasi raw {len(regs):,} -> clean {len(regs_clean):,} | orang unik: {regs.person_id.nunique():,}")
    print(f"scan raw {len(att):,} -> hari-kehadiran unik {len(daily):,}")
    print(f"event raw {len(camp):,} | tidak ketemu orangnya: {(~camp.is_matched).sum():,}")
    print(v360.segment.value_counts().to_string())


if __name__ == "__main__":
    main()
