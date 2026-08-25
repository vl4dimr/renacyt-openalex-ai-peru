# -*- coding: utf-8 -*-
"""
Cosecha de OpenAlex: obras en IA (subfield 1702) y Visión Computacional (1707)
con al menos un autor afiliado a una institución de Perú, 2015 en adelante.

Salidas:
  data/openalex_authorships_ia_pe.csv  (una fila por autoría peruana por obra)
  data/openalex_autores_ia.csv         (agregado por autor)
"""
import json
import time
import urllib.request
import urllib.parse
import pandas as pd

BASE = "https://api.openalex.org/works"
SUBFIELDS = {"subfields/1702": "Artificial Intelligence",
             "subfields/1707": "Computer Vision and Pattern Recognition"}
HEADERS = {"User-Agent": "renacyt-ai-peru-research-script"}


def fetch(url, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  retry {i+1} tras error: {e}")
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"Fallo persistente: {url}")


rows = []
seen_works = set()
for sf, sf_name in SUBFIELDS.items():
    cursor = "*"
    page = 0
    while cursor:
        params = {
            "filter": f"authorships.countries:countries/pe,primary_topic.subfield.id:{sf},from_publication_date:2015-01-01",
            "per-page": "200",
            "cursor": cursor,
            "select": "id,title,publication_year,type,primary_topic,authorships,cited_by_count",
        }
        url = BASE + "?" + urllib.parse.urlencode(params)
        data = fetch(url)
        page += 1
        for w in data.get("results", []):
            wid = w["id"]
            dup = wid in seen_works  # obra ya vista bajo el otro subfield
            if dup:
                continue
            seen_works.add(wid)
            pt = w.get("primary_topic") or {}
            topic = pt.get("display_name", "")
            subf = (pt.get("subfield") or {}).get("display_name", sf_name)
            for a in w.get("authorships", []):
                if "PE" not in (a.get("countries") or []):
                    continue
                auth = a.get("author") or {}
                insts_pe = [i for i in (a.get("institutions") or [])
                            if i.get("country_code") == "PE"]
                rows.append({
                    "work_id": wid,
                    "anio": w.get("publication_year"),
                    "tipo_obra": w.get("type"),
                    "citas": w.get("cited_by_count"),
                    "topic": topic,
                    "subfield": subf,
                    "author_id": auth.get("id", ""),
                    "author_name": auth.get("display_name", ""),
                    "orcid": auth.get("orcid") or "",
                    "instituciones_pe": "|".join(i.get("display_name", "") for i in insts_pe),
                    "tipo_institucion": "|".join(i.get("type", "") for i in insts_pe),
                })
        cursor = (data.get("meta") or {}).get("next_cursor")
        print(f"{sf_name}: pagina {page}, filas acumuladas {len(rows)}, obras {len(seen_works)}")
        time.sleep(0.15)

df = pd.DataFrame(rows)
df.to_csv("data/openalex_authorships_ia_pe.csv", index=False, encoding="utf-8-sig")
print("\nAuthorships peruanas:", len(df), "| obras únicas:", df.work_id.nunique(),
      "| autores únicos:", df.author_id.nunique())

# Agregado por autor
def top_join(s, n=3):
    vc = s.value_counts()
    return "|".join(vc.head(n).index)

ag = df.groupby("author_id").agg(
    author_name=("author_name", "first"),
    orcid=("orcid", "first"),
    n_obras_ia=("work_id", "nunique"),
    citas_ia=("citas", "sum"),
    primer_anio_ia=("anio", "min"),
    ultimo_anio_ia=("anio", "max"),
    topic_principal=("topic", top_join),
    subfield_principal=("subfield", lambda s: s.value_counts().index[0]),
    institucion_principal=("instituciones_pe", lambda s: top_join(s[s != ""], 1)),
    tipo_institucion=("tipo_institucion", lambda s: top_join(s[s != ""], 1)),
).reset_index()
ag.to_csv("data/openalex_autores_ia.csv", index=False, encoding="utf-8-sig")
print("Autores agregados:", len(ag))
print(ag.n_obras_ia.describe())
