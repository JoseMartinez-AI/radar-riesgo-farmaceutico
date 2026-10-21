import sqlite3, sys
SENAL = {("FARMACO_A","REACCION_1"),("FARMACO_B","REACCION_2"),("FARMACO_C","REACCION_3")}
q = """SELECT f.principio_activo, r.termino_preferido, s.prr, s.chi_cuadrado, s.nivel_riesgo
       FROM fact_senales_riesgo s JOIN dim_farmaco f USING(farmaco_id) JOIN dim_reaccion r USING(reaccion_id)"""
vp = fp = fn = vn = 0
for f, r, prr, chi, niv in sqlite3.connect(sys.argv[1]).execute(q):
    real = (f, r) in SENAL; pred = niv == "Alto"
    vp += real and pred; fn += real and not pred; fp += (not real) and pred; vn += (not real) and not pred
    print(f"{f} | {r} | PRR={prr} chi2={chi} | nivel={niv} | referencia={'senal' if real else 'sin senal'}")
print(f"VP={vp} FP={fp} FN={fn} VN={vn}")
print(f"Sensibilidad={vp/(vp+fn)*100:.1f}%  Precision={(vp/(vp+fp)*100 if vp+fp else 0):.1f}%  Especificidad={vn/(vn+fp)*100:.1f}%")
