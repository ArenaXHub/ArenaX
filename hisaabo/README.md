# Hisaabo by ArenaX · From attendance to accounts

Attendance, wages and site accounts for construction labour contractors. A product of ArenaX Digital Solutions.

Tagline: English "From attendance to accounts", Hinglish "Hazri se hisaab tak", Hindi "हाज़िरी से हिसाब तक".

| Address | What |
|---|---|
| `https://arenax.in/hisaabo/` | product page with the live demo (opens in English) |
| `https://arenax.in/hisaabo/demo/` | standalone demo page: one fictional contractor, two sites |
| `https://arenax.in/hisaabo/app/` | quick demo app, front end only (opens in Hinglish) |

Older addresses (`/sitebook/`, `/khatasite/`, `/sitekhata/` and their `app/`) are redirect pages at the repository root, so links already shared keep working. The working app is planned at `hisaabo.arenax.in` (separate hosting and repository).

## Public data is fictional

This repository is public. Every page here shows a fictional company (Shree Ganesh Constructions), client (ABC Infra Ltd), sites (Site A – Ahmedabad, Site B – Pune), supervisors and workers. The numbers come from real registers but every money amount is shifted by a random 10–15 % per site, so totals, nets and margins still add up while no figure matches a real one. Hours, day codes and dates keep the register's arithmetic (8 h = 1 day). Real names, real numbers and the real site and client names are never committed; they exist only in the raw registers, a git-ignored name map and a private file outside the repository.

## Folder

```
hisaabo/
  index.html                 product page + live demo (inline CSS/JS, data inlined as JSON)
  demo/index.html            standalone demo page (built from index.html, do not edit by hand)
  app/index.html             quick demo app: login + one-tap roles, reads data/hisaabo-demo.json
  assets/                    favicon.svg, og.png
  data/hisaabo-demo.json     the fictional demo data (full, pretty-printed)
  raw/                       registers and local.json (ignored by git)
  tools/build_demo_data.py   registers -> JSON -> inlined into index.html (--fictional for every public build)
  tools/build_demo_page.py   index.html -> demo/index.html (+ the private pitch copy)
  tools/sync_app.py          copies the site's fonts, icon sprite and shared strings into app/index.html
```

The product brief, data model and the register checks live in the private ArenaX workspace, not here.

## Rebuild

```
py -I hisaabo/tools/build_demo_data.py hisaabo/raw/<register-1>.xlsx hisaabo/raw/<register-2>.xlsx ^
   --out hisaabo/data/hisaabo-demo.json --inline hisaabo/index.html --fictional ^
   --private-html <ArenaX>\private\hisaabo-demo-real.html
py -I hisaabo/tools/build_demo_page.py hisaabo/index.html hisaabo/demo/index.html --pitch <ArenaX>\private\hisaabo-demo-pitch.html
py -I hisaabo/tools/sync_app.py hisaabo/index.html hisaabo/app/index.html
```

- `--fictional` is the only public build. `--seed` (fixed by default) makes a rebuild give the same names and shifts.
- `--private-html` writes the real-name, real-number page (fonts embedded, works offline) outside the repository. Never commit it.
- `--pitch` writes a self-contained copy of the demo page with the same fictional data, for sending on WhatsApp. Outside the repository.
- `raw/local.json` maps register files to site slots (`site-a`, `site-b`) and holds the real site labels and receipt header. It is git-ignored; without it the sites take `site-a`, `site-b` in input order.

Needs Python 3.12 and `openpyxl`. The EMP/AADHAR column is never read.

## Editing

- Labels: English and Hinglish use the professional terms (Contractor, Supervisor, Accountant, Worker, Attendance, Cost breakdown, Wages, Allowance & mess, Other expenses, Margin, Client billing); Hindi uses ठेकेदार, मुंशी, अकाउंटेंट, मज़दूर, हाज़िरी, खर्च का हिसाब, मज़दूरी, खर्ची + मेस, बाकी खर्च, बचत, कंपनी का बिल. All strings are in the `T` object (Hindi, Hinglish, English, in that order).
- Pricing: the `PRICING` object at the top of the script in `index.html`.
- Benefit line: `BENEFIT` (3 wrong attendance entries caught a week, ₹495 a day, 4.33 weeks a month), set against the launch price while the offer runs. The calculator uses the same basis with the contractor's own numbers.
- Cost breakdown colours: costs in reds (Wages darkest, Allowance & mess lighter, Other expenses lightest), Margin green (`--c-cost1..3`, `--c-margin`), validated with the dataviz palette checks; every segment carries a label or a callout.
- Query form: the single `CONTACT_WHATSAPP` line (temporary contact; see the ArenaX decision log).
- Icons: the inline SVG sprite; use `ic('name')`. No emoji.
- After changing fonts, icons or shared strings: run `sync_app.py`. After any change to `index.html`: run `build_demo_page.py`.

## Verify before committing

```
py -I -m http.server 8765 --bind 127.0.0.1        # from the repo root
```

Screenshot `/hisaabo/`, `/hisaabo/demo/` and `/hisaabo/app/` at 1280 and 390 px wide; the console must be clean and `scrollWidth == clientWidth`. Scan every public file for real names before a commit.
