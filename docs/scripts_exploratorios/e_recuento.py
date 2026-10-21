import sys, sqlite3, math, pandas as pd
from pathlib import Path
folder, db = Path(sys.argv[1]), sys.argv[2]
def leer(pref):
    f = next(p for p in folder.rglob("*") if p.suffix.lower() == ".txt" and p.stem.upper().startswith(pref))
    df = pd.read_csv(f, sep="$", encoding="latin-1", dtype=str, low_memory=False, on_bad_lines="skip")
    df.columns = df.columns.str.lower().str.strip()
    return df
demo, drug, reac = leer("DEMO"), leer("DRUG"), leer("REAC")
demo["v"] = pd.to_numeric(demo["caseversion"], errors="coerce").fillna(0)
demo = demo.sort_values("v").drop_duplicates("caseid", keep="last")
ids = set(demo.primaryid); N = len(ids)
drug = drug[drug.primaryid.isin(ids)]; reac = reac[reac.primaryid.isin(ids)]
q = """SELECT f.principio_activo, r.termino_preferido, s.casos_farmaco_reaccion, s.casos_farmaco_otras_reac,
       s.casos_otros_farmacos_reac, s.casos_otros_farmacos_otras_reac, s.prr, s.ror, s.chi_cuadrado, s.nivel_riesgo
       FROM fact_senales_riesgo s JOIN dim_farmaco f USING(farmaco_id) JOIN dim_reaccion r USING(reaccion_id)"""
filas = sqlite3.connect(db).execute(q).fetchall()
def eq(manual, bd):
    return (math.isnan(manual) and bd == 0) or abs(round(manual, 2) - bd) <= 0.011
ok = 0
print("farmaco | reaccion | BD(a,b,c,d) | manual(a,b,c,d) | PRR bd/manual | ROR bd/manual | chi2 bd/manual | nivel bd | coincide")
for f, r, a_, b_, c_, d_, prr_bd, ror_bd, chi_bd, niv in filas:
    idf = set(drug.loc[drug.drugname.str.strip().str.upper() == f.upper(), "primaryid"])
    idr = set(reac.loc[reac.pt.str.strip().str.upper() == r.upper(), "primaryid"])
    a = len(idf & idr); b = len(idf) - a; c = len(idr) - a; d = N - a - b - c
    prr = (a/(a+b))/(c/(c+d)) if (a+b) and (c+d) and c else float("nan")
    ror = (a*d)/(b*c) if b*c else float("nan")
    den = (a+b)*(c+d)*(a+c)*(b+d)
    chi = N*(abs(a*d-b*c)-N/2)**2/den if den else float("nan")
    same = (a, b, c, d) == (a_, b_, c_, d_) and eq(prr, prr_bd) and eq(ror, ror_bd)
    ok += same
    print(f"{f} | {r} | {a_},{b_},{c_},{d_} | {a},{b},{c},{d} | {prr_bd}/{prr:.2f} | {ror_bd}/{ror:.2f} | {chi_bd}/{chi:.2f} | {niv} | {'Si' if same else 'NO'}")
print(f"Casos tras deduplicar: {N} | Coinciden {ok} de {len(filas)}")
