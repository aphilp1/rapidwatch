"""
Assembles rapidwatch.html from rapidwatch-gulf-ri.html + rapidwatch-gulf-map.html.
v2: z-index stacking (both panels always rendered so Leaflet initialises correctly);
    #app{position:fixed} removed from map CSS; #panel-map is a flex column.
"""
import sys, pathlib

DIR = pathlib.Path(r'C:\Users\aphil\Documents\RapidWatch')
RI  = DIR / 'rapidwatch-gulf-ri-source.html'   # standalone RI source — never overwritten
MAP = DIR / 'rapidwatch-gulf-map.html'
OUT   = DIR / 'rapidwatch.html'
OUTRI = DIR / 'rapidwatch-gulf-ri.html'

def between(text, open_tag, close_tag, start=0):
    s = text.index(open_tag, start) + len(open_tag)
    e = text.index(close_tag, s)
    return text[s:e], e + len(close_tag)

ri_src  = RI.read_text(encoding='utf-8')
map_src = MAP.read_text(encoding='utf-8')

# ── extract sections ──────────────────────────────────────────────────────────
ri_css,  _        = between(ri_src,  '<style>', '</style>')
# Map has TWO style blocks: block 1 = inlined Leaflet CSS, block 2 = custom map CSS
leaflet_css, css1_end = between(map_src, '<style>', '</style>')
map_css,     _        = between(map_src, '<style>', '</style>', css1_end)
ri_body, _  = between(ri_src,  '<body>',  '<script>')

body_start = map_src.index('<body>')
map_body, _ = between(map_src, '<body>', '<script>', body_start)

# Leaflet block (first <script> in body)
leaf_start = map_src.index('<script>', body_start)
leaf_js, leaf_end = between(map_src, '<script>', '</script>', leaf_start)

# Map custom script (second <script> in body)
cust_start = map_src.index('<script>', leaf_end)
map_js, _  = between(map_src, '<script>', '</script>', cust_start)

ri_js, _   = between(ri_src, '<script>', '</script>')

# ── scrub custom map CSS rules that conflict with the tab panel system ────────
# 1. html,body height / overflow (tab system owns this)
map_css = map_css.replace(
    'html,body{margin:0;height:100%;background:var(--abyss);color:var(--ink);'
    'font-family:"IBM Plex Sans",system-ui,sans-serif;font-weight:300}',
    '/* html,body — owned by tab system */'
)
# 2. #app position:fixed (replaced by flex child inside #panel-map)
map_css = map_css.replace(
    '#app{position:fixed;inset:0;display:flex;flex-direction:column}',
    '/* #app layout — owned by tab system */'
)
print('  #app{position:fixed} removed from map CSS:',
      '#app{position:fixed' not in map_css)

# ── tab system CSS ────────────────────────────────────────────────────────────
TAB_CSS = """
/* ===== TAB SYSTEM ===== */
html,body{margin:0;overflow:hidden;height:100%;background:var(--abyss);
  color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;
  font-weight:300;-webkit-font-smoothing:antialiased}

/* shared top bar */
#tabbar{
  position:fixed;top:0;left:0;right:0;z-index:10000;height:50px;
  display:flex;align-items:center;gap:16px;padding:0 18px;
  background:rgba(5,11,18,.96);border-bottom:1px solid rgba(120,160,180,.18);
  backdrop-filter:blur(14px);
}
#tabbar .brand{display:flex;align-items:center;gap:10px;
  font-family:"Space Grotesk";font-weight:700;letter-spacing:.04em;font-size:14px;
  flex-shrink:0}
#tabbar .brand .dot{width:10px;height:10px;border-radius:50%;background:var(--amber);
  box-shadow:0 0 0 3px rgba(255,138,61,.16),0 0 14px 2px rgba(255,138,61,.5);
  animation:tbpulse 3.4s ease-in-out infinite}
@keyframes tbpulse{
  0%,100%{box-shadow:0 0 0 3px rgba(255,138,61,.18),0 0 14px 1px rgba(255,138,61,.45)}
  50%{box-shadow:0 0 0 5px rgba(255,138,61,.06),0 0 22px 4px rgba(255,138,61,.7)}}
#tabbar .brand small{display:block;font-family:"IBM Plex Mono";font-weight:400;
  font-size:9.5px;color:var(--mute);letter-spacing:.13em;margin-top:1px}
#tabbar .divider{width:1px;height:22px;background:rgba(120,160,180,.2)}
.tabs{display:flex;gap:4px}
.tab{font-family:"Space Grotesk";font-size:13px;font-weight:500;
  padding:6px 16px;border-radius:8px;border:1px solid transparent;
  color:var(--slate);background:none;cursor:pointer;transition:all .2s}
.tab:hover{color:var(--ink);background:rgba(255,255,255,.05)}
.tab.active{color:var(--amber);border-color:rgba(255,138,61,.3);
  background:rgba(255,138,61,.08)}

/* panels — BOTH always rendered (z-index swap, not display:none)
   so Leaflet initialises with a real container size */
.tab-panel{
  position:fixed;top:50px;left:0;right:0;bottom:0;
  z-index:1;pointer-events:none;
}
.tab-panel.active{z-index:2;pointer-events:auto}

/* RI panel */
#panel-ri{
  overflow-y:auto;overflow-x:hidden;
  /* opaque bg so the map panel behind it is not visible */
  background:
    radial-gradient(1200px 700px at 78% -8%,rgba(255,138,61,.10),transparent 60%),
    radial-gradient(1100px 800px at 10% 6%,rgba(70,207,214,.08),transparent 55%),
    linear-gradient(180deg,#06101a 0%,var(--abyss) 38%,#03070c 100%);
}
/* hide the RI Observatory's own sticky topbar — the combined tabbar replaces it */
#panel-ri .topbar{display:none !important}

/* the map CSS has .panel{position:absolute;z-index:1000} for its legend overlays.
   that leaks into the RI feature section's .panel grid cells and breaks layout.
   reset to normal document flow inside the RI panel. */
#panel-ri .panel{position:relative !important;z-index:auto !important;
  backdrop-filter:none !important;box-shadow:none !important}

/* scroll-reveal uses IntersectionObserver against the document viewport,
   which doesn't fire inside a fixed overflow container — force all
   .reveal elements visible so content is never stuck at opacity:0 */
#panel-ri .reveal{opacity:1 !important;transform:none !important}

/* Map panel: flex column so #app fills it */
#panel-map{overflow:hidden;display:flex;flex-direction:column}

/* Map app fills the panel as a flex child */
#panel-map #app{
  flex:1;min-height:0;
  position:relative !important;
  inset:auto !important;
  display:flex !important;
  flex-direction:column !important;
}
/* map tile area fills remaining height */
#panel-map #map{flex:1;min-height:0}

/* hide duplicate brand in map's own header */
#panel-map header .brand{display:none}
"""

