"""Fungsi cleaning yang dipakai bersama (email, phone, company)."""
import re
import pandas as pd

EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9\-]+(\.[a-z0-9\-]+)*\.[a-z]{2,}$")
DOMAIN_FIX = {
    "gmial.com": "gmail.com", "gmai.com": "gmail.com", "gmail.co": "gmail.com",
    "gmail.con": "gmail.com", "gmaill.com": "gmail.com",
    "yahooo.com": "yahoo.com", "yaho.com": "yahoo.com",
    "outlok.com": "outlook.com",
}
PHONE_RE = re.compile(r"^8\d{8,11}$")
LEGAL_RE = re.compile(r"\b(PT|CV|TBK)\b")


def is_blank(x):
    return x is None or (isinstance(x, float) and pd.isna(x)) or str(x).strip() == ""


def has(v):
    return isinstance(v, str) and v != ""


def clean_email(raw):
    """Return (email_clean, status). status: missing / invalid / fixed / ok."""
    if is_blank(raw):
        return None, "missing"
    e = str(raw).strip().lower()
    user, _, dom = e.partition("@")
    status = "ok"
    if dom in DOMAIN_FIX:
        e = f"{user}@{DOMAIN_FIX[dom]}"
        status = "fixed"
    if EMAIL_RE.match(e):
        return e, status
    return None, "invalid"


def clean_phone(raw):
    """Standarisasi ke +62xxxxxxxxxx. Return None kalau tidak valid."""
    if is_blank(raw):
        return None
    d = re.sub(r"\D", "", str(raw))
    if d.startswith("62"):
        rest = d[2:]
    elif d.startswith("0"):
        rest = d[1:]
    else:
        rest = d
    return "+62" + rest if PHONE_RE.match(rest) else None


def company_key(raw):
    """Kunci normalisasi nama perusahaan: tanpa PT/CV/Tbk, tanpa tanda baca, uppercase."""
    if is_blank(raw):
        return ""
    s = re.sub(r"[.,]", " ", str(raw).upper())
    s = LEGAL_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def collapse_ws(raw):
    return "" if is_blank(raw) else re.sub(r"\s+", " ", str(raw).strip())


def none_if_na(series):
    return series.astype(object).where(series.notna(), None)
