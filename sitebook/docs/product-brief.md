# SiteBook · product brief (v0.1, 19 Nov 2026)

SiteBook is a Labour Management System for construction labour contractors (thekedars) who run several sites for a principal company, pay labour by the day and settle weekly in cash. A product of ArenaX Digital Solutions.

Pilot material: two real registers (Davengere Site, supervisor Sonu Nigam; Motidau PS-1 Gujarat, supervisor/foreman Arun Sharma; principal company Quartzite Infrastructure Pvt Ltd). The demo at `arenax.in/sitebook/` is built from them.

## The problem, as the registers show it

- Attendance is a paper "Daily Manhours Report" per site per month: one row per worker, hours per date (8 h = 1 day, 12 h = 1.5), transcribed into Excel later.
- Money moves four times a week: company → thekedar (receipts of ₹1,000 to ₹50,000, several per month) → munshi (cash for kharchi and mess) → mazdoor (weekly pocket money, advances). Each hop is in a different place: the register's right block, UPI history, memory.
- The thekedar's profit is a separate billing sheet per month (day-units × rate per designation) compared by hand with the labour sheet. In Feb 2026 at PS-1: billed ₹6,64,400 against wages ₹4,09,814, margin ₹2,54,586 (38%), but nobody sees this until the month closes.
- Dues and advances are carried forward by hand (PRE AMOUNT, DUES AMOUNT); negative net payments (worker owes the contractor) are common.
- Rates change (e.g. one PS-1 helper ₹420 → ₹450 from Jan 2026) and the effective date is implicit in which monthly sheet has the new number.

## Users (hard constraints)

| User | Reality | What SiteBook asks of them |
|---|---|---|
| Labour (mazdoor) | cannot read or write | nothing: no login, no app. QR card, WhatsApp voice note, printed weekly slip |
| Supervisor (munshi, foreman) | one per site, barely literate, marks a paper register, gives cash advances | tap pictures: 4 attendance buttons per worker, note images for advances, one submit |
| Contractor (thekedar) | several sites, low formal education, sets daily rates, wants profit, expense and dues at a glance | KPI tiles, two charts, a settlement table, big −10/+10 rate buttons |

USP: the contractor's and supervisor's work gets easier. Hindi, Hinglish and English (3-way toggle, default Hinglish), big icons, pictures and animation; text is secondary. Attendance is supervised (the munshi marks; workers do not self check-in) and must feel like the paper register.

## Roles (role-based access)

1. **ArenaX Admin (KP)**: onboard contractors, trials, plans, billing, suspend, support view.
2. **Thekedar / Owner**: all sites, rates with effective dates, approve weekly settlement, pay munshi, profit dashboard, reports.
3. **Munshi / Supervisor**: own site only: attendance, advances, cash handover acknowledgement. Cannot change rates or edit past days.
4. **Hisaab-wala / Accountant** (suggested, optional): the contractor's office clerk: payments, advances, expenses, reports; no rate changes.
5. **Company view** (Phase 2, read-only): the principal employer (e.g. QIPL) sees attendance proof for billing.
6. **Mazdoor**: no login; QR card, WhatsApp voice note or printed slip of weekly pay.

## Product surface (as demoed)

- **Munshi app** (PWA, phone): site picker; worker cards with avatar; ☀️ 8 ghante, ☀️🌙 12 ghante OT, 🌓 4 ghante, ❌ nahi aaya; ± hour stepper; "Sabko pura din"; live tally (aaye / nahi aaye / baaki); 💵 advance by tapping ₹100/₹200/₹500 notes; "Register dekho" shows the week grid exactly as the Excel; "Hazri jama karo" stamps site (geo-lock 200 m), time and group photo; optional Hindi voice confirmation.
- **Thekedar dashboard**: KPI tiles (billed, wages, margin, margin %, workers, days, receipts, advances); daily margin bars with tooltips; monthly billed vs wages grouped bars (legend, one axis, table view); weekly settlement table (days, rate, wage, kharchi+mess, advance, net; negative in red = mazdoor par baaki) with a full-month view that reproduces the register's totals; rate change (worker, −10/+10, effective-from date, history seeded from the registers); company receipts timeline.
- **ArenaX admin**: contractors table (plan, trial days left, sites, active labour, monthly bill from the pricing formula), MRR tile, cost-and-margin tile from the cost model, extend-trial / suspend. Sample rows are marked SAMPLE; the pilot row's active labour comes from the registers.

