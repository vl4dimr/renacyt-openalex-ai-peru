# -*- coding: utf-8 -*-
"""
Cruce por nombre entre autores de IA (OpenAlex, afiliación Perú) y el registro
RENACYT. Emparejamiento por conjuntos de tokens con tres niveles de confianza:
  exacta : igualdad del conjunto completo de tokens
  alta   : >=3 tokens del autor contenidos en el nombre RENACYT, con al menos
           un apellido y un nombre de pila coincidentes, candidato único
  media  : 2 tokens contenidos, candidato único en todo el registro

Salidas:
  data/investigadores_ia_limpio.csv   (autores IA emparejados con RENACYT)
  data/match_no_encontrados.csv       (autores IA sin par en RENACYT)
  outputs/match_reporte.json
"""
import json
import pandas as pd
import unicodedata
from collections import defaultdict

PARTICULAS = {"DE", "LA", "DEL", "LOS", "LAS", "Y", "DA", "DI", "VAN", "VON"}

def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s))
                if unicodedata.category(c) != "Mn")
    s = s.upper().replace("-", " ").replace(".", " ").replace("'", " ")
    return " ".join(t for t in s.split() if t)

def tokens(s, drop_particles=True):
    ts = norm(s).replace(",", " ").split()
    if drop_particles:
        ts = [t for t in ts if t not in PARTICULAS]
    return ts

ren = pd.read_csv("data/renacyt_limpio.csv", encoding="utf-8-sig")
oa = pd.read_csv("data/openalex_autores_ia.csv", encoding="utf-8-sig")

# --- Índices RENACYT ---
ren_tokens, ren_surnames, ren_given = {}, {}, {}
tok2rows = defaultdict(set)
for i, r in ren.iterrows():
    nombre = str(r["INVESTIGADOR"])
    if "," in nombre:
        ap, no = nombre.split(",", 1)
    else:
        ap, no = nombre, ""
    su, gi = tokens(ap), tokens(no)
    ren_surnames[i], ren_given[i] = set(su), set(gi)
    ren_tokens[i] = set(su) | set(gi)
    for t in ren_tokens[i]:
        tok2rows[t].add(i)

# --- Matching ---
matches, no_match = [], []
for _, a in oa.iterrows():
    ts_all = tokens(a["author_name"])
    ts = [t for t in ts_all if len(t) > 1]          # descartar iniciales
    if len(ts) < 2:
        no_match.append({**a.to_dict(), "motivo": "nombre_insuficiente"})
        continue
    cand = None
    for t in ts:
        rows = tok2rows.get(t, set())
        cand = rows if cand is None else (cand & rows)
        if not cand:
            break
    cand = cand or set()
    tier, chosen = None, None
    tset = set(ts)
    exact = [c for c in cand if ren_tokens[c] == tset]
    if len(exact) == 1:
        tier, chosen = "exacta", exact[0]
    elif len(cand) == 1:
        c = next(iter(cand))
        has_su = bool(tset & ren_surnames[c])
        has_gi = bool(tset & ren_given[c])
        if len(ts) >= 3 and has_su and has_gi:
            tier, chosen = "alta", c
        elif len(ts) == 2 and has_su and has_gi:
            tier, chosen = "media", c
    if chosen is None:
        motivo = "ambiguo" if len(cand) > 1 else "sin_candidato"
        no_match.append({**a.to_dict(), "motivo": motivo})
        continue
    r = ren.loc[chosen]
    matches.append({
        "author_id": a["author_id"], "author_name": a["author_name"],
        "orcid": a["orcid"], "n_obras_ia": a["n_obras_ia"], "citas_ia": a["citas_ia"],
        "primer_anio_ia": a["primer_anio_ia"], "ultimo_anio_ia": a["ultimo_anio_ia"],
        "topic_principal": a["topic_principal"], "subfield_principal": a["subfield_principal"],
        "institucion_principal": a["institucion_principal"],
        "tipo_institucion": a["tipo_institucion"],
        "confianza_match": tier,
        "CODIGO_RENACYT": r["CODIGO_RENACYT"], "INVESTIGADOR": r["INVESTIGADOR"],
        "sexo": r["sexo"], "rango_edad": r["rango_edad"], "nivel": r["nivel"],
        "nivel_orden": r["nivel_orden"], "condicion": r["condicion"],
        "REGLAMENTO": r["REGLAMENTO"], "anio_calificacion": r["anio_calificacion"],
        "region": r["region"], "macrozona": r["macrozona"], "pais": r["pais"],
    })

m = pd.DataFrame(matches)
# Un investigador RENACYT puede aparecer con dos perfiles OpenAlex: conservar el
# de mayor produccion y sumar obras/citas.
m = m.sort_values("n_obras_ia", ascending=False)
agg_first = {c: "first" for c in m.columns if c not in
             {"CODIGO_RENACYT", "n_obras_ia", "citas_ia", "primer_anio_ia", "ultimo_anio_ia"}}
m = m.groupby("CODIGO_RENACYT").agg({**agg_first, "n_obras_ia": "sum", "citas_ia": "sum",
                                     "primer_anio_ia": "min", "ultimo_anio_ia": "max"}).reset_index()

nm = pd.DataFrame(no_match)
m.to_csv("data/investigadores_ia_limpio.csv", index=False, encoding="utf-8-sig")
nm.to_csv("data/match_no_encontrados.csv", index=False, encoding="utf-8-sig")

rep = {
    "autores_openalex_ia": int(len(oa)),
    "emparejados": int(len(m)),
    "por_confianza": m["confianza_match"].value_counts().to_dict(),
    "no_emparejados": int(len(nm)),
    "motivos_no_match": nm["motivo"].value_counts().to_dict(),
    "tasa_match_pct": round(100 * len(m) / len(oa), 1),
    "nota": ("Autores OpenAlex sin par en RENACYT incluyen: estudiantes/tesistas no "
             "registrados, coautores extranjeros con afiliacion temporal peruana, "
             "y variantes de nombre no resueltas."),
}
with open("outputs/match_reporte.json", "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=2)
print(json.dumps(rep, ensure_ascii=False, indent=2))
print("\nNiveles de los emparejados:\n", m["nivel"].value_counts())
print("\nObras IA de emparejados:", m["n_obras_ia"].sum())
