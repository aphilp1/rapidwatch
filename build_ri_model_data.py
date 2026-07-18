"""Build data/ri_model/ri_model_outputs.json for the RI Model tab.

Source of every number: the gulf-ri-model repo's real outputs —
  results/baseline_loso_predictions.csv  (leave-one-storm-out probabilities,
      commit 9d6acfb; thresholds 25/30/35/40 kt)
  data/processed/hurdat2_atlantic.csv    (best-track intensity for context)
  results/baseline_summary.csv           (skill scores)
  results/baseline_podfar_logi_30kt.csv  (catch/false-alarm table)

Storms included: every storm in the modeling sample with at least one
forecast point inside the Gulf box (18-31N, 82-98W). No synthetic or
placeholder values anywhere (standing no-fake-data rule).
"""
import json
import pathlib

import pandas as pd

GRM = pathlib.Path(r"C:\Users\aphil\Documents\gulf-ri-model")
OUT = pathlib.Path(r"C:\Users\aphil\Documents\RapidWatch\data\ri_model")
OUT.mkdir(parents=True, exist_ok=True)

pred = pd.read_csv(GRM / "results" / "baseline_loso_predictions.csv")
pred["t"] = pd.to_datetime(pred[["year", "month", "day", "hour"]])
hur = pd.read_csv(GRM / "data" / "processed" / "hurdat2_atlantic.csv")
hur["t"] = pd.to_datetime(hur[["year", "month", "day", "hour"]])

# full storm names from HURDAT2 (predictions carry only 4-letter stubs)
names = hur.groupby("atcf_id")["name"].first()

gulf_storms = sorted(pred.loc[pred.gulf, "atcf_id"].unique())
storms = []
for sid in gulf_storms:
    p = pred[pred.atcf_id == sid].sort_values("t")
    tr = hur[hur.atcf_id == sid].sort_values("t")
    t0 = p.t.min() - pd.Timedelta("48h")
    t1 = p.t.max() + pd.Timedelta("72h")
    tr = tr[(tr.t >= t0) & (tr.t <= t1)]
    nm = str(names.get(sid, p.name.iloc[0])).title()
    storms.append({
        "id": sid,
        "nm": nm,
        "yr": int(p.year.iloc[0]),
        "maxp": round(float(p.p_logi_30.max()), 3),
        "peak": int(tr.vmax.max()) if len(tr) else int(p.vmax0.max()),
        "fixes": [
            {"t": r.t.strftime("%Y-%m-%dT%H:00Z"),
             "lat": round(r.lat0, 2), "lon": round(-r.lon0, 2),
             "v": int(r.vmax0), "dv": int(r.delv_24),
             "g": bool(r.gulf),
             "p": [round(float(r.p_logi_25), 3), round(float(r.p_logi_30), 3),
                   round(float(r.p_logi_35), 3), round(float(r.p_logi_40), 3)]}
            for r in p.itertuples()],
        "track": [
            {"t": r.t.strftime("%Y-%m-%dT%H:00Z"),
             "lat": round(r.lat, 2), "lon": round(-r.lon, 2),
             "v": int(r.vmax)}
            for r in tr.itertuples()],
    })

summ = pd.read_csv(GRM / "results" / "baseline_summary.csv")
podfar = pd.read_csv(GRM / "results" / "baseline_podfar_logi_30kt.csv")


def bss(model, thr):
    row = summ[(summ.model == model) & (summ.threshold_kt == thr)]
    return float(row.bss_pct.iloc[0]) if len(row) else None


pred["ri"] = pred.delv_24 >= 30
in_set = pred.atcf_id.isin(gulf_storms)
best = pred[pred.ri & in_set].nlargest(6, "p_logi_30")
miss = pred[pred.ri & pred.gulf].nsmallest(5, "p_logi_30")


def leader(df):
    return [{"id": r.atcf_id, "nm": str(names.get(r.atcf_id, r.name)).title(),
             "yr": int(r.year), "t": r.t.strftime("%b %d %HZ"),
             "v": int(r.vmax0), "dv": int(r.delv_24),
             "p": round(float(r.p_logi_30), 3)} for r in df.itertuples()]


meta = {
    "built_from": "aphilp1/gulf-ri-model results (LOSO baseline, commit 9d6acfb)",
    "n_cases": 8806, "n_storms": 538, "years": "1982-2023",
    "base_rate": [10.80, 6.61, 3.72, 2.21],   # 25/30/35/40 kt, all-basin %
    "thresholds": [25, 30, 35, 40],
    "bss": {"all30": bss("LOGI", 30), "gulf30": bss("LOGI-Gulf", 30),
            "all25": bss("LOGI", 25), "gulf25": bss("LOGI-Gulf", 25)},
    "coef": [["PER", 0.72, "12-h intensity trend"],
             ["SHRD", -0.78, "wind shear"],
             ["POT", 0.54, "room to grow"],
             ["OHC", 0.22, "ocean heat"],
             ["D200", 0.17, "upper outflow"],
             ["RHLO", 0.13, "mid-level moisture"]],
    "podfar": [[int(r.prob_thresh_pct), int(r.hits), int(r.hits + r.misses),
                int(r.false_alarms), round(float(r.POD), 2),
                round(float(r.FAR), 2)] for r in podfar.itertuples()],
    "best_calls": leader(best),
    "worst_misses": leader(miss),
}

out = {"meta": meta, "storms": storms}
path = OUT / "ri_model_outputs.json"
path.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
n_fix = sum(len(s["fixes"]) for s in storms)
n_trk = sum(len(s["track"]) for s in storms)
print(f"{len(storms)} Gulf storms, {n_fix} fixes, {n_trk} track points "
      f"-> {path} ({path.stat().st_size / 1e6:.2f} MB)")
