import sys, pandas as pd
from pathlib import Path
d = Path(sys.argv[1])
def leer(pref):
    f = next(p for p in d.rglob("*") if p.suffix.lower() == ".txt" and p.stem.upper().startswith(pref))
    return pd.read_csv(f, sep="$", encoding="latin-1", dtype=str, low_memory=False, on_bad_lines="skip")
demo, drug, reac = leer("DEMO"), leer("DRUG"), leer("REAC")
print("Filas DEMO, DRUG, REAC:", len(demo), len(drug), len(reac))
ids = set(demo.primaryid)
for n, t in (("DRUG", drug), ("REAC", reac)):
    h = (~t.primaryid.isin(ids)).sum()
    print(f"Huerfanos {n}: {h} ({h/len(t)*100:.3f}%)")
print("caseid duplicados:", demo.caseid.duplicated().sum())
campo = "prod_ai" if "prod_ai" in drug.columns else "drugname"
con_f = set(drug.loc[drug[campo].notna(), "primaryid"]); con_r = set(reac.loc[reac["pt"].notna(), "primaryid"])
ok = demo.primaryid.isin(con_f) & demo.primaryid.isin(con_r) & demo["fda_dt"].notna()
print(f"Completitud (farmaco, reaccion y fecha fda_dt): {ok.mean()*100:.2f}%")
