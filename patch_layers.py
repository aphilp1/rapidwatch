import shutil, sys, pathlib

HTML = pathlib.Path(r'C:\Users\aphil\Documents\RapidWatch\rapidwatch-gulf-map.html')
BAK  = HTML.with_suffix('.html.bak')

# ── backup ──────────────────────────────────────────────────────────────────
shutil.copy(HTML, BAK)
print('Backup  ->', BAK)

src = HTML.read_text(encoding='utf-8')

# Genesis-label line contains ’ (curly right single quote), not U+0027.
# Build both marker lines with the correct codepoint via explicit escape.
_GENESIS_OLD = (
    "  L.marker([g.lat,g.lon],{icon:L.divIcon({className:'',html:`<div style=\"color:#cdd9e1;"
    "font:600 11px 'Space Grotesk';white-space:nowrap;text-shadow:0 0 6px #050b12,0 0 6px #050b12"
    "\">${s.name} ’${String(s.year).slice(2)}</div>`,iconSize:[0,0]})}).addTo(trackLayer);\n"
)
_GENESIS_NEW = (
    "  L.marker([g.lat,g.lon],{icon:L.divIcon({className:'',html:`<div style=\"color:#cdd9e1;"
    "font:600 11px 'Space Grotesk';white-space:nowrap;text-shadow:0 0 6px #050b12,0 0 6px #050b12"
    "\">${s.name} ’${String(s.year).slice(2)}</div>`,iconSize:[0,0]})}).addTo(lyr);\n"
)

# ── patch 1 : one layerGroup per storm, keyed by name ───────────────────────
OLD_TRACK = (
    "const trackLayer=L.layerGroup();\n"
    "STORMS.forEach(s=>{\n"
    "  const latlngs=s.pts.map(p=>[p.lat,p.lon]);\n"
    "  // connecting path\n"
    "  L.polyline(latlngs,{color:'#cdd9e1',weight:1.2,opacity:.32}).addTo(trackLayer);\n"
    "  // genesis label\n"
    "  const g=s.pts[0];\n"
    + _GENESIS_OLD +
    "  s.pts.forEach(p=>{\n"
    "    // RI halo\n"
    "    if(p.ri) L.circleMarker([p.lat,p.lon],{radius:9,color:'#ff8a3d',weight:1.6,opacity:.9,fill:false,dashArray:'2,2'}).addTo(trackLayer);\n"
    "    // category dot\n"
    "    L.circleMarker([p.lat,p.lon],{radius:p.land?6:4.5,color:p.land?'#ffffff':'#04101a',weight:p.land?2:1,fillColor:SS[p.cat]||'#6b8a9e',fillOpacity:1})\n"
    "      .bindPopup(pop((p.land?'Landfall · ':'')+'Best track fix','',`${s.name} (${s.year})`,\n"
    "        `${p.lat.toFixed(1)}°N ${Math.abs(p.lon).toFixed(1)}°W · ${p.t}`,\n"
    "        `${p.w} kt — ${p.cat}${p.mb?` · ${p.mb} mb`:''}${p.ri?' · rapidly intensifying (+30 kt/24 h)':''}${p.land?' · landfall':''}`,\n"
    "        p.ri?['RI']:null)).addTo(trackLayer);\n"
    "  });\n"
    "});"
)

NEW_TRACK = (
    "const stormLayers={};\n"
    "STORMS.forEach(s=>{\n"
    "  const lyr=L.layerGroup();\n"
    "  stormLayers[s.name]=lyr;\n"
    "  const latlngs=s.pts.map(p=>[p.lat,p.lon]);\n"
    "  L.polyline(latlngs,{color:'#cdd9e1',weight:1.2,opacity:.32}).addTo(lyr);\n"
    "  const g=s.pts[0];\n"
    + _GENESIS_NEW +
    "  s.pts.forEach(p=>{\n"
    "    if(p.ri) L.circleMarker([p.lat,p.lon],{radius:9,color:'#ff8a3d',weight:1.6,opacity:.9,fill:false,dashArray:'2,2'}).addTo(lyr);\n"
    "    L.circleMarker([p.lat,p.lon],{radius:p.land?6:4.5,color:p.land?'#ffffff':'#04101a',weight:p.land?2:1,fillColor:SS[p.cat]||'#6b8a9e',fillOpacity:1})\n"
    "      .bindPopup(pop((p.land?'Landfall · ':'')+'Best track fix','',`${s.name} (${s.year})`,\n"
    "        `${p.lat.toFixed(1)}°N ${Math.abs(p.lon).toFixed(1)}°W · ${p.t}`,\n"
    "        `${p.w} kt — ${p.cat}${p.mb?` · ${p.mb} mb`:''}${p.ri?' · rapidly intensifying (+30 kt/24 h)':''}${p.land?' · landfall':''}`,\n"
    "        p.ri?['RI']:null)).addTo(lyr);\n"
    "  });\n"
    "});"
)

# ── patch 2 : four registry entries instead of one ──────────────────────────
OLD_REG = " {key:'Hurricane best tracks · RI in amber',lyr:trackLayer,on:true,heat:true},"
NEW_REG  = (
    " {key:'Katrina 2005 · RI in amber',lyr:stormLayers['Katrina'],on:true,heat:true},\n"
    " {key:'Rita 2005 · RI in amber',lyr:stormLayers['Rita'],on:true,heat:true},\n"
    " {key:'Helene 2024 · RI in amber',lyr:stormLayers['Helene'],on:true,heat:true},\n"
    " {key:'Milton 2024 · RI in amber',lyr:stormLayers['Milton'],on:true,heat:true},"
)

# ── apply patches, abort if either search string not found exactly once ──────
failed = False
for label, old, new in [
    ('track-layer block', OLD_TRACK, NEW_TRACK),
    ('registry entry',    OLD_REG,   NEW_REG),
]:
    n = src.count(old)
    if n != 1:
        print('FAIL  "' + label + '" matched', n, 'time(s) -- expected exactly 1; aborting')
        failed = True
    else:
        src = src.replace(old, new, 1)
        print('OK    patched:', label)

if failed:
    sys.exit(1)

HTML.write_text(src, encoding='utf-8')
print('Written ->', HTML)

# ── self-verify ──────────────────────────────────────────────────────────────
v = HTML.read_text(encoding='utf-8')
checks = [
    ('stormLayers={} introduced',             'stormLayers={}' in v),
    ('old trackLayer=L.layerGroup() gone',    'const trackLayer=L.layerGroup()' not in v),
    ('Katrina 2005 in registry',              "key:'Katrina 2005" in v),
    ('Rita 2005 in registry',                 "key:'Rita 2005"    in v),
    ('Helene 2024 in registry',               "key:'Helene 2024"  in v),
    ('Milton 2024 in registry',               "key:'Milton 2024"  in v),
    ('old combined key gone',                 "key:'Hurricane best tracks" not in v),
]

all_ok = True
print('\nVerification:')
for desc, passed in checks:
    mark = 'PASS' if passed else 'FAIL'
    if not passed:
        all_ok = False
    print('  ' + mark + '  ' + desc)

sys.exit(0 if all_ok else 1)
