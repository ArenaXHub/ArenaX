# KhataSite · product brief (v0.5, 19 Nov 2026)

KhataSite is a Labour Management System for construction labour contractors (thekedars) who run several sites for a principal company, pay labour by the day and settle weekly in cash. A product of ArenaX Digital Solutions.

Pilot material: two real registers (Davengere Site, supervisor Sonu Nigam; Motidau PS-1 Gujarat, supervisor/foreman Arun Sharma; principal company Quartzite Infrastructure Pvt Ltd). The demo at `arenax.in/khatasite/` is built from them, with worker names shortened.

ArenaX's own business side (admin console, costs) is kept in the private ArenaX workspace, not in this public repository.

## The problem, as the registers show it

- Attendance is a paper "Daily Manhours Report" per site per month: one row per worker, hours per date (8 h = 1 day, 12 h = 1.5), transcribed into Excel later.
- Money moves four times a week: company → thekedar → munshi (cash for kharchi and mess) → mazdoor (weekly pocket money, advances). Each hop is in a different place: the register's right block, UPI history, memory.
- The thekedar's bachat (what is left of the company bill after wages and extra costs) is worked out by hand at month end. In Feb 2026 at PS-1: billed ₹6,64,400; wages ₹4,09,814; extra costs ₹8,072; bachat ₹2,46,514 (37%).
- Dues and advances are carried forward by hand; negative net payments (worker owes the contractor) are common.
- Rates change (e.g. one PS-1 helper ₹420 → ₹450 from Jan 2026) and the effective date is implicit in which monthly sheet has the new number.

## Users (hard constraints)

| User | Reality | What KhataSite asks of them |
|---|---|---|
| Labour (mazdoor) | cannot read or write | nothing: no login, no app. QR card or WhatsApp slip (add-ons), printed weekly slip |
| Supervisor (munshi, foreman) | one per site, barely literate, marks a paper register, gives cash advances | tap pictures: 4 attendance buttons per worker, note images for kharchi, one submit. Sees days and the kharchi he gave, never rates or wages |
| Contractor (thekedar) | several sites, low formal education, sets daily rates, wants bachat, expense and dues at a glance | four big tiles, alerts, "paisa kahan gaya" bar, two charts, settlement table, big −10/+10 rate buttons |

Hindi, Hinglish and English (3-way toggle, default Hinglish), big icons, pictures and motion; text is secondary. Attendance is supervised (the munshi marks; workers do not self check-in) and must feel like the paper register.

## Roles shown to visitors

1. **Thekedar / Owner**: all sites, rates with effective dates, approve weekly settlement, pay munshi, bachat dashboard, reports.
2. **Munshi / Supervisor**: own site only: attendance, kharchi, cash receipt. Cannot change rates or edit past days.
3. **Hisaab-wala / Accountant** (suggested, optional): the contractor's office clerk: payments, advances, expenses, reports; no rate changes.
4. **Company view** (Phase 2, read-only): the principal employer (e.g. QIPL) sees attendance proof for billing.
5. **Mazdoor**: no login; QR card and WhatsApp slip (add-ons) or a printed weekly slip.

## Product surface (as demoed)

- **Munshi app** (PWA, phone): site picker; worker cards with avatar; sun = 8 ghante, sun + moon = 12 ghante OT, half circle = 4 ghante, cross = nahi aaya; ± hour stepper; "Sabko pura din"; live tally; kharchi by tapping ₹100/₹200/₹500 notes; "Register dekho" shows this week's page; "Hazri jama karo" stamps site (geo-lock 200 m), time and group photo; optional Hindi voice. Four step cards beside the phone light up in step with an automatic walk-through; the visitor can take over at any tap.
- **Thekedar dashboard**: tiles for company bill, mazdoori, bachat and "mazdoor par baaki" with good / watch / act states (icon + label + colour); alerts built from the data (dues, absent today, kharchi up this week, advance above wages, workers who left); "paisa kahan gaya" stacked bar (kharchi + mess, mazdoori at settlement, extra costs, bachat); bachat % ring; daily bachat bars; monthly bill vs wages; weekly settlement table; rate change with effective date and history; company cash timeline.

## Trust and technology

Geo-lock 200 m · morning time window · group photo · offline-first PWA with sync · Labour Codes-ready wage and attendance registers (OSH Code 2020, Code on Wages 2019) · dashboards · add-ons: QR / NFC worker card, WhatsApp parchi.

