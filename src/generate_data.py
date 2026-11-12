"""Generate data dummy pameran B2B (FIKTIF) dengan masalah data quality yang sengaja dibuat.

Output (data/raw):
  registrations.csv     -> mirip CRM   (registrasi pengunjung)
  attendance.csv        -> mirip ERP   (scan badge per hari)
  campaign_events.jsonl -> mirip GA4   (event email/WhatsApp, nested JSON)
  edition_summary.csv   -> laporan resmi per edisi (untuk reconciliation)
Output (data/ground_truth): kunci jawaban untuk mengukur akurasi cleaning.
"""
import json
import random
import re
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
TRUTH = ROOT / "data" / "ground_truth"
SEED, N_PEOPLE, N_COMPANIES, DAYS = 42, 6000, 700, 3

EDITIONS = [
    ("NFE2024", "Nusantara Food Expo 2024", date(2024, 5, 14)),
    ("NFE2025", "Nusantara Food Expo 2025", date(2025, 5, 13)),
    ("NFE2026", "Nusantara Food Expo 2026", date(2026, 5, 12)),
    ("PPI2025", "Pack & Process Indonesia 2025", date(2025, 9, 23)),
    ("PPI2026", "Pack & Process Indonesia 2026", date(2026, 9, 22)),
]
SOURCES = ["Online", "Email Campaign", "WhatsApp", "Referral", "Onsite"]
GATES = ["Gate A", "Gate B", "Gate C"]
W1 = ["Sinar", "Maju", "Mitra", "Nusantara", "Bumi", "Cipta", "Karya", "Sumber", "Abadi", "Global", "Prima",
      "Tirta", "Boga", "Rasa", "Agro", "Jaya", "Mandiri", "Sentosa", "Lestari", "Makmur", "Berkah", "Tunggal",
      "Indah", "Harapan"]
W2 = ["Pangan", "Utama", "Persada", "Sejahtera", "Bersama", "Murni", "Alam", "Kencana", "Artha", "Graha",
      "Langgeng", "Surya", "Cahaya", "Dwi", "Tri", "Mega", "Citra", "Adi", "Putra", "Wijaya", "Hasta", "Bina",
      "Kreasi", "Lintas"]
CAT = ["Pangan", "Boga", "Kemasan", "Logistik", "Foods", "Trading", "Indo", "Packaging"]
JOBS = ["Purchasing Manager", "Marketing Manager", "Procurement Staff", "Sales Executive", "Business Development",
        "Operations Manager", "Quality Assurance", "Supply Chain Lead", "Owner", "Director", "R&D Manager",
        "Brand Manager"]
FREE = ["gmail.com", "gmail.com", "gmail.com", "yahoo.com", "yahoo.com", "outlook.com"]
TYPOS = {
    "gmail.com": ["gmial.com", "gmai.com", "gmail.co", "gmail.con", "gmaill.com"],
    "yahoo.com": ["yahooo.com", "yaho.com"],
    "outlook.com": ["outlok.com"],
}