# ── tab switcher JS ───────────────────────────────────────────────────────────
TAB_JS = """<script>
(function(){
  var tabs   = document.querySelectorAll('#tabbar .tab');
  var panels = document.querySelectorAll('.tab-panel');
  tabs.forEach(function(tab){
    tab.addEventListener('click', function(){
      tabs.forEach(function(t){t.classList.remove('active');});
      panels.forEach(function(p){p.classList.remove('active');});
      tab.classList.add('active');
      document.getElementById(tab.dataset.panel).classList.add('active');
      // Leaflet needs a size refresh whenever its container becomes the front layer
      if(tab.dataset.panel === 'panel-map'){
        setTimeout(function(){ if(typeof map!=='undefined') map.invalidateSize(); }, 60);
      }
    });
  });
})();
</script>"""

# ── assemble ──────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RAPIDWATCH — Gulf RI Observatory &amp; Geospatial Canvas</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{ri_css}
</style>
<!-- inlined Leaflet CSS -->
<style>
{leaflet_css}
</style>
<!-- map custom CSS -->
<style>
{map_css}
</style>
<style>
{TAB_CSS}
</style>
</head>
<body>

<div id="tabbar">
  <div class="brand"><span class="dot"></span><div>RAPIDWATCH<small>GULF RI OBSERVATORY</small></div></div>
  <div class="divider"></div>
  <div class="tabs">
    <button class="tab active" data-panel="panel-ri">RI Observatory</button>
    <button class="tab" data-panel="panel-map">Gulf Map</button>
  </div>
</div>

<div id="panel-ri" class="tab-panel active">
{ri_body}
</div>

<div id="panel-map" class="tab-panel">
{map_body}
</div>

<script>
{leaf_js}
</script>
<script>
{map_js}
</script>
<script>
{ri_js}
</script>
{TAB_JS}

</body>
</html>"""

OUT.write_text(html, encoding='utf-8')
OUTRI.write_text(html, encoding='utf-8')
print('Written ->', OUT)
print('Written ->', OUTRI)

# ── verify ────────────────────────────────────────────────────────────────────
v = OUT.read_text(encoding='utf-8')
checks = [
    ('tab bar present',              'id="tabbar"' in v),
    ('RI panel present',             'id="panel-ri"' in v),
    ('Map panel present',            'id="panel-map"' in v),
    ('Leaflet L.map call present',   'L.map(' in v),
    ('stormLayers in map JS',        'stormLayers' in v),
    ('#app fixed rule removed',      '#app{position:fixed' not in v),
    ('panel-map flex layout',        '#panel-map{overflow:hidden;display:flex' in v or
                                     'display:flex;flex-direction:column' in v),
    ('RI topbar hidden',             '#panel-ri .topbar{display:none' in v),
    ('map.invalidateSize present',   'invalidateSize' in v),
    ('z-index stacking (not hide)',  'z-index:2' in v and 'display:none' not in v.split('tab-panel')[1][:200]),
]
print()
all_ok = True
for desc, passed in checks:
    mark = 'PASS' if passed else 'FAIL'
    if not passed: all_ok = False
    print(f'  {mark}  {desc}')

sys.exit(0 if all_ok else 1)