## Pricing (every number lives in the `PRICING` object in `index.html`)

- **Free trial**: 10 Din, 1 site, all features, no card (long enough for one full weekly hisaab).
- **Site Plan, monthly**: ₹3,999 per site per month + GST, includes 40 active labour per site; ₹10 per extra active labour. "Active" = marked present at least once that month. Munshi and accountant logins free.
- **Site Plan, annual**: ₹25,000 per site per year + GST (₹2,083 a month), paid once a year (`site.annual`). Extra labour is still ₹10 per extra active labour, counted each month. Onboarding is free on the annual plan.
- **Launch offer**: ₹2,499 per site per month, locked for the first 6 months (₹1,500 off, shown against the struck-through ₹3,999), for contractors who join in the launch month (January 2027, `launch.start = 2027-01-01`, `launch.lockMonths = 6`). From the seventh month they pay ₹3,999 a month, or take the annual plan. December 2026 is the pilot with the two contractors, who get this offer.
- **Onboarding (one-time, per contractor)**: register import, munshi training, site setup (GPS, time window). Final rule (KP, 19 Nov 2026), in `PRICING.onboarding`:
  - Monthly plan: ₹3,999 if booked by 31 Dec 2026 (`early`, `earlyBy`), shown against the struck-through ₹4,999 with a countdown on the onboarding card; ₹4,999 after (`regular`).
  - Annual plan: free (`annualFree`), shown as the struck-through monthly onboarding price of that day and FREE, with the line "Saal ka plan lo, setup free. ₹3,999 bachao." Until 31 Dec 2026 the struck price is ₹3,999; after that it is ₹4,999.
  - The launch banner and the Site Plan card say "setup FREE" next to the annual plan, and the banner shows the monthly plan's onboarding offer.
- **Add-ons**: QR / NFC worker card; WhatsApp parchi (weekly pay slip / voice note). "Ask Price".
- **Multi-site discount** (`PRICING.multiSite`): 2–4 sites 10% off the regular per-site price (₹3,599 a month, ₹22,500 a year); 5–9 sites 15% off (₹3,399 a month, ₹21,250 a year). The tier reached applies to all of the contractor's sites. It does not stack with the launch price; the lower of the two applies. Shown as a strip under the plan cards ("Zyada site, kam daam") and in the calculator.
- **Multi-site / company**: 10+ sites, "Ask Price" (`enterprise.minSites`), with a button to the query form.
- No competitor names or prices on the public page.

### Fayda vs kharcha (shown on the pricing section, the dashboard and the calculator)

An estimate, always labelled "andaaza", from two stated assumptions in the `SAVINGS` object, applied to the register numbers:

1. If only 1% of attendance is written wrong, the contractor overpays 1% of the month's wages.
2. The munshi saves 1 hour a day of register work (valued at his monthly pay ÷ 10-hour day).

PS-1 Motidau, Feb 2026: 1% of ₹4,09,814 = ₹4,098, plus 10% of the foreman's ₹25,000 = ₹2,500, so ₹6,598 a month against ₹2,083 (the annual plan per month): 3.2 times the cost. `SAVINGS.compareWith` sets the cost the fayda is set against: `'annual'` (annual plan ÷ 12, the default, named under the cost bar) or `'monthly'` (₹3,999, 1.6 times). The dashboard shows the same figure for whichever site and month is selected.

The calculator takes the contractor's own numbers: sites, workers per site, average daily rate, the munshi's monthly salary and the munshi hours saved a day (default 1). Wages = sites × workers × rate × 30 paid day-units a month (overtime included, as in the register); fayda = 1% of those wages + the munshi's saved hours valued from his own salary (salary × hours ÷ 10-hour day). Defaults come from the PS-1 Feb register (26 workers, ₹495 average rate, ₹25,000 munshi): ₹6,361 a month, 1.6 times the monthly plan (₹3,999) and 3.1 times the annual plan per month (₹2,083). Always labelled "andaaza". The cost side sets the two plans side by side for the contractor's sites and workers: plan price, onboarding, first month and first year, before and with GST. January 2027 joiners on the monthly plan pay the launch price for the first 6 months. At one site with no extra labour, booked by 31 Dec 2026, the first year costs ₹42,987 on the monthly plan (6 × ₹2,499 + 6 × ₹3,999 + ₹3,999 onboarding) and ₹25,000 on the annual plan: ₹17,987 less before GST. With 2 to 9 sites the plan price drops by the multi-site discount; from 10 sites the calculator shows "Ask Price" and a button to the query form.

