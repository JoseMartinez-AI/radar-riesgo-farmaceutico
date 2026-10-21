import sys
from pathlib import Path
esc = int(sys.argv[1]) if len(sys.argv) > 1 else 1
out = Path("data/raw/faers/2024-Q2-sintetico"); out.mkdir(parents=True, exist_ok=True)
M = {
 "FARMACO_A": {"REACCION_1":40,"REACCION_2":10,"REACCION_3":10,"OTRA":140},
 "FARMACO_B": {"REACCION_1":10,"REACCION_2":30,"REACCION_3":10,"OTRA":150},
 "FARMACO_C": {"REACCION_1":10,"REACCION_2":10,"REACCION_3":24,"OTRA":156},
 "FARMACO_D": {"REACCION_1":10,"REACCION_2":10,"REACCION_3":10,"OTRA":170},
 "FARMACO_E": {"REACCION_1":10,"REACCION_2":10,"REACCION_3":10,"OTRA":170},
 "FARMACO_F": {"REACCION_1":50,"REACCION_2":50,"REACCION_3":50,"OTRA":850},
}
demo = ["primaryid$caseid$caseversion$fda_dt$age$sex$occp_cod$reporter_country"]
drug = ["primaryid$drug_seq$role_cod$drugname$val_vbm"]
reac = ["primaryid$pt$drug_rec_act"]
pid = 100000
for f, rs in M.items():
    for r, n in rs.items():
        for _ in range(n * esc):
            pid += 1
            demo.append(f"{pid}$C{pid}$1$20240415$40$F$MD$PE")
            drug.append(f"{pid}$1$PS${f}$1")
            reac.append(f"{pid}${r}$1")
for nombre, filas in (("DEMO", demo), ("DRUG", drug), ("REAC", reac)):
    (out / f"{nombre}.txt").write_text("\n".join(filas) + "\n", encoding="latin-1")
print("Casos generados:", pid - 100000)
