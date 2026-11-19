"""Build the standalone demo page (arenax.in/hisaabo/demo/) from the website, and optionally the pitch copy.

The demo page is the website in demo mode: the same code and the same fictional data, with
`data-page="demo"` on <html>, so only the demo intro, the month at a glance, the live demo
(supervisor app and contractor dashboard) and the contact band show. Paths move one folder down.

    py -I hisaabo/tools/build_demo_page.py hisaabo/index.html hisaabo/demo/index.html \
        [--pitch C:\\Users\\Kamal\\Projects\\ArenaX\\private\\hisaabo-demo-pitch.html]

--pitch writes one self-contained file (fonts and icon embedded, app links to the published app)
for sending on WhatsApp; it lives outside every repository and is never committed.
Run after every change to hisaabo/index.html or its data.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_demo_data import embed_fonts  # noqa: E402

TITLE = "Hisaabo demo · From attendance to accounts"
DESC = "Hisaabo by ArenaX, live demo with a fictional contractor: the supervisor app and the contractor dashboard. A product of ArenaX Digital Solutions."


def demo_mode(html: str) -> str:
    html = html.replace('<html lang="en" data-lang="en" data-build="public">', '<html lang="en" data-lang="en" data-build="public" data-page="demo">', 1)
    assert 'data-page="demo"' in html, "the <html> tag changed; update build_demo_page.py"
    html = re.sub(r"<title>[^<]*</title>", f"<title>{TITLE}</title>", html, count=1)
    html = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{DESC}">', html, count=1)
    html = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{TITLE}">', html, count=1)
    html = html.replace('<meta property="og:url" content="https://arenax.in/hisaabo/">', '<meta property="og:url" content="https://arenax.in/hisaabo/demo/">')
    html = html.replace('<link rel="canonical" href="https://arenax.in/hisaabo/">', '<link rel="canonical" href="https://arenax.in/hisaabo/demo/">')
    html = html.replace('href="#top" class="logo"', 'href="../" class="logo"')
    return html


def one_folder_down(html: str) -> str:
    html = html.replace("url(../assets/", "url(../../assets/").replace('href="../assets/', 'href="../../assets/')
    html = html.replace('href="assets/', 'href="../assets/').replace('src="assets/', 'src="../assets/')
    html = html.replace('href="app/"', 'href="../app/"').replace('href="demo/"', 'href="./"')
    html = html.replace('class="navhome" data-t="back_home">', 'class="navhome" data-t="back_home">', 1)
    return html


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--pitch", type=Path, help="also write a self-contained copy here (outside the repository)")
    a = ap.parse_args()
    site = a.site.read_text(encoding="utf-8")
    if 'data-build="public"' not in site:
        sys.exit("the website must be the public build (fictional data) before the demo page is made")
    page = one_folder_down(demo_mode(site))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(page, encoding="utf-8")
    print(f"wrote {a.out} ({a.out.stat().st_size // 1024} KB)")
    if a.pitch:
        pitch = embed_fonts(demo_mode(site), a.site.parent).replace('data-build="public"', 'data-build="pitch"', 1)
        pitch = pitch.replace('href="../"', 'href="https://arenax.in/hisaabo/"')
        a.pitch.parent.mkdir(parents=True, exist_ok=True)
        a.pitch.write_text(pitch, encoding="utf-8")
        print(f"pitch copy written to {a.pitch} ({a.pitch.stat().st_size // 1024} KB, fictional data, self-contained; never commit)")


if __name__ == "__main__":
    main()
