"""
make_report_html.py — render NOAA_RI_observation_report.md to a clean, printable,
self-contained HTML document (no external assets) for local download / save-as-PDF.

  python make_report_html.py
"""
import pathlib, base64, re, markdown

DIR = pathlib.Path(__file__).parent
MD  = DIR / 'NOAA_RI_observation_report.md'
OUT = DIR / 'NOAA_RI_observation_report.html'

html_body = markdown.markdown(MD.read_text(encoding='utf-8'),
                              extensions=['tables', 'toc', 'sane_lists', 'attr_list'])

# inline local figure PNGs as base64 so the HTML is fully self-contained / portable
def _inline(m):
    p = DIR / m.group(1)
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:image/png;base64,{b64}"'
    return m.group(0)
html_body = re.sub(r'src="([^"]+\.png)"', _inline, html_body)

CSS = """
:root{--ink:#16222e;--mute:#5b6b78;--line:#e2e8ee;--amber:#c9700f;--red:#c0392b;--accent:#0d6b73;--bg:#fbfcfd}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.62 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.doc{max-width:860px;margin:0 auto;padding:56px 40px 96px}
h1{font-size:30px;line-height:1.2;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:22px;margin:42px 0 10px;padding-top:14px;border-top:1px solid var(--line)}
h3{font-size:16.5px;margin:26px 0 6px;color:var(--accent)}
h1+h3{color:var(--mute);font-weight:600;border:0;margin-top:0}
p,li{color:#26323d}
a{color:var(--accent)}
strong{color:var(--ink)}
em{color:var(--mute)}
hr{border:0;border-top:1px solid var(--line);margin:34px 0}
table{border-collapse:collapse;width:100%;margin:16px 0;font-size:14.5px}
th,td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
th{background:#eef3f6;font-weight:700}
tr:nth-child(even) td{background:#f6f9fb}
code{background:#eef3f6;border-radius:4px;padding:1px 5px;font:13.5px ui-monospace,SFMono-Regular,Menlo,monospace}
blockquote{margin:0;padding:2px 16px;border-left:3px solid var(--amber);color:var(--mute)}
img{display:block;max-width:100%;margin:24px auto 4px;border:1px solid var(--line);border-radius:8px;box-shadow:0 1px 5px rgba(0,0,0,.07)}
img + em{display:block;text-align:center;color:var(--mute);font-size:13px;line-height:1.5;max-width:830px;margin:0 auto 24px}
@media print{img{break-inside:avoid}}
.banner{background:linear-gradient(135deg,#0d2436,#123a44);color:#eaf3f5;border-radius:14px;
  padding:22px 26px;margin:0 0 28px}
.banner .k{font:11px/1 ui-monospace,monospace;letter-spacing:.18em;color:#7fd4da;text-transform:uppercase}
.banner h1{color:#fff;margin-top:8px}
.print{position:fixed;top:16px;right:16px;background:var(--accent);color:#fff;border:0;border-radius:8px;
  padding:9px 16px;font:600 13px sans-serif;cursor:pointer;box-shadow:0 3px 10px rgba(0,0,0,.18)}
@media print{.print{display:none}body{background:#fff}.doc{padding:0}h2{break-before:auto}}
"""

PAGE = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Understanding Hurricane Rapid Intensification Dynamics — RapidWatch</title>
<style>{CSS}</style></head><body>
<button class="print" onclick="window.print()">Save / Print as PDF</button>
<div class="doc">
<div class="banner"><div class="k">RapidWatch · independent analysis · not for distribution</div></div>
{html_body}
</div></body></html>"""

OUT.write_text(PAGE, encoding='utf-8')
print(f"Wrote {OUT.name}  ({OUT.stat().st_size//1024} KB)")
