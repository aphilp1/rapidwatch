"""
make_readme_html.py — render README.md to a clean, printable, self-contained
README.html (no external assets), matching the RapidWatch report house style.

  python make_readme_html.py
"""
import pathlib, markdown

DIR = pathlib.Path(__file__).parent
MD  = DIR / 'README.md'
OUT = DIR / 'README.html'

html_body = markdown.markdown(MD.read_text(encoding='utf-8'),
                              extensions=['tables', 'toc', 'sane_lists', 'attr_list', 'fenced_code'])

CSS = """
:root{--ink:#16222e;--mute:#5b6b78;--line:#e2e8ee;--amber:#c9700f;--red:#c0392b;--accent:#0d6b73;--bg:#fbfcfd}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.62 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.doc{max-width:860px;margin:0 auto;padding:40px 40px 96px}
h1{font-size:29px;line-height:1.2;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:21px;margin:40px 0 10px;padding-top:14px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:24px 0 6px;color:var(--accent)}
p,li{color:#26323d}
a{color:var(--accent);word-break:break-word}
strong{color:var(--ink)}
em{color:var(--mute)}
hr{border:0;border-top:1px solid var(--line);margin:34px 0}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14.5px}
th,td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
th{background:#eef3f6;font-weight:700}
tr:nth-child(even) td{background:#f6f9fb}
code{background:#eef3f6;border-radius:4px;padding:1px 5px;font:13px ui-monospace,SFMono-Regular,Menlo,monospace}
pre{background:#0d1b26;color:#dbe7ee;border-radius:10px;padding:16px 18px;overflow:auto;line-height:1.5;font-size:13px}
pre code{background:none;color:inherit;padding:0}
blockquote{margin:0;padding:2px 16px;border-left:3px solid var(--amber);color:var(--mute)}
@media print{pre{break-inside:avoid;white-space:pre-wrap}body{background:#fff}.doc{padding:0}.print{display:none}}
.print{position:fixed;top:16px;right:16px;background:var(--accent);color:#fff;border:0;border-radius:8px;
  padding:9px 16px;font:600 13px sans-serif;cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,.18)}
.banner{background:linear-gradient(135deg,#0d2436,#123a44);color:#eaf3f5;border-radius:14px;
  padding:22px 26px;margin:0 0 28px}
.banner .k{font:11px/1 ui-monospace,monospace;letter-spacing:.18em;color:#7fd4da;text-transform:uppercase}
.banner h1{color:#fff;margin:8px 0 0;border:0;padding:0}
/* the README's own H1 is replaced by the banner */
.doc > h1:first-of-type{display:none}
"""

PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RapidWatch — README</title>
<style>{CSS}</style></head><body>
<button class="print" onclick="window.print()">Save / Print as PDF</button>
<div class="doc">
<div class="banner"><div class="k">RapidWatch · project README</div>
<h1>Gulf Rapid Intensification Observatory</h1></div>
{html_body}
</div></body></html>"""

OUT.write_text(PAGE, encoding='utf-8')
print(f"Wrote {OUT.name}  ({OUT.stat().st_size//1024} KB)")
