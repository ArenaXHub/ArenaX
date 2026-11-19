"""Copy the website's fonts, icon sprite and shared strings into the demo app.

The demo app (app/index.html) is one self-contained page. Three parts of it come from the
website (index.html) so both look and read the same; they sit between markers:

    /*@FONTS*/ ... /*@/FONTS*/          every @font-face, with paths one folder deeper
    <!--@SPRITE--> ... <!--@/SPRITE-->  the inline SVG icon sprite
    /*@SITE_T*/ ... /*@/SITE_T*/        the strings listed in SHARED, same wording in hi / hn / en

Run after changing any of those on the website:

    py -I khatasite/tools/sync_app.py khatasite/index.html khatasite/app/index.html
"""
import re
import sys
from pathlib import Path

SHARED = ("mon dow h8 h12 h4 habs hours_u day_u t_present t_absent t_left adv_btn adv_title adv_clear adv_done reg_cap reg_name submit all_full reg_show reg_hide "
          "ok_title ok_geo ok_photo ok_sync ok_close stamp voice speak_abs speak_h k_billed k_billed_sub k_wages k_wages_sub k_bachat k_bachat_sub k_owed k_owed_sub "
          "no_bill st_good st_watch st_action st_clear al_owed al_absent al_allin al_left c_name c_days c_rate c_wage c_km c_adv c_net c_total fixed_pay per_month "
          "tt_date tt_billed tt_wages tt_bachat tt_present tt_absent month leg_plus leg_minus vd_h vd_h_nb vd_sub vd_sub_nb tbl_show tbl_hide "
          "r_th r_mu r_hw lv_owner lv_site lv_office p_pay p_adv p_exp p_rep").split()


def fill(text: str, start: str, end: str, value: str) -> str:
    i, j = text.find(start), text.find(end)
    if i < 0 or j < i:
        raise SystemExit(f"markers {start} … {end} not found in the app")
    return text[: i + len(start)] + "\n" + value + "\n" + text[j:]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding="utf-8")
    site = Path(sys.argv[1]).read_text(encoding="utf-8")
    app_path = Path(sys.argv[2])
    app = app_path.read_text(encoding="utf-8")

    fonts = [line.replace("url(../assets/", "url(../../assets/") for line in site.splitlines() if line.startswith("@font-face")]
    if len(fonts) < 5:
        raise SystemExit(f"expected the website's @font-face rules, found {len(fonts)}")

    i = site.index('<svg width="0" height="0" style="position:absolute"')
    sprite = site[i: site.index("</svg>", i) + len("</svg>")]

    ti = site.index("const T = {")
    body = site[ti: site.index("\n};", ti)]
    s = r"'(?:[^'\\]|\\.)*'"
    found = {m.group(1): m.group(0) for m in re.finditer(r"(\w+):\[(" + s + r"),\s*(" + s + r"),\s*(" + s + r")\]", body)}
    missing = [k for k in SHARED if k not in found]
    if missing:
        raise SystemExit(f"strings missing on the website: {missing}")
    strings = "  // shared with the website (same wording); refreshed by tools/sync_app.py\n" + "\n".join("  " + found[k] + "," for k in SHARED)

    app = fill(app, "/*@FONTS*/", "/*@/FONTS*/", "\n".join(fonts))
    app = fill(app, "<!--@SPRITE-->", "<!--@/SPRITE-->", sprite)
    app = fill(app, "/*@SITE_T*/", "/*@/SITE_T*/", strings)
    app_path.write_text(app, encoding="utf-8")
    print(f"{app_path}: {len(fonts)} fonts, {sprite.count('<symbol')} icons, {len(SHARED)} shared strings")


if __name__ == "__main__":
    main()