### Query form and always-visible CTA

A floating "10 Din free trial" button and every trial button open a short form (name, mobile, place, sites, workers, note). It opens WhatsApp with a pre-filled message to the number in the single `CONTACT_WHATSAPP` line. That line holds a temporary contact until the ArenaX business number replaces it (KP's exceptions to CLAUDE.md rule 5, D-69 and D-70, cover this line only). If the line is `null`, the form opens an email to contactarenax@gmail.com with the same message. Nothing is stored by the page.

## Compliance wording

The Contract Labour (Regulation and Abolition) Act was repealed when the four Labour Codes came into force on 21 Nov 2025. Do not write "Form XIV / Contract Labour Act". Say: "Labour Codes-ready wage and attendance registers (OSH Code 2020, Code on Wages 2019)".

## ArenaX as business consultants

Cash and register flow audit · register import to KhataSite · Labour Codes setup · munshi training (one morning on site).

## Roadmap

| Phase | Scope | Notes |
|---|---|---|
| 0 (now) | Product page + clickable demo from the two registers | this repo, `khatasite/` |
| 1 | Pilot (Dec 2026) with the PS-1 / Davengere contractor: munshi PWA (offline attendance, kharchi, submit with geo + photo), thekedar dashboard, weekly settlement, rate history | launch offer ₹2,499 for the first 6 months |
| 1.5 | Accountant role, register import tool (this build script generalised), Labour Codes register export, QR card and WhatsApp parchi add-ons | onboarding ₹3,999 / ₹4,999 on the monthly plan, free on the annual plan |
| 2 | Company view (read-only attendance proof for billing), multi-site plans, payment gateway for subscriptions | |
| 3 | Payouts to labour (UPI), audit trail, analytics across sites | |

## Decided by KP (19 Nov 2026)

- Launch month January 2027; December 2026 is the pilot with the two contractors.
- `BH`, `MH`, `bhu` stay "other" for now.
- The munshi sees days only, plus the kharchi he himself gave. No rates, no wages on the munshi app.
- Worker names are shortened (first name + initial) in everything public; the real-name demo is built outside the repository and never committed.
- v2: no internal ArenaX views, costs or business numbers on any public page or in this repository; QR / NFC card and WhatsApp parchi are add-ons.
- v2.1: pricing ₹2,999 regular, ₹1,999 launch, onboarding ₹4,999, "Ask Price" for add-ons, "10 Din" trial; bachat = company bill − total site expense (wages, which include kharchi + mess, plus extra), as in the register's month total; onboarding without QR cards; fayda estimate shown to contractors; sample popups (WhatsApp parchi, printed slip, QR card, geo-lock, morning window, group photo, offline, register, dashboard); always-visible CTA with a query form. (The v2.1 prices were replaced in v2.3.)
- v2.2: the fayda calculator takes the contractor's own numbers and values the munshi's saved time from his salary. Onboarding stays ₹4,999 in the launch offer (free onboarding was tried and withdrawn the same day).
- v2.3: monthly plan ₹3,999 per site per month; launch offer ₹2,499 for the first month only, for contractors who join in January 2027; annual plan ₹25,000 per site per year (₹2,083 a month); the fayda is set against the annual plan per month. Onboarding, final rule: free on the annual plan; on the monthly plan ₹3,999 if booked by 31 Dec 2026, ₹4,999 after.
- v2.5: the launch price ₹2,499 is locked for the first 6 months (replaces "first month only"); after 31 Dec 2026 the annual onboarding box strikes ₹4,999; multi-site discount 2–4 sites 10%, 5–9 sites 15%, 10+ sites Ask Price, not stacking with the launch price.
- v2.6: renamed from SiteBook to KhataSite (KP's name rule of 19 Nov 2026: "Hisaabo" is the name of a live accounting app, "SiteKhata" of an Android app). Website `arenax.in/khatasite/`; the old `arenax.in/sitebook/` redirects there. App address (planned): `khatasite.arenax.in`.
