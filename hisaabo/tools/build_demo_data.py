#!/usr/bin/env python3
"""Build the Hisaabo demo data from two "Daily Manhours Report" Excel registers.

Usage:
    py -I hisaabo/tools/build_demo_data.py <register.xlsx> [<register.xlsx> ...] \
        --out hisaabo/data/hisaabo-demo.json [--inline hisaabo/index.html]

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
(daily wages, daily billing, daily bachat (billed minus wages), monthly billed vs wages, rate history).
With --inline the JSON is written into the page between the markers
<!--HISAABO-DATA--> ... <!--/HISAABO-DATA--> as a JSON script tag.
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
            if k == "DATE" and isinstance(ws.cell(r, c + 1).value, str) and ws.cell(r, c + 1).value.strip().upper() in LOCAL["receipt_headers"]:
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
        # Under the PAYMENT total the register lists the month's other costs (EXTRA, the
        # foreman's MESS) and then the month total. Take that total when present.
        pay_total = totals["payment"]
        below = []
        for r in range(total_row + 1, min(ws.max_row, total_row + 6) + 1):
            v = ws.cell(r, c_pay).value if c_pay else None
            if is_num(v):
                below.append(float(v))
        cost_total = None
        for i, v in enumerate(below):
            if pay_total and v >= pay_total and abs(v - (pay_total + sum(below[:i]))) < 1.0:
                cost_total = v
                break
        if cost_total is not None:
            totals["extra_costs"] = r2(cost_total - pay_total)
        else:
            small = []
            for v in below:
                if v <= 0 or (pay_total and v >= 0.2 * pay_total):
                    break
                small.append(v)
            totals["extra_costs"] = r2(sum(small)) if small else None
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
    """Daily wages, billing and bachat plus worker-level summaries for one month."""
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
    absent = {d: 0 for d in dates}
    for w in lab["workers"]:
        for d, h in zip(dates, w["hours"]):
            if h == "A":
                absent[d] += 1
    daily = [{
        "date": d,
        "wages": r2(wages[d]),
        "billed": r2(billing[d]),
        "bachat": r2(billing[d] - wages[d]),
        "present": present[d],
        "absent": absent[d],
    } for d in dates]
    fixed_salaries = r2(sum(w["monthly_salary"] or 0 for w in lab["workers"] if w["pay_type"] == "fixed_monthly"))
    wages_register = lab["register_totals"].get("payment") or r2(sum(w["payment"] for w in lab["workers"]))
    billed = bill["billed_total"] if bill else None
    # contractor-side extra costs for the month: travel paid out (T.A debit) and the EXTRA EXPENSES line
    ta_debit = r2(sum(w["ta_debit"] for w in lab["workers"]))
    extra = r2(max(0.0, lab["expenses"].get("extra_expenses", 0.0)))
    reg_extra = lab["register_totals"].get("extra_costs")
    extras = r2(reg_extra if reg_extra is not None else extra)
    days_marked = sum(1 for d in daily if d["present"] > 0)
    owed_rows = [w for w in lab["workers"] if w["net_payment"] < 0]
    left = sum(1 for w in lab["workers"] if any(h == "L" for h in w["hours"]))
    kharchi_mess = lab["register_totals"].get("pocket_mess_total") or r2(sum(w["pocket_mess_total"] for w in lab["workers"]))
    bachat = r2(billed - wages_register - extras) if (billed is not None and wages_register > 0) else None
    return {
        "extras": extras,
        "days_marked": days_marked,
        "ta_debit": ta_debit,
        "extra_expenses": extra,
        "kharchi_mess": r2(kharchi_mess),
        "cash_to_workers": r2(wages_register - kharchi_mess),
        "owed_by_workers": r2(-sum(w["net_payment"] for w in owed_rows)),
        "owed_count": len(owed_rows),
        "left_count": left,
        "bachat": bachat,
        "bachat_pct": r2(bachat / billed * 100) if (billed and bachat is not None) else None,
        "daily": daily,
        "wages_variable": r2(sum(wages.values())),
        "fixed_salaries": fixed_salaries,
        "wages_register": r2(wages_register),
        "billed": billed,
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
                principal = next((full for pre, full in LOCAL["principal_names"].items() if v.upper().startswith(pre.upper())), title_case(v))
                break
        client_rates = {}
        for b in billing:
            for k, v in b["client_rates"].items():
                client_rates.setdefault(k, v)
        slot = site_slot(p, len(sites))
        sites.append({
            "id": slot["id"],
            "name": site_name,
            "label": slot["real_label"] or site_name,
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
                "bachat": m["derived"]["bachat"],
                "bachat_pct": m["derived"]["bachat_pct"],
                "extras": m["derived"]["extras"],
                "days_marked": m["derived"]["days_marked"],
                "kharchi_mess": m["derived"]["kharchi_mess"],
                "receipts": m["receipts_total"],
                "advances": m["register_totals"].get("advance"),
                "dues": m["register_totals"].get("dues"),
            } for m in months],
        })
    sites.sort(key=lambda x: x["id"])
    return {
        "generated": dt.date.today().isoformat(),
        "format": "Daily Manhours Report (8 h = 1 day; billing sheets in day-units)",
        "codes": {"A": "absent", "L": "left the site", "PS1/PS2/PS3": "moved to another site", "BH/MH/bhu": "other (to confirm)"},
        "sites": sites,
    }


def slim_for_inline(data: dict, keep_months: int) -> dict:
    """Keep full daily detail for the last `keep_months` months of each site; summaries stay complete."""
    out = json.loads(json.dumps(data))
    keep_worker = ("name", "hours", "total_days", "weeks", "pocket_mess_total", "advance", "rate", "pay_type", "monthly_salary", "payment", "net_payment")
    keep_month = ("month", "dates", "week_endings", "days_in_month", "workers", "register_totals", "receipts", "receipts_total", "derived")
    for s in out["sites"]:
        # months with labour entries only, newest `keep_months`
        s["months"] = [m for m in s["months"] if m["derived"]["active_workers"] > 0][-keep_months:]
        for k in ("expenses_sheet", "billing_only_months", "source_file", "client_rates", "principal"):
            s.pop(k, None)
        s["rate_history"] = {k: {"changes": v["changes"]} for k, v in s["rate_history"].items() if v["changes"]}
        for i, m in enumerate(s["months"]):
            s["months"][i] = m = {k: v for k, v in m.items() if k in keep_month}
            m["workers"] = [{k: v for k, v in w.items() if k in keep_worker} for w in m["workers"]]
            for r in m["receipts"]:
                r.pop("note", None)
    return _compact(out)


def _compact(o):
    """Whole-number floats as ints (12.0 -> 12) to keep the inlined JSON small."""
    if isinstance(o, float):
        return int(o) if o.is_integer() else o
    if isinstance(o, list):
        return [_compact(x) for x in o]
    if isinstance(o, dict):
        return {k: _compact(v) for k, v in o.items()}
    return o


# ------------------------------------------------------- site slots, fictional build
# Every build uses the same generic site ids, so the page config never names a real site.
# Real registers map to a slot by file name; the fictional build (public) replaces names and shifts money.
# Real site labels, receipt headers and the client's name live in raw/local.json (git-ignored, like the registers):
#   {"slots": [{"match": "<file-name part>", "id": "site-a", "real_label": "<short real name>"}, ...],
#    "receipt_headers": ["<header text above the client receipts>"], "principal_names": {"<prefix>": "<full name>"}}
# Without it, sites take site-a, site-b ... in input order and the receipts header is read as "RECEIPTS".
FICT_SITES = {"site-a": "Site A \u2013 Ahmedabad", "site-b": "Site B \u2013 Pune"}


def _load_local() -> dict:
    f = Path(__file__).resolve().parent.parent / "raw" / "local.json"
    cfg = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    cfg.setdefault("slots", [])
    cfg["receipt_headers"] = {h.upper() for h in cfg.get("receipt_headers", ["RECEIPTS"])}
    cfg.setdefault("principal_names", {})
    return cfg


LOCAL = _load_local()
FICT_COMPANY = "Shree Ganesh Constructions"
FICT_CLIENT = "ABC Infra Ltd"
FICT_SUPERVISORS = {"site-a": "Mahesh Chauhan", "site-b": "Vinod Patil"}
FIRST = ("Aakash Ajay Amit Anil Arjun Ashok Babulal Balram Bharat Bhola Chandan Deepak Dharam Dinesh Ganesh Gopal Hari Harish "
         "Jagdish Jeevan Kailash Kamal Kishan Lakhan Laxman Madan Manoj Mohan Mukesh Naresh Nitin Pankaj Pawan Prakash Pramod "
         "Rajesh Rakesh Ramesh Ravi Sachin Sanjay Santosh Satish Shankar Shyam Sohan Sunil Suresh Tarun Umesh Vijay Vikram Yogesh").split()
LAST = ("Bhagat Chavan Das Gaikwad Jadhav Kale Kumar Mahato Mandal Meena Mishra More Nayak Pawar Prasad Rathod Rawat Sahu "
        "Shinde Singh Solanki Thakur Verma Yadav").split()
MONEY_W = ("rate", "payment", "monthly_salary", "net_payment", "pocket_mess_total", "advance", "dues", "pre_amount", "ta_credit", "ta_debit")
MONEY_T = ("pocket_mess_total", "advance", "dues", "payment", "net_payment", "extra_costs")
DESIG_ROWS = ("forman", "foreman", "carpenter", "fitter", "helper", "total")


def site_slot(path: Path, index: int) -> dict:
    stem = path.stem.lower()
    for sl in LOCAL["slots"]:
        if sl["match"].lower() in stem:
            return {"id": sl["id"], "real_label": sl.get("real_label")}
    return {"id": "site-" + "abcdefghij"[index], "real_label": None}


def r10(v):
    """Nearest Rs 10 (KP, 20 Nov 2026: shifted daily rates look like real ones)."""
    return float(round(v / 10) * 10) if is_num(v) else v


def _rebill(bill: dict) -> float:
    """Client billing after rounding: rate per day-unit to Rs 10, row and month totals from units x rate, GST in proportion."""
    old_total = bill.get("billed_total") or 0
    for row in bill["rows"]:
        row["rate"] = r10(row["rate"])
        row["payment"] = float(round(sum(u for u in row["units"] if u) * row["rate"]))
    bill["client_rates"] = {k: r10(v) for k, v in bill["client_rates"].items()}
    new_total = float(round(sum(row["payment"] for row in bill["rows"])))
    if old_total:
        for k in ("gst", "billed_with_gst"):
            if is_num(bill.get(k)):
                bill[k] = float(round(bill[k] * new_total / old_total))
    bill["billed_total"] = new_total
    return new_total


def round_site_rates(site: dict) -> None:
    """Round the shifted daily rates to the nearest Rs 10, then recompute payments, nets, totals, daily wages, billing and margin."""
    for b in site["billing_only_months"]:
        _rebill(b)
    for m in site["months"]:
        delta = 0.0
        for w in m.get("workers", []):
            if w.get("pay_type") == "daily" and is_num(w.get("rate")) and w["rate"]:
                new = r10(w["rate"])
                if new != w["rate"]:
                    newpay = float(round(w["payment"] * new / w["rate"]))
                    dp = newpay - w["payment"]
                    w["payment"], w["net_payment"], w["rate"] = newpay, float(round(w["net_payment"] + dp)), new
                    delta += dp
        rt = m.get("register_totals", {})
        for k in ("payment", "net_payment"):
            if is_num(rt.get(k)):
                rt[k] = float(round(rt[k] + delta))
        bill = m.get("billing")
        billed = _rebill(bill) if bill else None
        d = m.get("derived")
        if not d:
            continue
        idx = {dd: i for i, dd in enumerate(m["dates"])}
        bidx = {dd: i for i, dd in enumerate(bill["dates"])} if bill else {}
        for x in d["daily"]:
            i = idx.get(x["date"])
            if i is not None:
                x["wages"] = r2(sum(w["hours"][i] / DAY_HOURS * w["rate"] for w in m["workers"] if w["pay_type"] == "daily" and is_num(w["hours"][i])))
            if bill:
                j = bidx.get(x["date"])
                x["billed"] = r2(sum((row["units"][j] or 0) * row["rate"] for row in bill["rows"])) if j is not None else 0.0
            x["bachat"] = r2(x["billed"] - x["wages"])
        d["wages_register"] = float(round(d["wages_register"] + delta))
        d["wages_variable"] = r2(sum(x["wages"] for x in d["daily"]))
        d["cash_to_workers"] = float(round(d["wages_register"] - d["kharchi_mess"]))
        owed = [w for w in m["workers"] if w["net_payment"] < 0]
        d["owed_by_workers"] = float(round(-sum(w["net_payment"] for w in owed)))
        d["owed_count"] = len(owed)
        if billed is not None:
            d["billed"] = billed
        if d.get("billed") is not None and d.get("bachat") is not None:
            d["bachat"] = float(round(d["billed"] - d["wages_register"] - d["extras"]))
            d["bachat_pct"] = r2(d["bachat"] / d["billed"] * 100) if d["billed"] else None


def fictionalize(data: dict, seed: int) -> dict:
    """Public build (KP, 20 Nov 2026): fictional company, client, sites, supervisors and workers, and every money
    amount shifted by one random factor per site (10-15 % up or down, drawn from `seed`). Money is scaled by the same
    factor everywhere in a site, so totals, nets and the profit split still add up; hours, day codes, dates and head-
    counts stay as in the registers so the register arithmetic (8 h = 1 day) holds. Remarks and receipt notes are dropped."""
    import random
    rng = random.Random(seed)
    out = json.loads(json.dumps(data))
    pool = [f"{a} {b}" for a in FIRST for b in LAST]
    rng.shuffle(pool)
    names: dict[str, str] = {}
    firsts: set[str] = set()
    # never hand out a fictional name that matches a real person in the registers (full pair or first name + initial)
    real_people = set()
    for site in data["sites"]:
        real_people.add(site.get("supervisor") or "")
        for m in site["months"] + site["billing_only_months"]:
            real_people.update(w["name"] for w in m.get("workers", []))
            real_people.update(r["name"] for r in ((m.get("billing") or {}).get("rows", []) + m.get("rows", [])))
    taken = set()
    for n in real_people:
        parts = n.split()
        if len(parts) >= 2:
            taken.add((parts[0].lower(), parts[1].lower()))
            taken.add((parts[0].lower(), parts[1][0].lower()))
    pool = [c for c in pool if (c.split()[0].lower(), c.split()[1].lower()) not in taken and (c.split()[0].lower(), c.split()[1][0].lower()) not in taken]

    def fname(real: str) -> str:
        if real not in names:
            cand = pool.pop()
            while cand.split()[0] in firsts and len(firsts) < len(FIRST):
                cand = pool.pop()
            firsts.add(cand.split()[0])
            names[real] = cand
        return names[real]

    def money(v, f, dec=0):
        if v is None or not is_num(v):
            return v
        return round(v * f, dec) if dec else float(round(v * f))

    out["codes"] = {"A": "absent", "L": "left the site", "TR1/TR2/TR3": "transferred to another site", "BH/MH/bhu": "other (to confirm)"}
    out["company"] = FICT_COMPANY
    out["name_policy"] = "fictional: company, client, sites and people; money shifted 10-15 % per site"
    out.pop("format", None)
    for site in out["sites"]:
        fict = FICT_SITES.get(site["id"], site["id"].replace("-", " ").title())
        f = (1 + rng.uniform(0.10, 0.15)) if rng.random() < 0.5 else (1 - rng.uniform(0.10, 0.15))
        f = round(f, 3)
        site["name"] = fict
        site["label"] = fict
        site["principal"] = FICT_CLIENT
        site["supervisor"] = FICT_SUPERVISORS.get(site["id"], "Site Supervisor")
        site["source_file"] = site["id"] + ".xlsx"
        site.pop("name_policy", None)
        for m in site["months"] + site["billing_only_months"]:
            m["site"] = site["name"]
            m["supervisor"] = site["supervisor"]
            m.pop("sheet", None)
            for w in m.get("workers", []):
                w["name"] = fname(w["name"])
                w["remarks"] = ""
                # transfer codes name the contractor's real sites (PS1, PS3 ...): shown as TR1, TR3 ...
                w["hours"] = [("TR" + h[2:]) if isinstance(h, str) and h.upper().startswith("PS") else h for h in w["hours"]]
                for k in MONEY_W:
                    w[k] = money(w.get(k), f, 2 if (k == "rate" and w.get("pay_type") != "daily") else 0)
                for wk in w.get("weeks", []):
                    wk["pocket"] = money(wk["pocket"], f)
                    wk["mess"] = money(wk["mess"], f)
            for k in MONEY_T:
                if k in m.get("register_totals", {}):
                    m["register_totals"][k] = money(m["register_totals"][k], f)
            for r in m.get("receipts", []):
                r["amount"] = money(r["amount"], f)
                r["note"] = ""
            if "receipts_total" in m:
                m["receipts_total"] = float(round(sum(r["amount"] for r in m["receipts"])))
            m["expenses"] = {k: money(v, f) for k, v in m.get("expenses", {}).items()}
            bills = [m["billing"]] if m.get("billing") else ([m] if m.get("kind") == "billing" else [])
            for b in bills:
                b["site"] = site["name"]
                b["supervisor"] = site["supervisor"]
                b.pop("sheet", None)
                for row in b["rows"]:
                    if not row["name"].lower().startswith(DESIG_ROWS):
                        row["name"] = fname(row["name"])
                    row["rate"] = money(row["rate"], f)
                    row["payment"] = money(row["payment"], f)
                b["client_rates"] = {k: money(v, f) for k, v in b["client_rates"].items()}
                for k in ("billed_total", "gst", "billed_with_gst"):
                    b[k] = money(b.get(k), f)
            if m.get("derived"):
                d = m["derived"]
                for k in ("extras", "ta_debit", "extra_expenses", "kharchi_mess", "cash_to_workers", "owed_by_workers", "bachat",
                          "wages_variable", "fixed_salaries", "wages_register", "billed"):
                    d[k] = money(d.get(k), f)
                for x in d["daily"]:
                    x["wages"] = money(x["wages"], f, 2)
                    x["billed"] = money(x["billed"], f, 2)
                    x["bachat"] = r2(x["billed"] - x["wages"])
                if d.get("billed") is not None and d.get("bachat") is not None:
                    d["bachat"] = float(round(d["billed"] - d["wages_register"] - d["extras"]))
                    d["bachat_pct"] = r2(d["bachat"] / d["billed"] * 100) if d["billed"] else None
        round_site_rates(site)
        site["client_rates"] = {k: r10(money(v, f)) for k, v in site["client_rates"].items()}
        site["expenses_sheet"] = [{k: (v if k == "month" else money(v, f)) for k, v in e.items()} for e in site["expenses_sheet"]]
        site["rate_history"] = {fname(k): {"rates": [{"month": r["month"], "rate": r10(money(r["rate"], f))} for r in v["rates"]],
                                            "changes": [{**c, "from": r10(money(c["from"], f)), "to": r10(money(c["to"], f))} for c in v["changes"] if r10(money(c["from"], f)) != r10(money(c["to"], f))]}
                                for k, v in site["rate_history"].items()}
        bym = {m["month"]: m for m in site["months"]}
        bonly = {b["month"]: b for b in site["billing_only_months"]}
        for srow in site["summary"]:
            m = bym.get(srow["month"])
            for k in ("wages", "billed", "bachat", "extras", "kharchi_mess", "receipts", "advances", "dues"):
                srow[k] = money(srow.get(k), f)
            if not m and srow["month"] in bonly:
                srow["billed"] = bonly[srow["month"]]["billed_total"]
            if m:
                d = m["derived"]
                srow.update(wages=d["wages_register"], billed=d["billed"], bachat=d["bachat"], bachat_pct=d["bachat_pct"],
                            extras=d["extras"], kharchi_mess=d["kharchi_mess"], receipts=m["receipts_total"])
        site["_shift"] = f
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
    """Public build: worker and supervisor names become first name + initial (KP, 19 Nov 2026: full names only in the
    private file); site names stay; free-text remarks and receipt notes (which name people) are dropped. Numbers are untouched."""
    out = json.loads(json.dumps(data))
    for site in out["sites"]:
        keep: set[str] = set()
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

        site["supervisor"] = m(site["supervisor"])  # first, so the supervisor keeps the plain short form
        for month in site["months"] + site["billing_only_months"]:
            if month.get("supervisor"):
                month["supervisor"] = m(month["supervisor"])
            for w in month.get("workers", []):
                w["name"] = m(w["name"])
                w["remarks"] = ""
            for r in month.get("receipts", []):
                r["note"] = ""
            bill = month.get("billing")
            if bill and bill.get("supervisor"):
                bill["supervisor"] = m(bill["supervisor"])
            if month.get("kind") == "billing" and month.get("supervisor"):
                month["supervisor"] = m(month["supervisor"])
            for row in (bill["rows"] if bill else month.get("rows", [])):
                row["name"] = m(row["name"])
        site["rate_history"] = {m(k): v for k, v in site["rate_history"].items()}
        site["name_policy"] = "worker and supervisor names shortened to first name + initial"
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


def inline_into(html_path: Path, data: dict, keep_months: int = 4) -> None:
    data = slim_for_inline(data, keep_months)
    html = html_path.read_text(encoding="utf-8")
    start, end = "<!--HISAABO-DATA-->", "<!--/HISAABO-DATA-->"
    i, j = html.find(start), html.find(end)
    if i < 0 or j < 0:
        sys.exit(f"markers not found in {html_path}")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new = html[: i + len(start)] + '\n<script id="hisaabo-data" type="application/json">' + blob + "</script>\n" + html[j:]
    html_path.write_text(new, encoding="utf-8")


def write_private(template: Path, out: Path, data: dict, keep_months: int) -> None:
    """One self-contained HTML with real names and embedded fonts, written outside the repo."""
    html = template.read_text(encoding="utf-8")
    start, end = "<!--HISAABO-DATA-->", "<!--/HISAABO-DATA-->"
    i, j = html.find(start), html.find(end)
    blob = json.dumps(slim_for_inline(data, keep_months), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html[: i + len(start)] + '\n<script id="hisaabo-data" type="application/json">' + blob + "</script>\n" + html[j:]
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
    ap.add_argument("--inline-months", type=int, default=4, help="months with labour entries to inline per site, newest first (default 4)")
    ap.add_argument("--mask", action="store_true", help="public build: worker names as first name + initial, remarks and receipt notes dropped")
    ap.add_argument("--fictional", action="store_true", help="public build: fictional company, client, sites and people; money shifted 10-15 %% per site")
    ap.add_argument("--seed", type=int, default=20261120, help="random seed for --fictional (fixed, so a rebuild gives the same page)")
    ap.add_argument("--private-html", type=Path, help="also write a self-contained page with REAL names and numbers to this path (outside the repo)")
    a = ap.parse_args()
    real = build(a.xlsx)
    data = fictionalize(real, a.seed) if a.fictional else (mask_names(real) if a.mask else real)
    shifts = {x["id"]: x.pop("_shift") for x in data["sites"] if "_shift" in x}
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
        print(f"inlined into {a.inline} ({'fictional' if a.fictional else 'masked' if a.mask else 'REAL'} data)")
    if shifts:
        print("money shift per site (printed only, kept out of the JSON): " + ", ".join(f"{k} x{v}" for k, v in shifts.items()))
    if a.private_html:
        if not a.inline:
            sys.exit("--private-html needs --inline (the page is the template)")
        write_private(a.inline, a.private_html, real, a.inline_months)


if __name__ == "__main__":
    main()
