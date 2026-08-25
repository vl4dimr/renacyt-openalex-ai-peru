# -*- coding: utf-8 -*-
"""
Análisis completo: registro RENACYT total + subconjunto de investigadores con
producción en IA (cruce OpenAlex). Genera JSONs, tablas markdown y resúmenes.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats

ORDEN_NIVEL = ["Distinguido", "I", "II", "III", "IV", "V", "VI", "VII"]
NIVELES_ALTOS = {"Distinguido", "I", "II", "III", "IV"}

ren = pd.read_csv("data/renacyt_limpio.csv", encoding="utf-8-sig")
ia = pd.read_csv("data/investigadores_ia_limpio.csv", encoding="utf-8-sig")
oa_aut = pd.read_csv("data/openalex_autores_ia.csv", encoding="utf-8-sig")
oa_works = pd.read_csv("data/openalex_authorships_ia_pe.csv", encoding="utf-8-sig")

# ----------------------------------------------------------------------------
# Normalización de instituciones (OpenAlex mezcla nombres en inglés/español)
# ----------------------------------------------------------------------------
INST_MAP = {
    "National University of San Marcos": "Universidad Nacional Mayor de San Marcos",
    "National University of Engineering": "Universidad Nacional de Ingeniería",
    "Peruvian University of Applied Sciences": "Universidad Peruana de Ciencias Aplicadas",
    "Private University of the North": "Universidad Privada del Norte",
    "National University of Trujillo": "Universidad Nacional de Trujillo",
    "National University of Saint Anthony the Abbot in Cuzco":
        "Universidad Nacional de San Antonio Abad del Cusco",
    "National University of the Peruvian Amazon": "Universidad Nacional de la Amazonía Peruana",
    "Universidad Nacional de San Agustin de Arequipa": "Universidad Nacional de San Agustín de Arequipa",
    "Universidad Nacional del Altiplano": "Universidad Nacional del Altiplano (Puno)",
}
PRIVADAS = {"Pontificia Universidad Católica del Perú", "Universidad César Vallejo",
            "Universidad Católica San Pablo", "Universidad Peruana de Ciencias Aplicadas",
            "Universidad Tecnológica del Perú", "Universidad Privada del Norte",
            "Universidad de Ingeniería y Tecnología", "Universidad Peruana Cayetano Heredia",
            "Universidad Continental", "Universidad San Ignacio de Loyola",
            "Universidad ESAN", "Universidad de Lima", "Universidad del Pacífico",
            "Universidad Ricardo Palma", "Universidad de Piura", "Universidad Andina del Cusco",
            "Universidad Católica de Santa María", "Universidad Señor de Sipán",
            "Universidad Peruana Unión", "Universidad Privada Antenor Orrego"}

def normaliza_inst(x):
    if pd.isna(x) or x == "":
        return "Sin afiliación registrada"
    return INST_MAP.get(x, x)

def sector_inst(nombre):
    if nombre == "Sin afiliación registrada":
        return "Sin dato"
    if nombre in PRIVADAS:
        return "Privada"
    if "Nacional" in nombre or nombre.startswith("Instituto") or "IGP" in nombre:
        return "Pública"
    if "Universidad" in nombre:
        return "Privada"
    return "Otro / no clasificado"

ia["institucion"] = ia["institucion_principal"].map(normaliza_inst)
ia["sector"] = ia["institucion"].map(sector_inst)

# ----------------------------------------------------------------------------
# Clusters de especialidad a partir del tópico principal OpenAlex
# ----------------------------------------------------------------------------
def cluster_especialidad(topic):
    t = str(topic).split("|")[0].lower()
    def any_in(*ks): return any(k in t for k in ks)
    if any_in("cancer", "blood", "medical", "health", "clinical", "radiom", "eeg",
              "diabetic", "tumor", "disease"):
        return "IA en salud"
    if any_in("tutoring", "adaptive learning", "education"):
        return "IA en educación"
    if any_in("sentiment", "topic modeling", "natural language", "language process",
              "hate speech", "speech", "text mining", "question answer", "translation"):
        return "PLN (NLP)"
    if any_in("image", "imaging", "vision", "video", "face", "object detect",
              "augmented reality", "recognition", "remote sensing", "biometric"):
        return "Visión computacional"
    if any_in("robot", "path planning", "fuzzy", "control system", "autonomous", "uav",
              "drone"):
        return "Robótica y control"
    if any_in("metaheuristic", "optimization", "evolutionary", "swarm", "genetic algorithm"):
        return "Optimización y metaheurísticas"
    if any_in("neural network", "deep learning", "explainable", "xai", "transformer"):
        return "Redes neuronales / Deep Learning"
    if any_in("anomaly", "imbalanced", "classification", "machine learning", "data mining",
              "clustering", "predictive", "random forest", "feature selection"):
        return "Aprendizaje automático (general)"
    if any_in("semantic web", "ontolog", "knowledge graph"):
        return "Web semántica y ontologías"
    return "IA aplicada (otros dominios)"

ia["especialidad"] = ia["topic_principal"].map(cluster_especialidad)

# ----------------------------------------------------------------------------
# 1. Estadísticas descriptivas
# ----------------------------------------------------------------------------
def dist(s, order=None):
    vc = s.value_counts(dropna=False)
    if order:
        vc = vc.reindex([o for o in order if o in vc.index])
    total = int(vc.sum())
    return {str(k): {"n": int(v), "pct": round(100 * v / total, 1)} for k, v in vc.items()}

desc = {
    "fuentes": {
        "renacyt": "Registro Nacional RENACYT, corte 2024-05-30 (datosabiertos.gob.pe)",
        "produccion_ia": ("OpenAlex: obras con subfield 'Artificial Intelligence' (1702) o "
                          "'Computer Vision and Pattern Recognition' (1707), >=2015, con "
                          "autoría afiliada a institución peruana"),
        "cruce": "Emparejamiento por nombre normalizado (3 niveles de confianza)",
    },
    "renacyt_total": {
        "n": int(len(ren)),
        "activos": int((ren["condicion"] == "Activo").sum()),
        "por_nivel": dist(ren["nivel"].fillna("Sin nivel"), ORDEN_NIVEL + ["Sin nivel"]),
        "por_sexo": dist(ren["sexo"]),
        "por_macrozona": dist(ren["macrozona"]),
        "por_rango_edad": dist(ren["rango_edad"]),
        "top10_regiones": dist(ren.loc[~ren["region"].isin(
            ["RESIDE EN EXTRANJERO", "NO REGISTRA"]), "region"]),
    },
    "ia_subconjunto": {
        "n": int(len(ia)),
        "pct_del_registro": round(100 * len(ia) / len(ren), 1),
        "obras_ia_total": int(ia["n_obras_ia"].sum()),
        "citas_ia_total": int(ia["citas_ia"].sum()),
        "por_nivel": dist(ia["nivel"], ORDEN_NIVEL),
        "por_sexo": dist(ia["sexo"]),
        "por_macrozona": dist(ia["macrozona"]),
        "por_especialidad": dist(ia["especialidad"]),
        "autores_openalex_totales": int(len(oa_aut)),
        "autores_openalex_no_renacyt": int(len(oa_aut) - len(ia)),
    },
}
# recorte top-10 regiones
top_reg = {k: v for i, (k, v) in enumerate(desc["renacyt_total"]["top10_regiones"].items()) if i < 10}
desc["renacyt_total"]["top10_regiones"] = top_reg

with open("outputs/estadisticas_descriptivas.json", "w", encoding="utf-8") as f:
    json.dump(desc, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------
# 2. Análisis temporal
# ----------------------------------------------------------------------------
anios = list(range(2015, 2027))
oa_first = oa_aut.groupby("primer_anio_ia").size()          # todos los autores OpenAlex
ia_first = ia.groupby("primer_anio_ia").size()              # solo RENACYT emparejados
works_year = oa_works.drop_duplicates("work_id").groupby("anio").size()
calif_year = ren.groupby("anio_calificacion").size()
calif_year_ia = ia.groupby("anio_calificacion").size()

def serie(s, rng):
    return {int(a): int(s.get(a, 0)) for a in rng}

obras = serie(works_year, range(2015, 2027))
vals = [v for a, v in obras.items() if 2015 <= a <= 2024 and v > 0]
cagr_obras = (vals[-1] / vals[0]) ** (1 / (len(vals) - 1)) - 1 if len(vals) > 1 else None

temporal = {
    "nota_periodo": ("RENACYT existe desde 2019 (antes REGINA); las fechas de calificación "
                     "cubren 2019-2024 (corte mayo 2024). La producción científica en IA "
                     "sí cubre 2015-2026 (obras OpenAlex; 2024-2026 parcial en autorías "
                     "de nuevos registros)."),
    "obras_ia_pe_por_anio": obras,
    "cagr_obras_2015_2024_pct": round(100 * cagr_obras, 1) if cagr_obras else None,
    "nuevos_autores_ia_por_anio_openalex": serie(oa_first, anios),
    "nuevos_investigadores_renacyt_ia_por_primer_anio_publicacion": serie(ia_first, anios),
    "calificaciones_renacyt_por_anio_total": serie(calif_year, range(2019, 2025)),
    "calificaciones_renacyt_por_anio_subconjunto_ia": serie(calif_year_ia, range(2019, 2025)),
    "niveles_por_cohorte_calificacion_ia": {
        str(int(a)): dist(g["nivel"], ORDEN_NIVEL)
        for a, g in ia.dropna(subset=["anio_calificacion"]).groupby("anio_calificacion")},
}
with open("outputs/analisis_temporal.json", "w", encoding="utf-8") as f:
    json.dump(temporal, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------
# 3. Análisis institucional
# ----------------------------------------------------------------------------
g = ia[ia["institucion"] != "Sin afiliación registrada"].groupby("institucion")
inst = g.agg(n_investigadores=("CODIGO_RENACYT", "count"),
             obras_ia=("n_obras_ia", "sum"),
             citas_ia=("citas_ia", "sum"),
             pct_niveles_altos=("nivel", lambda s: round(100 * s.isin(NIVELES_ALTOS).mean(), 1)),
             obras_por_investigador=("n_obras_ia", lambda s: round(s.mean(), 2)),
             ).sort_values("n_investigadores", ascending=False)
inst["sector"] = [sector_inst(i) for i in inst.index]
top15 = inst.head(15).reset_index()

sector_dist = ia[ia["sector"].isin(["Pública", "Privada"])].groupby("sector").agg(
    n=("CODIGO_RENACYT", "count"), obras=("n_obras_ia", "sum"),
    pct_niveles_altos=("nivel", lambda s: round(100 * s.isin(NIVELES_ALTOS).mean(), 1)))

institucional = {
    "top15_instituciones": top15.to_dict(orient="records"),
    "publico_vs_privado": {i: {"n": int(r["n"]), "obras_ia": int(r["obras"]),
                               "pct_niveles_altos": float(r["pct_niveles_altos"])}
                           for i, r in sector_dist.iterrows()},
    "nota_unap": None,
}
una = inst[inst.index.str.contains("Altiplano", case=False)]
if len(una):
    r = una.iloc[0]
    institucional["nota_unap"] = {
        "institucion": una.index[0], "ranking_nacional": int(inst.index.get_loc(una.index[0]) + 1),
        "n_investigadores": int(r["n_investigadores"]), "obras_ia": int(r["obras_ia"]),
        "pct_niveles_altos": float(r["pct_niveles_altos"])}
with open("outputs/analisis_institucional.json", "w", encoding="utf-8") as f:
    json.dump(institucional, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------
# 4. Especialización por región + brecha regional
# ----------------------------------------------------------------------------
ia_pe = ia[~ia["region"].isin(["RESIDE EN EXTRANJERO", "NO REGISTRA"])].copy()
top_regiones_ia = ia_pe["region"].value_counts().head(8).index.tolist()
mat = pd.crosstab(ia_pe.loc[ia_pe["region"].isin(top_regiones_ia), "region"],
                  ia_pe.loc[ia_pe["region"].isin(top_regiones_ia), "especialidad"])
mat = mat.loc[mat.sum(axis=1).sort_values(ascending=False).index]
mat.to_csv("outputs/matriz_region_especialidad.csv", encoding="utf-8-sig")

# Poblacion oficial INEI 2024 (al 30 de junio), extraida por scripts/11_inei_poblacion.py
_pob = pd.read_csv("data/inei_poblacion_2024.csv", encoding="utf-8-sig")
POB_MILES = {r.region: r.poblacion_2024 / 1000 for r in _pob.itertuples()}
reg_all = ren[~ren["region"].isin(["RESIDE EN EXTRANJERO", "NO REGISTRA"])] \
    .groupby("region").size().rename("renacyt_total")
reg_ia = ia_pe.groupby("region").size().rename("ia")
brecha = pd.concat([reg_all, reg_ia], axis=1).fillna(0).astype(int)
brecha["poblacion_miles"] = brecha.index.map(POB_MILES)
brecha = brecha.dropna(subset=["poblacion_miles"])
brecha["renacyt_por_100k"] = (brecha["renacyt_total"] / (brecha["poblacion_miles"] / 100)).round(2)
brecha["ia_por_100k"] = (brecha["ia"] / (brecha["poblacion_miles"] / 100)).round(2)
brecha = brecha.sort_values("renacyt_por_100k", ascending=False)
brecha.to_csv("outputs/brecha_regional.csv", encoding="utf-8-sig")

# ----------------------------------------------------------------------------
# 5. Productividad
# ----------------------------------------------------------------------------
ia_niv = ia.dropna(subset=["nivel_orden"]).copy()
ia_niv["jerarquia"] = 7 - ia_niv["nivel_orden"]     # 7=Distinguido ... 0=VII
sp_r, sp_p = stats.spearmanr(ia_niv["jerarquia"], ia_niv["n_obras_ia"])
pe_r, pe_p = stats.pearsonr(ia_niv["jerarquia"], ia_niv["n_obras_ia"])
sp_c, sp_cp = stats.spearmanr(ia_niv["jerarquia"], ia_niv["citas_ia"])

prod_nivel = ia_niv.groupby("nivel").agg(
    n=("CODIGO_RENACYT", "count"), obras_media=("n_obras_ia", "mean"),
    obras_mediana=("n_obras_ia", "median"), citas_media=("citas_ia", "mean")) \
    .reindex([n for n in ORDEN_NIVEL if n in ia_niv["nivel"].unique()]).round(2)

prod_zona = ia_pe.groupby("macrozona").agg(
    n=("CODIGO_RENACYT", "count"), obras_media=("n_obras_ia", "mean"),
    obras_total=("n_obras_ia", "sum"), citas_media=("citas_ia", "mean")).round(2)

prod_esp = ia.groupby("especialidad").agg(
    n=("CODIGO_RENACYT", "count"), obras_media=("n_obras_ia", "mean"),
    citas_media=("citas_ia", "mean")).sort_values("n", ascending=False).round(2)

# Mann-Whitney: obras Lima vs resto
lima = ia_pe.loc[ia_pe["macrozona"] == "Lima y Callao", "n_obras_ia"]
resto = ia_pe.loc[ia_pe["macrozona"] != "Lima y Callao", "n_obras_ia"]
mw_u, mw_p = stats.mannwhitneyu(lima, resto, alternative="two-sided")

productividad = {
    "correlacion_jerarquia_obras": {"spearman_rho": round(float(sp_r), 3),
                                    "p": float(f"{sp_p:.2e}"),
                                    "pearson_r": round(float(pe_r), 3),
                                    "p_pearson": float(f"{pe_p:.2e}")},
    "correlacion_jerarquia_citas": {"spearman_rho": round(float(sp_c), 3),
                                    "p": float(f"{sp_cp:.2e}")},
    "por_nivel": prod_nivel.reset_index().to_dict(orient="records"),
    "por_macrozona": prod_zona.reset_index().to_dict(orient="records"),
    "por_especialidad": prod_esp.reset_index().to_dict(orient="records"),
    "lima_vs_resto_mannwhitney": {"U": float(mw_u), "p": round(float(mw_p), 4),
                                  "mediana_lima": float(lima.median()),
                                  "mediana_resto": float(resto.median())},
}
with open("outputs/analisis_productividad.json", "w", encoding="utf-8") as f:
    json.dump(productividad, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------
# 6. Género
# ----------------------------------------------------------------------------
gen_all = pd.crosstab(ren["nivel"], ren["sexo"], normalize="index").mul(100).round(1) \
    .reindex(ORDEN_NIVEL)
gen_ia = pd.crosstab(ia["nivel"], ia["sexo"], normalize="index").mul(100).round(1) \
    .reindex(ORDEN_NIVEL)
genero = {
    "renacyt_total_pct_mujeres": round(100 * (ren["sexo"] == "Femenino").mean(), 1),
    "ia_pct_mujeres": round(100 * (ia["sexo"] == "Femenino").mean(), 1),
    "pct_mujeres_por_nivel_total": gen_all["Femenino"].dropna().to_dict(),
    "pct_mujeres_por_nivel_ia": gen_ia["Femenino"].dropna().to_dict(),
    "obras_media_por_sexo_ia": ia.groupby("sexo")["n_obras_ia"].mean().round(2).to_dict(),
}
with open("outputs/analisis_genero.json", "w", encoding="utf-8") as f:
    json.dump(genero, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------
# Dataset final + guardados auxiliares para figuras
# ----------------------------------------------------------------------------
ia.to_csv("outputs/investigadores_ia_limpio.csv", index=False, encoding="utf-8-sig")

print("=== RESUMEN ===")
print("RENACYT total:", len(ren), "| Subconjunto IA:", len(ia))
print("Spearman jerarquia-obras: rho=%.3f p=%.1e" % (sp_r, sp_p))
print("Mujeres RENACYT: %.1f%% | Mujeres IA: %.1f%%" %
      (genero["renacyt_total_pct_mujeres"], genero["ia_pct_mujeres"]))
print("\nEspecialidades:\n", ia["especialidad"].value_counts())
print("\nTop instituciones:\n", top15[["institucion", "n_investigadores", "sector",
                                       "pct_niveles_altos"]].head(10).to_string(index=False))
print("\nBrecha (por 100k hab):\n", brecha[["renacyt_total", "ia", "ia_por_100k",
                                            "renacyt_por_100k"]].head(12).to_string())
print("\nMatriz region x especialidad:\n", mat.to_string())
print("\nLima vs resto (obras): U=%.0f p=%.4f" % (mw_u, mw_p))