## Trust and technology

Geo-lock 200 m · morning time window · group photo · QR/NFC worker card · offline-first PWA with sync · WhatsApp voice/slip to labour · Labour Codes-ready wage and attendance registers (OSH Code 2020, Code on Wages 2019) · dashboards.

## Pricing (every number lives in the `PRICING` object in `index.html`)

- **Free trial**: 30 days, 1 site, all features, no card.
- **Site Plan**: ₹999 per site per month + GST, includes 40 active labour per site; ₹10 per extra active labour. "Active" = marked present at least once that month. Munshi and accountant logins free. Annual = pay 10 months.
- **Launch offer**: ₹799 per site per month (₹200 off) for contractors who join in the launch month, locked for their first 6 months. Launch month: **January 2027** (`launch.start = 2027-01-01`); December 2026 is the pilot with the two contractors. Pilot contractors (PS-1 / Davengere) get this offer.
- **Onboarding (one-time)**: ₹2,999: Excel import, QR cards, munshi training.
- **Multi-site / company**: 10+ sites, custom.
- No competitor names or prices on the public page.

## Cost model (for the admin tile and planning; not on the public page)

Variable cost ≈ ₹105 to ₹150 per contractor per month (WhatsApp slips ~₹0.17 per message, storage, ~3.5% payment-gateway fee).

| Stage | Contractors | Fixed cost / month | Margin at ₹999 | Margin at ₹799 |
|---|---|---|---|---|
| Pilot | 10 | ≈ ₹10,500 | 52% | 41% |
| Growth | 100 | ≈ ₹88,500 | 59% | 49% |
| Scale | 500 | ≈ ₹3,10,000 | 69% | 62% |

Break-even at the Growth cost base: 38 contractors at ₹999, 47 at ₹799.

## Compliance wording

The Contract Labour (Regulation and Abolition) Act was repealed when the four Labour Codes came into force on 21 Nov 2025. Do not write "Form XIV / Contract Labour Act". Say: "Labour Codes-ready wage and attendance registers (OSH Code 2020, Code on Wages 2019)".

## ArenaX as business consultants

Process audit of the contractor's cash and register flow · Excel-to-SiteBook migration · Labour Codes compliance setup · supervisor training (one morning on site, phone support through the first week).

## Roadmap

| Phase | Scope | Notes |
|---|---|---|
| 0 (now) | Product page + clickable demo from the two registers | this repo, `sitebook/` |
| 1 | Pilot (Dec 2026) with the PS-1 / Davengere contractor: munshi PWA (offline attendance, advances, submit with geo + photo), thekedar dashboard, weekly settlement, rate history, WhatsApp slips | launch offer ₹799 |
| 1.5 | Accountant role, Excel import tool (this build script generalised), QR cards, Labour Codes register export | onboarding fee ₹2,999 |
| 2 | Company view (read-only attendance proof for billing), multi-site plans, payment gateway for subscriptions | |
| 3 | Payouts to labour (UPI), bank-grade audit trail, analytics across contractors | |

## Decided by KP (19 Nov 2026)

- Launch month January 2027; December 2026 is the pilot with the two contractors.
- `BH`, `MH`, `bhu` stay "other" for now.
- The munshi sees days only, plus the advances and kharchi he himself gave. No rates, no wages on the munshi app.
- Names: the repository is public, so real worker names are never on GitHub. The public build masks worker names as first name + initial (supervisor and site names and all numbers stay). A separate private build with real names is written outside the repository for the two contractors and is never committed.
