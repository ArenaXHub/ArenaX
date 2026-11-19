#!/usr/bin/env python3
"""Build the SiteBook demo data from two "Daily Manhours Report" Excel registers.

Usage:
    py -I sitebook/tools/build_demo_data.py <register.xlsx> [<register.xlsx> ...] \
        --out sitebook/data/sitebook-demo.json [--inline sitebook/index.html]

Each workbook is one site. Monthly labour sheets (e.g. "FEB-26") hold one row per
worker with hours per date (8 h = 1 day), weekly pocket-money (kharchi) + mess
columns, advance, dues, carried-forward amount, travel, rate, payment and net.
Sheets ending in "C" (e.g. "FEB-26 C") are the billing to the principal company,
per designation, in day-units. An optional "EXPENSES" sheet summarises months.

The script never reads the EMP/AADHAR column (it is empty in these registers and
must stay out of the demo). No phone numbers exist in the registers.

With --mask (the public build) worker names become first name + initial and
free-text remarks and receipt notes are dropped; supervisor and site names and
every number stay. --private-html writes the real-name page outside the repo.

Output: one JSON with sites, months, workers, daily hours, weekly kharchi, dues,
rates, billing, receipts, expenses and the derived numbers the demo page shows
(daily wages, daily billing, daily margin, monthly billed vs wages, rate history).
With --inline the JSON is written into the page between the markers
<!--SITEBOOK-DATA--> ... <!--/SITEBOOK-DATA--> as a JSON script tag.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl is required: py -m pip install openpyxl")

DAY_HOURS = 8.0
CODES = {
    "A": "absent",
    "L": "left",
    "PS1": "moved",
    "PS2": "moved",
    "PS3": "moved",
    "BH": "other",
    "MH": "other",
    "BHU": "other",
    "-": "none",
}
WEEKDAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


# ----------------------------------------------------------------- helpers
def title_case(name: str) -> str:
    """'RAMESH KUMAR YADAV' -> 'Ramesh Kumar Yadav' (keeps digits)."""
    parts = []
    for w in re.split(r"(\s+)", name.strip()):
        if not w.strip():
            parts.append(w)
        elif re.fullmatch(r"PS-?\d", w, re.I):
            parts.append(w.upper())
        else:
            parts.append(w[:1].upper() + w[1:].lower())
    return "".join(parts)


def is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def num(v, default=0.0) -> float:
    return float(v) if is_num(v) else default


def r2(v: float) -> float:
    return round(v + 0.0, 2)


def cell_code(v):
    """A grid cell: number of hours, a code, or empty."""
    if v is None or v == "":
        return None
    if is_num(v):
        return float(v)
    s = str(v).strip().upper()
    return CODES.get(s, "other"), s


def parse_receipt_date(v, month: dt.date):
    """Receipt dates come as datetimes (sometimes day/month swapped) or 'd-m-yy' strings."""
    if isinstance(v, dt.datetime):
        d = v.date()
        if d.month != month.month and d.day == month.month and d.month <= 31:
            # Excel read 'D-M' as 'M-D': swap back
            try:
                d = dt.date(d.year, d.day, d.month)
            except ValueError:
                pass
        return d.isoformat()
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\s*", v)
        if m:
            dd, mm, yy = (int(x) for x in m.groups())
            if yy < 100:
                yy += 2000
            try:
                return dt.date(yy, mm, dd).isoformat()
            except ValueError:
                return None
    return None


def find_label_cols(ws, row: int) -> dict:
    """Map every string label in a header row to the list of its column indexes."""
    out: dict[str, list[int]] = {}
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row, c).value
        if isinstance(v, str):
            key = re.sub(r"\s+", " ", v.strip().upper())
            out.setdefault(key, []).append(c)
    return out


def right_value(ws, row: int, col: int, span: int = 8):
    """First numeric cell to the right of a label (same row)."""
    for c in range(col + 1, col + 1 + span):
        v = ws.cell(row, c).value
        if is_num(v):
            return float(v)
    return None


# ------------------------------------------------------------- sheet parsers
def sheet_meta(ws):
    site = sup = month = None
    for r in range(1, 7):
        for c in range(1, min(ws.max_column, 12) + 1):
            v = ws.cell(r, c).value
            if isinstance(v, str):
                k = v.strip().lower()
                nxt = ws.cell(r, c + 1).value
                if k.startswith("name of site") and isinstance(nxt, str):
                    site = title_case(nxt)
                elif k.startswith("name of supervisor") and isinstance(nxt, str):
                    sup = title_case(nxt)
                elif k.startswith("for the month") and isinstance(nxt, dt.datetime):
                    month = nxt.date().replace(day=1)
    return site, sup, month


def date_columns(ws, header_row: int, stop_col: int) -> list[tuple[int, str]]:
    cols = []
    for c in range(1, stop_col):
        v = ws.cell(header_row, c).value
        if isinstance(v, dt.datetime):
            cols.append((c, v.date().isoformat()))
    return cols


def parse_labour_sheet(ws):
    site, sup, month = sheet_meta(ws)
    if month is None:
        return None
    labels = find_label_cols(ws, 6)
    name_cols = labels.get("NAME OF EMPLOYEE", [])
    if not name_cols or "TOTAL DAY" not in labels:
        return None
    c_name = name_cols[0]
    c_desig = labels.get("DESIGNATION", [None])[0]
    c_status = labels.get("STATUS", [None])[0]
    c_total = labels["TOTAL DAY"][0]
    dcols = date_columns(ws, 7, c_total)
    # right block
    week_cols = []  # (week_ending_iso, pocket_col, mess_col)
    for c in range(c_total + 1, ws.max_column + 1):
        v = ws.cell(6, c).value
        if isinstance(v, dt.datetime):
            week_cols.append((v.date().isoformat(), c, c + 1))
    c_tot_pm = labels.get("TOTAL POCKET & MESS", [None])[0]
    c_adv = labels.get("ADVANCE", [None])[0]
    c_dues = labels.get("DUES AMOUNT", [None])[0]
    c_pre = labels.get("PRE AMOUNT", [None])[0]
    ta_cols = labels.get("T.A", [])
    c_ta_cr = ta_cols[0] if ta_cols else None
    c_ta_dr = ta_cols[1] if len(ta_cols) > 1 else None
    c_rate = labels.get("RATE", [None])[0]
    c_pay = labels.get("PAYMENT", [None])[0]
    c_net = labels.get("NET PAYMENT", [None])[0]
    c_rem = labels.get("REMARKS", [None])[0]
    days_in_month = calendar.monthrange(month.year, month.month)[1]

    workers = []
    total_row = None
    for r in range(8, ws.max_row + 1):
        a = ws.cell(r, 1).value
        if isinstance(a, str) and a.strip().upper().startswith("TOTAL"):
            total_row = r
            break
        raw_name = ws.cell(r, c_name).value
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        name = title_case(raw_name)
        hours = []  # aligned with `dates`: hours (number), a code string (A, L, PS1, MH, bhu ...) or null
        for c, iso in dcols:
            cv = cell_code(ws.cell(r, c).value)
            if cv is None:
                hours.append(None)
            elif isinstance(cv, float):
                hours.append(r2(cv))
            else:
                hours.append(cv[1])
        rate = num(ws.cell(r, c_rate).value) if c_rate else 0.0
        payment = num(ws.cell(r, c_pay).value) if c_pay else 0.0
        fixed = rate > 0 and abs(rate - round(rate)) > 0.01  # monthly salary / days
        weeks = []
        for iso, pc, mc in week_cols:
            weeks.append({
                "week_ending": iso,
                "pocket": r2(num(ws.cell(r, pc).value)),
                "mess": r2(num(ws.cell(r, mc).value)),
            })
        hours_sum = sum(v for v in hours if is_num(v))
        w = {
            "name": name,
            "designation": title_case(ws.cell(r, c_desig).value) if c_desig and isinstance(ws.cell(r, c_desig).value, str) else None,
            "status": (ws.cell(r, c_status).value or "").strip().title() if c_status and isinstance(ws.cell(r, c_status).value, str) else None,
            "hours": hours,
            "total_days": r2(num(ws.cell(r, c_total).value, hours_sum / DAY_HOURS)),
            "weeks": weeks,
            "pocket_mess_total": r2(num(ws.cell(r, c_tot_pm).value)) if c_tot_pm else 0.0,
            "advance": r2(num(ws.cell(r, c_adv).value)) if c_adv else 0.0,
            "dues": r2(num(ws.cell(r, c_dues).value)) if c_dues else 0.0,
            "pre_amount": r2(num(ws.cell(r, c_pre).value)) if c_pre else 0.0,
            "ta_credit": r2(num(ws.cell(r, c_ta_cr).value)) if c_ta_cr else 0.0,
            "ta_debit": r2(num(ws.cell(r, c_ta_dr).value)) if c_ta_dr else 0.0,
            "rate": r2(rate),
            "pay_type": "fixed_monthly" if fixed else "daily",
            "monthly_salary": r2(payment) if fixed else None,
            "payment": r2(payment),
            "net_payment": r2(num(ws.cell(r, c_net).value)) if c_net else 0.0,
            "remarks": (str(ws.cell(r, c_rem).value).strip() if c_rem and ws.cell(r, c_rem).value is not None else ""),
        }
        workers.append(w)

    # receipts and expense block below the grid
    receipts, expenses = [], {}
    start = (total_row or 8) + 1
    for r in range(start, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            v = ws.cell(r, c).value
            if not isinstance(v, str):
                continue
            k = re.sub(r"\s+", " ", v.strip().upper())
            if k == "DATE" and isinstance(ws.cell(r, c + 1).value, str) and ws.cell(r, c + 1).value.strip().upper() == "QIPL":
                rr = r + 1
                blank = 0
                while rr <= ws.max_row and blank < 3:
                    dv, av, nv = ws.cell(rr, c).value, ws.cell(rr, c + 1).value, ws.cell(rr, c + 2).value
                    if is_num(av) and av != 0:
                        receipts.append({
                            "date": parse_receipt_date(dv, month),
                            "amount": r2(float(av)),
                            "note": (nv.strip() if isinstance(nv, str) else ""),
                        })
                        blank = 0
                    elif dv is None and av is None:
                        blank += 1
                    rr += 1
            elif k in ("TOTAL EXPENSE", "EXTRA EXPENSES", "MESS", "EXPENCE IN HAND", "EXPENSE IN HAND", "PREVIOUS MONTH", "GST"):
                val = right_value(ws, r, c)
                if val is None and k == "PREVIOUS MONTH":
                    val = right_value(ws, r + 1, c) if r + 1 <= ws.max_row else None
                if val is not None:
                    key = {"TOTAL EXPENSE": "total_expense", "EXTRA EXPENSES": "extra_expenses", "MESS": "mess",
                           "EXPENCE IN HAND": "expense_in_hand", "EXPENSE IN HAND": "expense_in_hand",
                           "PREVIOUS MONTH": "previous_month", "GST": "gst"}[k]
                    expenses.setdefault(key, r2(val))
    receipts = [x for x in receipts if x["date"]]
    receipts.sort(key=lambda x: x["date"])

    totals = {}
    if total_row:
        totals = {
            "total_days": r2(num(ws.cell(total_row, c_total).value)),
            "pocket_mess_total": r2(num(ws.cell(total_row, c_tot_pm).value)) if c_tot_pm else 0.0,
            "advance": r2(num(ws.cell(total_row, c_adv).value)) if c_adv else 0.0,
            "dues": r2(num(ws.cell(total_row, c_dues).value)) if c_dues else 0.0,
            "payment": r2(num(ws.cell(total_row, c_pay).value)) if c_pay else 0.0,
            "net_payment": r2(num(ws.cell(total_row, c_net).value)) if c_net else 0.0,
        }
    return {
        "kind": "labour",
        "sheet": ws.title,
        "site": site,
        "supervisor": sup,
        "month": month.isoformat()[:7],
        "days_in_month": days_in_month,
        "dates": [iso for _, iso in dcols],
        "week_endings": [iso for iso, _, _ in week_cols],
        "workers": workers,
        "register_totals": totals,
        "receipts": receipts,
        "receipts_total": r2(sum(x["amount"] for x in receipts)),
        "expenses": expenses,
    }


def parse_billing_sheet(ws):
    site, sup, month = sheet_meta(ws)
    if month is None:
        return None
    labels = find_label_cols(ws, 6)
    if "TOTAL DAY" not in labels or "RATE" not in labels:
        return None
    c_name = labels.get("NAME OF EMPLOYEE", [None])[0]
    c_desig = labels.get("DESIGNATION", [None])[0]
    c_total = labels["TOTAL DAY"][0]
    c_rate = labels["RATE"][0]
    c_pay = labels.get("PAYMENT", [None])[0]
    dcols = date_columns(ws, 7, c_total)
    rows, total_row = [], None
    for r in range(8, ws.max_row + 1):
        a = ws.cell(r, 1).value
        if isinstance(a, str) and a.strip().upper().startswith("TOTAL"):
            total_row = r
            break
        raw = ws.cell(r, c_name).value if c_name else None
        if not isinstance(raw, str) or not raw.strip():
            continue
        units = []  # aligned with `dates`; null where the sheet has no number
        for c, iso in dcols:
            v = ws.cell(r, c).value
            units.append(round(float(v), 4) if is_num(v) else None)
        rows.append({
            "name": title_case(raw),
            "designation": title_case(ws.cell(r, c_desig).value) if c_desig and isinstance(ws.cell(r, c_desig).value, str) else None,
            "units": units,
            "total_units": r2(num(ws.cell(r, c_total).value, sum(u for u in units if u))),
            "rate": r2(num(ws.cell(r, c_rate).value)),
            "payment": r2(num(ws.cell(r, c_pay).value)) if c_pay else 0.0,
        })
    gst = total_incl = None
    billed_total = 0.0
    if total_row:
        billed_total = r2(num(ws.cell(total_row, c_pay).value)) if c_pay else 0.0
        for r in range(total_row + 1, min(ws.max_row, total_row + 6) + 1):
            for c in range(1, ws.max_column + 1):
                v = ws.cell(r, c).value
                if isinstance(v, str) and v.strip().upper() == "GST":
                    gst = right_value(ws, r, c, 3)
                elif isinstance(v, str) and v.strip().upper() == "TOTAL":
                    total_incl = right_value(ws, r, c, 3)
    client_rates = {}
    for row in rows:
        if row["designation"] and row["rate"]:
            client_rates.setdefault(row["designation"], row["rate"])
    return {
        "kind": "billing",
        "sheet": ws.title,
        "site": site,
        "supervisor": sup,
        "month": month.isoformat()[:7],
        "dates": [iso for _, iso in dcols],
        "rows": rows,
        "client_rates": client_rates,
        "billed_total": billed_total,
        "gst": r2(gst) if gst is not None else None,
        "billed_with_gst": r2(total_incl) if total_incl is not None else None,
    }


def parse_expenses_sheet(ws):
    out = []
    for r in range(3, ws.max_row + 1):
        m = ws.cell(r, 2).value
        if not isinstance(m, dt.datetime):
            continue
        out.append({
            "month": m.date().isoformat()[:7],
            "payment": r2(num(ws.cell(r, 3).value)),
            "mess": r2(num(ws.cell(r, 4).value)),
            "extra": r2(num(ws.cell(r, 5).value)),
            "ta_credit": r2(num(ws.cell(r, 6).value)),
            "ta_debit": r2(num(ws.cell(r, 7).value)),
            "due": r2(num(ws.cell(r, 8).value)),
            "misc": r2(num(ws.cell(r, 9).value)),
            "total": r2(num(ws.cell(r, 10).value)),
            "recovery": r2(num(ws.cell(r, 11).value)),
        })
    return out


# ------------------------------------------------------------------ derive
def derive_month(lab: dict, bill: dict | None) -> dict:
    """Daily wages, billing and margin plus worker-level summaries for one month."""
    dates = lab["dates"]
    wages = {d: 0.0 for d in dates}
    present = {d: 0 for d in dates}
    for w in lab["workers"]:
        for d, h in zip(dates, w["hours"]):
            if is_num(h) and h > 0:
                present[d] += 1
            if w["pay_type"] == "daily" and is_num(h):
                wages[d] += h / DAY_HOURS * w["rate"]
    billing = {d: 0.0 for d in dates}
    if bill:
        bdates = bill["dates"]
        for row in bill["rows"]:
            for d, u in zip(bdates, row["units"]):
                if u and d in billing:
                    billing[d] += u * row["rate"]
    daily = [{
        "date": d,
        "wages": r2(wages[d]),
        "billed": r2(billing[d]),
        "margin": r2(billing[d] - wages[d]),
        "present": present[d],
    } for d in dates]
    fixed_salaries = r2(sum(w["monthly_salary"] or 0 for w in lab["workers"] if w["pay_type"] == "fixed_monthly"))
    wages_register = lab["register_totals"].get("payment") or r2(sum(w["payment"] for w in lab["workers"]))
    billed = bill["billed_total"] if bill else None
    return {
        "daily": daily,
        "wages_variable": r2(sum(wages.values())),
        "fixed_salaries": fixed_salaries,
        "wages_register": r2(wages_register),
        "billed": billed,
        "margin": r2(billed - wages_register) if billed is not None else None,
        "margin_pct": r2((billed - wages_register) / billed * 100) if billed else None,
        "active_workers": sum(1 for w in lab["workers"] if any(is_num(h) and h > 0 for h in w["hours"])),
        "worker_rows": len(lab["workers"]),
    }


def rate_history(months: list[dict]) -> dict:
    """Per worker: [(month, rate)] and the changes between consecutive months."""
    seen: dict[str, list] = {}
    for m in sorted(months, key=lambda x: x["month"]):
        for w in m["workers"]:
            if w["pay_type"] != "daily" or not w["rate"]:
                continue
            seen.setdefault(w["name"], []).append({"month": m["month"], "rate": w["rate"]})
    out = {}
    for name, lst in seen.items():
        changes = []
        for a, b in zip(lst, lst[1:]):
            if a["rate"] != b["rate"]:
                changes.append({"from": a["rate"], "to": b["rate"], "effective_from": b["month"] + "-01"})
        out[name] = {"rates": lst, "changes": changes}
    return out


# -------------------------------------------------------------------- main
def build(paths: list[Path]) -> dict:
    sites = []
    for p in paths:
        wb = openpyxl.load_workbook(p, data_only=True)
        labour, billing, expenses = [], [], []
        for ws in wb.worksheets:
            t = ws.title.strip().upper()
            if t == "EXPENSES":
                expenses = parse_expenses_sheet(ws)
            elif re.search(r"[\s-]C$", t):
                b = parse_billing_sheet(ws)
                if b:
                    billing.append(b)
            else:
                l = parse_labour_sheet(ws)
                if l:
                    labour.append(l)
        labour.sort(key=lambda x: x["month"])
        billing.sort(key=lambda x: x["month"])
        bill_by_month = {b["month"]: b for b in billing}
        site_name = labour[0]["site"] if labour else p.stem
        supervisor = labour[0]["supervisor"] if labour else None
        months = []
        for l in labour:
            b = bill_by_month.get(l["month"])
            d = derive_month(l, b)
            months.append({**l, "billing": b, "derived": d})
        principal = None
        for ws in wb.worksheets:
            v = ws.cell(1, 3).value
            if isinstance(v, str) and v.strip():
                principal = "Quartzite Infrastructure Private Limited" if v.upper().startswith("QUARTZITE") else title_case(v)
                break
        client_rates = {}
        for b in billing:
            for k, v in b["client_rates"].items():
                client_rates.setdefault(k, v)
        sites.append({
            "id": re.sub(r"[^a-z0-9]+", "-", site_name.lower()).strip("-"),
            "name": site_name,
            "supervisor": supervisor,
            "principal": principal,
            "source_file": p.name,
            "months": months,
            "billing_only_months": [b for b in billing if b["month"] not in {l["month"] for l in labour}],
            "client_rates": client_rates,
            "expenses_sheet": expenses,
            "rate_history": rate_history(labour),
            "summary": [{
                "month": m["month"],
                "workers": m["derived"]["worker_rows"],
                "active_workers": m["derived"]["active_workers"],
                "days": m["register_totals"].get("total_days"),
                "wages": m["derived"]["wages_register"],
                "billed": m["derived"]["billed"],
                "margin": m["derived"]["margin"],
                "margin_pct": m["derived"]["margin_pct"],
                "receipts": m["receipts_total"],
                "advances": m["register_totals"].get("advance"),
                "dues": m["register_totals"].get("dues"),
            } for m in months],
        })
    return {
        "generated": dt.date.today().isoformat(),
        "format": "Daily Manhours Report (8 h = 1 day; billing sheets in day-units)",
        "codes": {"A": "absent", "L": "left the site", "PS1/PS2/PS3": "moved to another site", "BH/MH/bhu": "other (to confirm)"},
        "sites": sites,
    }


def slim_for_inline(data: dict, keep_months: int) -> dict:
    """Keep full daily detail for the last `keep_months` months of each site; summaries stay complete."""
    out = json.loads(json.dumps(data))
    for s in out["sites"]:
        s["months"] = s["months"][-keep_months:]
    return out


def mask_name(name: str) -> str:
    """'Ramesh Kumar Yadav' -> 'Ramesh K.'; a trailing number is kept ('Ramesh Kumar 2' -> 'Ramesh K. 2')."""
    parts = name.split()
    if len(parts) < 2:
        return name
    suffix = ""
    if re.fullmatch(r"\d+", parts[-1]):
        suffix = " " + parts[-1]
        parts = parts[:-1]
    if len(parts) < 2:
        return parts[0] + suffix
    return f"{parts[0]} {parts[1][0].upper()}.{suffix}"


def mask_names(data: dict) -> dict:
    """Public build: worker names become first name + initial; supervisor and site names stay;
    free-text remarks and receipt notes (which name people) are dropped. Numbers are untouched."""
    out = json.loads(json.dumps(data))
    for site in out["sites"]:
        keep = {site["supervisor"]}
        mapping: dict[str, str] = {}
        used: set[str] = set()

        def m(name: str) -> str:
            if name in keep:
                return name
            if name not in mapping:
                base = mask_name(name)
                cand, n = base, 2
                while cand in used:
                    cand = f"{base} {n}"
                    n += 1
                used.add(cand)
                mapping[name] = cand
            return mapping[name]

        for month in site["months"] + site["billing_only_months"]:
            for w in month.get("workers", []):
                w["name"] = m(w["name"])
                w["remarks"] = ""
            for r in month.get("receipts", []):
                r["note"] = ""
            bill = month.get("billing")
            for row in (bill["rows"] if bill else month.get("rows", [])):
                row["name"] = m(row["name"])
        site["rate_history"] = {m(k): v for k, v in site["rate_history"].items()}
        site["name_policy"] = "worker names shortened to first name + initial"
    return out


def embed_fonts(html: str, base: Path) -> str:
    """Private, self-contained build: replace url(../assets/fonts/x.woff2) with data URIs."""
    import base64

    def repl(mt):
        rel = mt.group(1)
        f = (base / rel).resolve()
        if not f.exists():
            return mt.group(0)
        b64 = base64.b64encode(f.read_bytes()).decode()
        return f"url(data:font/woff2;base64,{b64})"

    html = re.sub(r"url\((\.\./assets/fonts/[^)]+)\)", repl, html)
    html = re.sub(r"<link rel=\"preload\"[^>]*>\n", "", html)
    fav = base / "assets/favicon.svg"
    if fav.exists():
        html = html.replace('href="assets/favicon.svg" type="image/svg+xml"', 'href="data:image/svg+xml;base64,' + base64.b64encode(fav.read_bytes()).decode() + '" type="image/svg+xml"')
    return html


def inline_into(html_path: Path, data: dict, keep_months: int = 5) -> None:
    data = slim_for_inline(data, keep_months)
    html = html_path.read_text(encoding="utf-8")
    start, end = "<!--SITEBOOK-DATA-->", "<!--/SITEBOOK-DATA-->"
    i, j = html.find(start), html.find(end)
    if i < 0 or j < 0:
        sys.exit(f"markers not found in {html_path}")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new = html[: i + len(start)] + '\n<script id="sitebook-data" type="application/json">' + blob + "</script>\n" + html[j:]
    html_path.write_text(new, encoding="utf-8")


def write_private(template: Path, out: Path, data: dict, keep_months: int) -> None:
    """One self-contained HTML with real names and embedded fonts, written outside the repo."""
    html = template.read_text(encoding="utf-8")
    start, end = "<!--SITEBOOK-DATA-->", "<!--/SITEBOOK-DATA-->"
    i, j = html.find(start), html.find(end)
    blob = json.dumps(slim_for_inline(data, keep_months), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html[: i + len(start)] + '\n<script id="sitebook-data" type="application/json">' + blob + "</script>\n" + html[j:]
    html = html.replace('data-build="public"', 'data-build="private"', 1)
    html = embed_fonts(html, template.parent)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"private build written to {out} ({out.stat().st_size // 1024} KB, real names, fonts embedded; never commit)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--inline", type=Path, help="HTML page to inline the JSON into")
    ap.add_argument("--inline-months", type=int, default=5, help="months of daily detail per site to inline (default 5)")
    ap.add_argument("--mask", action="store_true", help="public build: worker names as first name + initial, remarks and receipt notes dropped")
    ap.add_argument("--private-html", type=Path, help="also write a self-contained page with REAL names to this path (outside the repo)")
    a = ap.parse_args()
    real = build(a.xlsx)
    data = mask_names(real) if a.mask else real
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out} ({a.out.stat().st_size // 1024} KB)")
    for s in data["sites"]:
        print(f"\n{s['name']} · supervisor {s['supervisor']} · {len(s['months'])} months")
        for m in s["summary"]:
            b = f"{m['billed']:>12,.0f}" if m["billed"] is not None else f"{'-':>12}"
            print(f"  {m['month']}  workers {m['workers']:>2} (active {m['active_workers']:>2})  wages {m['wages']:>12,.0f}  billed {b}  receipts {m['receipts']:>10,.0f}")
    if a.inline:
        inline_into(a.inline, data, a.inline_months)
        print(f"inlined into {a.inline} ({'masked' if a.mask else 'REAL'} names)")
    if a.private_html:
        if not a.inline:
            sys.exit("--private-html needs --inline (the page is the template)")
        write_private(a.inline, a.private_html, real, a.inline_months)


if __name__ == "__main__":
    main()
