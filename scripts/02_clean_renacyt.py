# -*- coding: utf-8 -*-
"""
Limpieza del registro RENACYT (corte 2024-05-30).
Salida: data/renacyt_limpio.csv

Nivel unificado (escala Reglamento 2021, donde I es el nivel más alto y VII el
de entrada; 'Distinguido' por encima de I). Equivalencia aplicada al Reglamento
2018 según la transición oficial: Carlos Monge Medrano I-IV -> I-IV;
María Rostworowski I-III -> V-VII.
"""
import pandas as pd
import unicodedata

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn")

df = pd.read_csv("data/renacyt_2024_05_raw.csv", sep=";", encoding="utf-8-sig", dtype=str)
df.columns = [c.strip() for c in df.columns]
for c in df.columns:
    df[c] = df[c].str.strip()

# --- Nivel unificado ---
def nivel_unificado(r):
    if r["REGLAMENTO"] == "Reglamento_2021":
        return r["NIVEL_REGLAMENTO_2021"]
    grupo, niv = r["GRUPO_REGLAMENTO_2018"], r["NIVEL_REGLAMENTO_2018"]
    if pd.isna(niv) or niv == "":
        return None
    if grupo == "Carlos Monge Medrano":
        return {"I": "I", "II": "II", "III": "III", "IV": "IV"}.get(niv)
    if grupo == "Maria Rostworowski":
        return {"I": "V", "II": "VI", "III": "VII"}.get(niv)
    return None

df["nivel"] = df.apply(nivel_unificado, axis=1)
df["nivel"] = df["nivel"].replace({"Investigador Distinguido": "Distinguido"})
ORDEN_NIVEL = ["Distinguido", "I", "II", "III", "IV", "V", "VI", "VII"]
df["nivel_orden"] = df["nivel"].map({n: i for i, n in enumerate(ORDEN_NIVEL)})

# --- Fecha de calificación vigente ---
f2021 = pd.to_datetime(df["EMISION_CONSTANCIA_REGLAMENTO_2021"], format="%Y%m%d", errors="coerce")
f2018 = pd.to_datetime(df["FECHA_INICIO_VIGENCIA_REGLAMENTO_2018"], format="%Y%m%d", errors="coerce")
df["fecha_calificacion"] = f2021.fillna(f2018)
df["anio_calificacion"] = df["fecha_calificacion"].dt.year

# --- Geografía ---
df["pais"] = df["PAIS_RESIDENCIA"].fillna("NO REGISTRA")
dep = df["DEPARTAMENTO"].fillna("")
dep = dep.replace({"PROV. CONST. DEL CALLAO": "CALLAO"})
dep = dep.where(dep != "", None)
df["region"] = dep
df.loc[df["region"].isna() & (df["pais"] != "PERÚ") & (df["pais"] != "NO REGISTRA"),
       "region"] = "RESIDE EN EXTRANJERO"
df["region"] = df["region"].fillna("NO REGISTRA")

LIMA_MET = {"LIMA", "CALLAO"}
SUR_ANDINO = {"PUNO", "CUSCO", "APURIMAC", "AYACUCHO", "HUANCAVELICA"}
def macrozona(r):
    if r in LIMA_MET: return "Lima y Callao"
    if r in SUR_ANDINO: return "Sur andino (Altiplano)"
    if r in {"RESIDE EN EXTRANJERO", "NO REGISTRA"}: return "Extranjero / no registra"
    return "Otras regiones"
df["macrozona"] = df["region"].map(macrozona)

# --- Otros campos ---
df["sexo"] = df["SEXO"]
df["rango_edad"] = df["RANGO_EDAD"]
df["condicion"] = df["CONDICION_ACTIVIDAD"].fillna("No registra")
df.loc[df["condicion"].str.contains("Nulidad", na=False), "condicion"] = "Excluido"

# --- Nombre normalizado para el cruce ---
df["nombre_norm"] = (df["INVESTIGADOR"].map(strip_accents).str.upper()
                     .str.replace(r"[^A-ZÑ, ]", " ", regex=True)
                     .str.replace(r"\s+", " ", regex=True).str.strip())

out = df[["CODIGO_RENACYT", "INVESTIGADOR", "nombre_norm", "sexo", "rango_edad",
          "REGLAMENTO", "condicion", "nivel", "nivel_orden", "fecha_calificacion",
          "anio_calificacion", "pais", "region", "macrozona", "PROVINCIA", "DISTRITO",
          "UBIGEO"]].copy()
out.to_csv("data/renacyt_limpio.csv", index=False, encoding="utf-8-sig")
print("Registros:", len(out))
print("\nNivel unificado:\n", out["nivel"].value_counts(dropna=False))
print("\nMacrozona:\n", out["macrozona"].value_counts())
print("\nAño calificación:\n", out["anio_calificacion"].value_counts().sort_index())
print("\nSin nivel:", out["nivel"].isna().sum())