def slug(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def make_companies(n):
    seen, out = set(), []
    while len(out) < n:
        w = [random.choice(W1), random.choice(W2), random.choice(CAT)]
        name = " ".join(w)
        if name in seen:
            continue
        seen.add(name)
        legal = random.choice(["PT", "PT", "PT", "CV"])
        out.append({"name": f"{legal} {name}", "domain": slug(name) + ".co.id"})
    return out


def make_people(fake, companies):
    people, used_email, used_phone = [], set(), set()
    for i in range(N_PEOPLE):
        c = random.choice(companies)
        first, last = fake.first_name(), fake.last_name()
        free = random.random() < 0.30
        while True:
            if free:
                email = f"{slug(first)}{slug(last)}{random.randint(1, 999)}@{random.choice(FREE)}"
            else:
                email = f"{slug(first)}.{slug(last)}{random.choice(['', random.randint(1, 99)])}@{c['domain']}"
            if email not in used_email:
                used_email.add(email)
                break
        while True:
            phone = f"8{random.randint(10**8, 10**9 - 1)}"
            if phone not in used_phone:
                used_phone.add(phone)
                break
        k = random.choices([1, 2, 3, 4, 5], [45, 25, 15, 10, 5])[0]
        people.append({
            "id": f"T{i + 1:05d}", "name": f"{first} {last}", "email": email, "free": free, "phone": phone,
            "company": c["name"], "job": random.choice(JOBS), "k": k,
            "p_att": 0.85 if k >= 3 else 0.60,
        })
    return people


# ---------- mutasi (bikin data kotor) ----------
def mut_name(n):
    r = random.random()
    if r < 0.08:
        return n.upper()
    if r < 0.12:
        return n.lower()
    if r < 0.20:
        return "  " + n.replace(" ", "  ") + " "
    return n


def mut_email(e, free):
    r = random.random()
    if r < 0.05:
        return ""
    if r < 0.08:
        user, dom = e.split("@")
        return random.choice([e.replace("@", ""), e.replace("@", "@@"), f"{user}@{dom.split('.')[0]}"])
    if free and r < 0.20:
        user, dom = e.split("@")
        e = f"{user}@{random.choice(TYPOS[dom])}"
    r2 = random.random()
    if r2 < 0.12:
        e = e.upper()
    elif r2 < 0.15:
        e = f" {e} "
    return e


def mut_phone(p):
    if random.random() < 0.07:
        return ""
    f = random.randint(0, 3)
    if f == 0:
        return "0" + p
    if f == 1:
        return "+62" + p
    if f == 2:
        return "62" + p
    return f"0{p[:3]}-{p[3:7]}-{p[7:]}"


def mut_company(c):
    r = random.random()
    if r < 0.02:
        return ""
    if r < 0.22:
        legal, rest = c.split(" ", 1)
        return random.choice([f"{legal}. {rest}", f"{rest}, {legal}", c.upper(), c.lower(), f"{legal}  {rest}", rest])
    return c


def fmt_ts(d):
    return d.strftime("%Y-%m-%d %H:%M:%S")


def main():
    random.seed(SEED)
    Faker.seed(SEED)
    fake = Faker("id_ID")
    RAW.mkdir(parents=True, exist_ok=True)
    TRUTH.mkdir(parents=True, exist_ok=True)

    people = make_people(fake, make_companies(N_COMPANIES))
    ed_start = {e[0]: e[2] for e in EDITIONS}
    counters = defaultdict(int)

    def new_reg_id(ed):
        counters[ed] += 1
        return f"R-{ed}-{counters[ed]:05d}"

    regs, truth_regs, true_regs = [], [], []
    for p in people:
        for ed_id, _, start in random.sample(EDITIONS, p["k"]):
            source = random.choices(SOURCES, [40, 25, 20, 10, 5])[0]
            if source == "Onsite":
                ts = datetime.combine(start + timedelta(days=random.randint(0, DAYS - 1)), time(8)) + timedelta(
                    minutes=random.randint(0, 480))
            else:
                ts = datetime.combine(start, time(0)) - timedelta(days=random.randint(1, 60),
                                                                  hours=random.randint(0, 23),
                                                                  minutes=random.randint(0, 59))
            rows = [(new_reg_id(ed_id), ts)]
            if random.random() < 0.06:  # registrasi ganda
                rows.append((new_reg_id(ed_id), ts + timedelta(minutes=random.randint(1, 4000))))
            for i, (rid, t) in enumerate(rows):
                regs.append({
                    "registration_id": rid, "edition_id": ed_id, "full_name": mut_name(p["name"]),
                    "email": mut_email(p["email"], p["free"]), "phone": mut_phone(p["phone"]),
                    "company_name": mut_company(p["company"]),
                    "job_title": "" if random.random() < 0.03 else p["job"],
                    "registered_at": fmt_ts(t), "source": source,
                })
                truth_regs.append({"registration_id": rid, "true_person_id": p["id"], "is_duplicate_row": i > 0})
            true_regs.append({"p": p, "ed": ed_id, "ids": [r for r, _ in rows], "source": source, "ts": ts})

    # ---------- attendance ----------
    scans, attended = [], defaultdict(set)
    n_scan = 0
    for tr in true_regs:
        p, ed = tr["p"], tr["ed"]
        if random.random() >= p["p_att"]:
            continue
        attended[ed].add(p["id"])
        n_days = random.choices([1, 2, 3], [50, 30, 20])[0]
        for d in sorted(random.sample(range(DAYS), n_days)):
            rid = random.choice(tr["ids"])
            r = random.random()
            if r < 0.03:
                rid = random.choice([rid.lower(), f" {rid} "])
            elif r < 0.045:
                rid = f"R-{ed}-{random.randint(90000, 99999)}"
            t = datetime.combine(ed_start[ed] + timedelta(days=d), time(8)) + timedelta(
                seconds=random.randint(0, 8 * 3600))
            gate = random.choice(GATES)
            n_scan += 1
            scans.append({"scan_id": f"S{n_scan:07d}", "registration_id": rid, "edition_id": ed,
                          "scan_date": t.strftime("%Y-%m-%d"), "scan_time": t.strftime("%H:%M:%S"), "gate": gate})
            if random.random() < 0.08:  # double scan
                t2 = t + timedelta(minutes=random.randint(1, 5))
                n_scan += 1
                scans.append({"scan_id": f"S{n_scan:07d}", "registration_id": rid, "edition_id": ed,
                              "scan_date": t2.strftime("%Y-%m-%d"), "scan_time": t2.strftime("%H:%M:%S"),
                              "gate": gate})

    # ---------- campaign events (nested JSON ala GA4) ----------
    events, n_ev = [], 0

    def emit(name, channel, ts, ed, p, link=None):
        nonlocal n_ev
        n_ev += 1
        r = random.random()
        email = p["email"]
        if r < 0.03:
            email = None
        elif r < 0.05:
            email = f"unknown{random.randint(1, 99999)}@gmail.com"
        elif r < 0.15:
            email = email.upper()
        elif r < 0.18:
            email = f" {email} "
        phone = None
        if channel == "whatsapp" or random.random() < 0.05:
            phone = random.choice(["0" + p["phone"], "+62" + p["phone"]])
        if email is None and phone is None:
            phone = "0" + p["phone"]
        ev = {
            "event_id": f"E{n_ev:08d}", "event_name": name,
            "event_timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"), "channel": channel, "edition_id": ed,
            "user_properties": {"email": email, "phone": phone},
            "event_params": {
                "campaign_id": f"CMP-{ed}-{'EM' if channel == 'email' else 'WA'}",
                "utm_source": "eloqua" if channel == "email" else "makari",
                "utm_medium": channel, "link_url": link,
            },
        }
        events.append(ev)
        if random.random() < 0.02:  # event ganda
            events.append(dict(ev))

    for tr in true_regs:
        p, ed = tr["p"], tr["ed"]
        start = datetime.combine(ed_start[ed], time(0))
        t0 = start - timedelta(days=random.randint(20, 45), hours=random.randint(0, 23))
        emit("email_sent", "email", t0, ed, p)
        if random.random() < 0.45:
            t1 = t0 + timedelta(hours=random.randint(1, 72))
            emit("email_open", "email", t1, ed, p)
            if random.random() < 0.30:
                emit("email_click", "email", t1 + timedelta(minutes=random.randint(1, 2000)), ed, p,
                     link=f"https://example-expo.test/{ed.lower()}/register")
        if random.random() < 0.70:
            w0 = start - timedelta(days=random.randint(10, 30), hours=random.randint(0, 23))
            emit("wa_sent", "whatsapp", w0, ed, p)
            if random.random() < 0.60:
                w1 = w0 + timedelta(hours=random.randint(1, 24))
                emit("wa_read", "whatsapp", w1, ed, p)
                if random.random() < 0.12:
                    emit("wa_reply", "whatsapp", w1 + timedelta(minutes=random.randint(1, 700)), ed, p)
        if tr["source"] in ("Email Campaign", "WhatsApp"):
            ch = "email" if tr["source"] == "Email Campaign" else "whatsapp"
            emit("register_conversion", ch, tr["ts"], ed, p)

    # ---------- tulis file ----------
    pd.DataFrame(regs).to_csv(RAW / "registrations.csv", index=False)
    pd.DataFrame(scans).to_csv(RAW / "attendance.csv", index=False)
    with open(RAW / "campaign_events.jsonl", "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    reg_true = defaultdict(set)
    for tr in true_regs:
        reg_true[tr["ed"]].add(tr["p"]["id"])
    pd.DataFrame([{
        "edition_id": e[0], "edition_name": e[1], "start_date": e[2].isoformat(), "days": DAYS,
        "reported_registered": len(reg_true[e[0]]), "reported_visitors": len(attended[e[0]]),
    } for e in EDITIONS]).to_csv(RAW / "edition_summary.csv", index=False)
    pd.DataFrame(truth_regs).to_csv(TRUTH / "registrations_truth.csv", index=False)

    print(f"registrations: {len(regs):,} | attendance scans: {len(scans):,} | campaign events: {len(events):,}")
    print(f"true unique persons: {len(people):,} -> file di {RAW}")


if __name__ == "__main__":
    main()
