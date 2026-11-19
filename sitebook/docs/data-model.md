# SiteBook · data model (v0.1)

Multi-tenant from day one: every row that belongs to a contractor carries `contractor_id`. Wage for a day = `hours / 8 × the rate effective on that date` (from `worker_rates`). Money fields are integers in paise or decimals with 2 places; dates are ISO; timestamps are UTC.

## Tables

### contractors
| field | notes |
|---|---|
| id | pk |
| name, owner_name, phone, email | phone/email never in exports |
| gst_number, udyam_number | optional |
| created_at, status | active, suspended |

### subscriptions
| field | notes |
|---|---|
| id, contractor_id | |
| plan | trial, site, launch, enterprise |
| price_per_site, included_labour, extra_labour_price, onboarding_fee | copied from the price list at signup so later price changes do not alter old invoices |
| trial_ends_at, locked_until | launch price period (`launch.lockMonths`: the first month in v2.3) |
| billing_cycle | monthly, annual (annual: onboarding_fee 0) |
| status | trial, active, past_due, suspended, cancelled |

### sites
| field | notes |
|---|---|
| id, contractor_id | |
| name | e.g. "Motidau PS-1 Gujarat" |
| principal_company | e.g. "Quartzite Infrastructure Pvt Ltd" |
| gps_lat, gps_lng, radius_m | default 200 |
| window_start, window_end | morning marking window, local time |
| timezone, status | |

### users
| field | notes |
|---|---|
| id, contractor_id | |
| role | owner, supervisor, accountant, company_viewer |
| site_scope | array of site ids; supervisors get exactly one |
| phone, name, pin_hash | login by phone + OTP or PIN |
| status | |

### workers
| field | notes |
|---|---|
| id, contractor_id | |
| name | as in the register, title case |
| designation | Forman, Carpenter, Fitter, Helper … |
| qr_id | printed on the card; unique per contractor |
| home_village, photo_id | |
| pay_type | daily, fixed_monthly |
| current_site_id | updated by a `moved` attendance code |
| status | active, left |

### worker_rates
| field | notes |
|---|---|
| id, worker_id | |
| rate | ₹ per 8-h day (or monthly salary when pay_type = fixed_monthly) |
| effective_from | date |
| set_by, set_at | user id |

Rate on a date = the row with the greatest `effective_from ≤ date`.

### attendance
| field | notes |
|---|---|
| id, contractor_id, site_id, worker_id | |
| date | |
| hours | decimal; null when a code applies |
| code | present, absent (A), left (L), moved (PS1…), other (BH/MH/bhu until confirmed) |
| marked_by | supervisor user id |
| gps_lat, gps_lng, gps_ok | inside the site radius |
| photo_id | group photo of the submission |
| marked_at, synced_at | offline-first: marked_at is the phone's time, synced_at the server's |
| locked | true after the owner approves the week |

Unique on (worker_id, date). Past days are editable only by owner/accountant, with an audit row.

### advances
| field | notes |
|---|---|
| id, contractor_id, site_id, worker_id | |
| date, amount | |
| kind | advance (ADVANCE column), pocket (weekly kharchi) |
| given_by | user id |
| note | |

### kharchi_mess
| field | notes |
|---|---|
| id, contractor_id, site_id, worker_id | |
| week_ending | Sunday, as the register |
| pocket, mess | the two weekly columns |

### cash_handovers
| field | notes |
|---|---|
| id, contractor_id, site_id | |
| from_user_id, to_user_id | owner → supervisor, supervisor → worker (to_worker_id) |
| amount, mode | upi, cash |
| reference | UPI id or null |
| acknowledged_at, ack_by | one tap by the receiver |

### client_rates
| field | notes |
|---|---|
| id, contractor_id, site_id | |
| designation, rate | per day-unit billed to the company (Forman 900, Carpenter 800 …) |
| effective_from | |

### client_receipts
| field | notes |
|---|---|
| id, contractor_id, site_id | |
| date, amount, mode, reference, note | the QIPL block under the grid |

### expenses
| field | notes |
|---|---|
| id, contractor_id, site_id | |
| date, kind | mess, ta_credit, ta_debit, extra, misc |
| amount, note, recorded_by | |

### weekly_settlements
| field | notes |
|---|---|
| id, contractor_id, site_id, worker_id | |
| week_ending | |
| days, wage | computed: Σ hours/8 and Σ hours/8 × rate(date) |
| pocket, mess, advance, dues_brought_forward, ta_credit, ta_debit | |
| net | wage − pocket − mess − advance − dues + carried_forward + ta_credit − ta_debit (the register's formula) |
| status | draft, approved, paid |
| approved_by, approved_at, paid_at, slip_sent_at | |

### billing_units (derived view for the company bill)
Per site, date and designation: Σ day-units × client rate. Day-units follow the company's rule (the registers bill 1.625 units for a 13-h day), configurable per site.

## Derived numbers the dashboard shows

- Daily wages = Σ over daily-paid workers of hours/8 × rate(date). Fixed-monthly salaries are added at month level.
- Daily billed = Σ day-units × client rate. Daily bachat = billed − wages.
- Monthly billed vs wages, bachat (billed − wages − extra costs) and bachat %, receipts, advances, dues.
- Active labour for pricing = workers with at least one present day in the month, per site.

## Privacy

Aadhaar is never stored (the registers' column is empty and stays so). Phone numbers of workers are optional and never exported. Exports and the Labour Codes registers carry name, designation, days, rate and wage only.
