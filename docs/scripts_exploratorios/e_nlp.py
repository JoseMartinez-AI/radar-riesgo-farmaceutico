import sys, json
sys.path.insert(0, ".")
from pathlib import Path
from src.nlp.extractor import clean_clinical_text, detect_risk_signals_in_text
from src.pipeline.scraper import parse_html_alert

def prediccion(res):
    """Devuelve (clave usada, True si el NLP detecta riesgo)."""
    for k, v in res.items():
        if isinstance(v, list):
            return k, len(v) > 0
    for k, v in res.items():
        if isinstance(v, bool):
            return k, v
    for k, v in res.items():
        if isinstance(v, int):
            return k, v > 0
    return None, False

print("=== PARTE 1: alertas reales de DIGEMID ===")
for p in sorted(Path("data/raw/digemid").glob("*.html")):
    a = parse_html_alert(p.read_text(encoding="utf-8", errors="ignore"))
    res = detect_risk_signals_in_text(a["contenido"], lang="es")
    print(p.name, "|", a["titulo"])
    print("   resultado:", json.dumps(res, ensure_ascii=False, default=str))

# Muestra etiquetada a mano ANTES de ejecutar. 1 = menciona un riesgo, 0 = no.
# Las frases 9, 10, 19 y 20 son casos dificiles (sinonimos y negaciones).
MUESTRA = [
 ("El valproato puede causar malformaciones congenitas graves cuando se usa durante el embarazo.", 1),
 ("Se han notificado casos de hepatotoxicidad grave, incluida insuficiencia hepatica fatal.", 1),
 ("El uso de clozapina se asocia a agranulocitosis potencialmente mortal y requiere control de leucocitos.", 1),
 ("El producto esta contraindicado en pacientes con hipersensibilidad conocida al principio activo.", 1),
 ("Se ha reportado arritmia ventricular y prolongacion del intervalo QT con el uso de domperidona.", 1),
 ("La amiodarona puede producir toxicidad pulmonar, incluida fibrosis pulmonar irreversible.", 1),
 ("Existe riesgo de pancreatitis hemorragica con desenlace fatal en menores de dos anos.", 1),
 ("La isotretinoina es teratogenica y esta contraindicada en mujeres embarazadas.", 1),
 ("Esta medicina puede dañar al bebe durante la gestacion; evite usarla si espera un hijo.", 1),
 ("Pueden presentarse reacciones que ponen en peligro la vida y requieren atencion de emergencia.", 1),
 ("Conservar el producto a temperatura no mayor de 30 grados, protegido de la luz y la humedad.", 0),
 ("Cada tableta contiene 500 mg de principio activo y excipientes c.s.p.", 0),
 ("Para mayor informacion comunicarse con la Direccion General de Medicamentos, Insumos y Drogas.", 0),
 ("El envase contiene 30 tabletas recubiertas en blister de aluminio.", 0),
 ("La presente alerta se publica para conocimiento de los profesionales de la salud.", 0),
 ("El titular del registro sanitario es el laboratorio indicado en la etiqueta.", 0),
 ("Tomar con un vaso de agua despues de los alimentos.", 0),
 ("Via de administracion oral; presentacion en frasco de 120 mililitros.", 0),
 ("No se han reportado casos de hepatotoxicidad ni de malformaciones en los estudios revisados.", 0),
 ("El medicamento fue retirado por un defecto en el etiquetado del envase, sin riesgo para la salud.", 0),
]

print()
print("=== PARTE 2: muestra etiquetada (20 frases) ===")
vp = fp = fn = vn = 0
clave = None
for i, (frase, esperado) in enumerate(MUESTRA, 1):
    res = detect_risk_signals_in_text(frase, lang="es")
    clave, pred = prediccion(res)
    obtenido = 1 if pred else 0
    vp += esperado == 1 and obtenido == 1
    fn += esperado == 1 and obtenido == 0
    fp += esperado == 0 and obtenido == 1
    vn += esperado == 0 and obtenido == 0
    print(f"{i:02d} | esperado={esperado} obtenido={obtenido} | {'OK' if esperado == obtenido else 'ERROR'} | {frase[:70]}")
n = len(MUESTRA)
print(f"Clave usada para la prediccion: {clave}")
print(f"VP={vp} FP={fp} FN={fn} VN={vn}")
print(f"Exactitud={(vp+vn)/n*100:.1f}%  Precision={(vp/(vp+fp)*100 if vp+fp else 0):.1f}%  Sensibilidad={(vp/(vp+fn)*100 if vp+fn else 0):.1f}%")
print("Criterio fijado antes de la prueba: exactitud >= 80%")
