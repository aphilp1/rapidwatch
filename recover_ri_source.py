"""
Extracts the original RI Observatory content from the corrupted (self-nested)
rapidwatch-gulf-ri.html and saves it as a clean standalone source file:
  rapidwatch-gulf-ri-source.html

After running this once, the assembler will use -source.html as its input
and will never overwrite it again.
"""
import pathlib, sys

DIR = pathlib.Path(r'C:\Users\aphil\Documents\RapidWatch')
SRC_ASSEMBLED = DIR / 'rapidwatch-gulf-ri.html'
OUT_SOURCE    = DIR / 'rapidwatch-gulf-ri-source.html'

text = SRC_ASSEMBLED.read_text(encoding='utf-8')

# ── 1. extract RI CSS (first <style>...</style> block) ───────────────────────
css_start = text.index('<style>') + len('<style>')
css_end   = text.index('</style>', css_start)
ri_css    = text[css_start:css_end]
print('  RI CSS extracted: {:,} chars'.format(len(ri_css)))

# ── 2. extract RI body
#    The actual RI observatory body starts with its OWN sticky topbar:
#      <div class="topbar">
#    The assembly template uses id="tabbar" not class="topbar".
#    The LAST occurrence of <div class="topbar"> is the real one.
TOPBAR_TAG = '<div class="topbar">'
last_topbar = text.rfind(TOPBAR_TAG)
if last_topbar == -1:
    print('FAIL  could not find <div class="topbar"> in assembled file')
    sys.exit(1)

# The RI body ends at </footer> — find the first one after the topbar
FOOTER_CLOSE = '</footer>'
footer_end = text.index(FOOTER_CLOSE, last_topbar) + len(FOOTER_CLOSE)
ri_body = text[last_topbar:footer_end]
print('  RI body extracted: {:,} chars  (lines ~{} to ~{})'.format(
    len(ri_body),
    text[:last_topbar].count('\n') + 1,
    text[:footer_end].count('\n') + 1,
))

# ── 3. RI JS
#    The IntersectionObserver script — since the CSS already forces
#    opacity:1 on .reveal elements in the combined file, this script
#    is a clean rebuild of the original functionality.
ri_js = """// scroll-reveal
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));
"""

# ── 4. write clean standalone source file ────────────────────────────────────
source_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RAPIDWATCH — Gulf RI Observatory</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{ri_css}
</style>
</head>
<body>
{ri_body}
<script>
{ri_js}
</script>
</body>
</html>
"""

OUT_SOURCE.write_text(source_html, encoding='utf-8')
print('  Written ->', OUT_SOURCE)

# ── 5. verify ─────────────────────────────────────────────────────────────────
v = OUT_SOURCE.read_text(encoding='utf-8')
checks = [
    ('has topbar',         '<div class="topbar">' in v),
    ('has hero section',   'class="hero"' in v),
    ('has footer',         '<footer>' in v),
    ('has reveal class',   'class="reveal"' in v or '"eyebrow reveal"' in v),
    ('no id=tabbar',       'id="tabbar"' not in v),
    ('no id=panel-ri',     'id="panel-ri"' not in v),
    ('no id=panel-map',    'id="panel-map"' not in v),
    ('has script',         '<script>' in v),
]
print()
all_ok = True
for desc, passed in checks:
    mark = 'PASS' if passed else 'FAIL'
    if not passed: all_ok = False
    print('  {}  {}'.format(mark, desc))

if all_ok:
    print('\nSource file is clean. Now update assemble_rapidwatch.py to use:')
    print("  RI = DIR / 'rapidwatch-gulf-ri-source.html'")
sys.exit(0 if all_ok else 1)
