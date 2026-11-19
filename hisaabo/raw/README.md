# Raw registers (not in git)

Drop the contractor's Excel registers and `local.json` here. `.gitignore` keeps every `.xlsx`, `.xls`, `.csv` and `.json` out of the repository: the repository is public and the registers carry worker names, hours, rates, advances and dues; `local.json` names the real sites.

Then run `tools/build_demo_data.py --fictional` (see `../README.md`). Only the fictional JSON and the pages are committed.
