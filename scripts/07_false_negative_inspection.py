# -*- coding: utf-8 -*-
"""
Inspección de falsos negativos del cruce: muestra aleatoria (semilla fija) de
100 autores OpenAlex sin par en RENACYT; para cada uno se busca el mejor
candidato difuso en el registro (Jaccard de tokens + similitud de secuencia).
Los pares con similitud alta se listan para veredicto manual.
Salida: outputs/inspeccion_no_match.csv
"""
import difflib
import pandas as pd
import unicodedata

SEED = 42
N = 100
PARTICULAS = {"DE", "LA", "DEL", "LOS", "LAS", "Y", "DA", "DI", "VAN", "VON"}

def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s))
                if unicodedata.category(c) != "Mn")
    return s.upper().replace("-", " ").replace(".", " ").replace(",", " ")

def toks(s):
    return [t for t in norm(s).split() if len(t) > 1 and t not in PARTICULAS]

ren = pd.read_csv("data/renacyt_limpio.csv", encoding="utf-8-sig")
nm = pd.read_csv("data/match_no_encontrados.csv", encoding="utf-8-sig")
nm = nm[nm["motivo"].isin(["sin_candidato", "ambiguo"])]
muestra = nm.sample(n=N, random_state=SEED)

ren_names = ren["INVESTIGADOR"].tolist()
ren_toksets = [set(toks(n)) for n in ren_names]
ren_join = [" ".join(sorted(toks(n))) for n in ren_names]

rows = []
for _, a in muestra.iterrows():
    at = set(toks(a["author_name"]))
    ajoin = " ".join(sorted(at))
    best_i, best_s = -1, 0.0
    for i, rt in enumerate(ren_toksets):
        if not (at & rt):
            continue
        j = len(at & rt) / len(at | rt) if (at | rt) else 0
        if j < 0.3:
            continue
        s = 0.5 * j + 0.5 * difflib.SequenceMatcher(None, ajoin, ren_join[i]).ratio()
        if s > best_s:
            best_s, best_i = s, i
    rows.append({
        "author_openalex": a["author_name"],
        "motivo": a["motivo"],
        "n_obras": a["n_obras_ia"],
        "mejor_candidato_renacyt": ren_names[best_i] if best_i >= 0 else "",
        "similitud": round(best_s, 3),
    })

df = pd.DataFrame(rows).sort_values("similitud", ascending=False)
df.to_csv("outputs/inspeccion_no_match.csv", index=False, encoding="utf-8-sig")
print("Muestra:", len(df))
print("\nPares con similitud >= 0.60 (revisar manualmente):\n")
print(df[df.similitud >= 0.60].to_string(index=False))
print("\nDistribución de similitud:")
print(pd.cut(df.similitud, [0, .4, .5, .6, .7, .8, 1.0]).value_counts().sort_index())
