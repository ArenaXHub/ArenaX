# KhataSite by ArenaX

Labour Management System for construction labour contractors. A product of ArenaX Digital Solutions.

Live path: `https://arenax.in/khatasite/` (this folder is served as-is by GitHub Pages; the root homepage is untouched).

Renamed from SiteBook on 19 Nov 2026. The old path `https://arenax.in/sitebook/` is a redirect page (`sitebook/index.html` at the repository root) so links already shared keep working. The app is planned at `khatasite.arenax.in` (separate hosting; see the ArenaX decision log).

The page carries `noindex` because the demo is built from two real site registers (hours, rates, advances, dues, company receipts) and is shared by link with the contractors who provided them. Worker names in the public build are shortened to first name + initial; the repository is public and real worker names are never committed. Nothing about ArenaX's own business (admin console, costs) belongs in this folder; that lives in the private ArenaX workspace.

## Folder

```
khatasite/
  index.html                 the whole site: product page + live demo (inline CSS/JS, data inlined as JSON)
  assets/                    favicon.svg, og.png (fonts are the site's own, ../assets/fonts; the ₹ sign and the हिंदी label use tiny fonts embedded in index.html)
  data/khatasite-demo.json    everything the build script extracted and derived (full, pretty-printed)
  raw/                       the two Excel registers (ignored by git: this repo is public)
  tools/build_demo_data.py   Excel -> JSON -> inlined into index.html
  docs/product-brief.md      users, roles, pricing, compliance wording, roadmap
  docs/data-model.md         tables for the real product
  verify/                    headless screenshots (desktop 1280, phone 390) used before each commit
```

## Rebuild the demo data

```
py -I khatasite/tools/build_demo_data.py khatasite/raw/Davengere_Site.xlsx khatasite/raw/PS-1_ALKESH.xlsx ^
   --out khatasite/data/khatasite-demo.json --inline khatasite/index.html --mask ^
   --private-html C:\Users\Kamal\Projects\ArenaX\private\khatasite-demo-real.html
```

`--mask` is the public build: worker names become first name + initial ("Sakindera R."), free-text remarks and receipt notes are dropped, supervisor and site names and every number stay. `--private-html` writes a second, self-contained page with the real names and the fonts embedded, outside the repository, for the two contractors (sent by WhatsApp). Always build the public page with `--mask`; never commit the private file.

Needs Python 3.12 and `openpyxl`. The script prints a month-by-month summary (workers, wages, billed, receipts) so the numbers can be checked against the registers. `--inline` replaces the JSON between `<!--KHATASITE-DATA-->` markers in `index.html` with a slimmed copy (only the fields the page uses); `--inline-months` (default 4) sets how many months with labour entries per site are inlined, the summary rows stay complete.

The EMP/AADHAR column is never read. No phone numbers exist in the registers. Keep it that way.

## What the registers contain (verified)

Format "Daily Manhours Report" (Quartzite Infrastructure Pvt Ltd). Row 6 headers, row 7 dates, workers from row 8 to the `TOTAL` row. Attendance is in **hours**: 8 h = 1 day, 12 h = 1.5 days, 4 h = half. Codes: `A` absent, `L` left the site, `PS1`/`PS2`/`PS3` moved to another site, `BH`/`MH`/`bhu` other leave (shown as "other" until confirmed). Right block per worker: weekly POCKET (kharchi) + MESS, totals, ADVANCE, DUES AMOUNT, PRE AMOUNT, two T.A columns (credit, debit), RATE (₹ per 8-h day; a non-integer rate marks a fixed monthly salary, the foreman), PAYMENT, NET PAYMENT, REMARKS. Below the grid: QIPL receipts by date, TOTAL EXPENSE, EXTRA EXPENSES, MESS, EXPENCE IN HAND, PREVIOUS MONTH.

Sheets ending in `C` are the billing to the company per designation in day-units (Forman ₹900, Carpenter ₹800, Fitter ₹800, Helper ₹650 per day-unit) with GST and total.

Net payment, as the register computes it: `PAYMENT − (POCKET + MESS) − ADVANCE − DUES + PRE AMOUNT + T.A credit − T.A debit`.

| Register | Site | Supervisor | Months |
|---|---|---|---|
| `Davengere_Site.xlsx` | Davengere Site | Sonu Nigam | Aug, Sep, Oct 2026 (no billing sheets) |
| `PS-1_ALKESH.xlsx` | Motidau PS-1 Gujarat | Arun Sharma | Jun, Jul, Aug, Nov, Dec 2025; Jan, Feb, Mar, Apr 2026; billing sheets Dec to Apr; EXPENSES sheet |

Numbers checked against the registers (billed vs labour wages): Feb-26 ₹6,64,400 vs ₹4,09,814 (27 workers); Dec-25 ₹7,05,831 vs ₹4,19,628; Jan-26 ₹7,52,644 vs ₹4,67,273; Mar-26 ₹4,77,662 vs ₹2,95,604. Feb-26 QIPL receipts: 01 ₹30,000, 07 ₹35,000, 15 ₹33,000, 19 ₹4,500, 22 ₹26,000, 26 ₹1,000. The script reproduces all of these; the daily billing series sums exactly to the month's billed total, and daily variable wages plus the foreman's fixed salary sum exactly to the register's PAYMENT total.

## Editing

- Pricing: the `PRICING` object at the top of the script in `index.html` (v2.7: monthly plan ₹3,999 per site per month; launch offer ₹2,499 locked for the first 6 months, for contractors who join in January 2027 (`launch.lockMonths = 6`); multi-site discount in `multiSite` (2–4 sites 10%, 5–9 sites 15%, not stacking with the launch price; 10+ sites "Ask Price" from `enterprise.minSites`); annual plan ₹29,999 per site per year (`site.annual`; 2–4 sites ₹26,999 and 5–9 sites ₹25,499 in `multiSite[].annual`); 10 Din trial; onboarding in `onboarding`: monthly plan ₹3,999 if booked by 31 Dec 2026 (`earlyBy`), ₹4,999 after, free on the annual plan (`annualFree`); 40 active labour included, ₹10 per extra; add-ons "Ask Price").
- Query form: the single line `CONTACT_WHATSAPP` next to it holds the WhatsApp number the form sends to (international form, no +). It is a temporary contact until the ArenaX business number replaces it; KP's rule 5 exceptions (D-69, D-70) cover this line only. Set it to `null` to send by email.
- Fayda estimate: `SAVINGS` next to it (1% attendance errors, 1 munshi hour a day valued from the munshi's salary, 30 paid day-units a month, reference register PS-1 Feb 2026). `compareWith` picks the cost the fayda is set against: the annual plan ÷ 12 (default) or the monthly plan. The calculator lets the contractor enter his own numbers.
- Icons: an inline SVG sprite at the top of `<body>`; use `ic('name')` in code. Do not use emoji: older Android phones show new emoji as empty boxes, and emoji font fallback slows the page.
- Demo dates and default dashboard: the `DEMO` object next to it.
- Strings: the `T` object (every key has Hindi, Hinglish, English, in that order).

## Verify before committing

```
py -I -m http.server 8765 --bind 127.0.0.1        # from the repo root
# then screenshot http://127.0.0.1:8765/khatasite/index.html at 1280 and 390 px wide,
# check the console is clean and document.documentElement.scrollWidth == clientWidth
# Lighthouse mobile (performance ≥ 85) against a gzip server, as GitHub Pages serves gzip
```
