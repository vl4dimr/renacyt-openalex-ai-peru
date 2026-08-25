# -*- coding: utf-8 -*-
"""Extrae la población oficial INEI 2024 por departamento.
Fuente: INEI, 'Población estimada al 30 de junio, por años calendario y sexo,
según departamento, 2000-2026' (proy_03_4.xlsx).
Salida: data/inei_poblacion_2024.csv  [region, poblacion_2024]"""
import pandas as pd
import unicodedata

def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s))
                if unicodedata.category(c) != "Mn")
    return s.upper().strip()

df = pd.read_excel("data/inei_poblacion_dep_2000_2026.xlsx",
                   sheet_name="2024-2026", header=None)
# fila 2: años en cols 2,5,8; fila 3: Total/Hombre/Mujer; datos desde fila 5
anio_cols = {int(df.iloc[2, c]): c for c in (2, 5, 8) if pd.notna(df.iloc[2, c])}
col2024 = anio_cols[2024]
rows = []
for i in range(5, len(df)):
    dep, tot = df.iloc[i, 1], df.iloc[i, col2024]
    if pd.isna(dep) or pd.isna(tot):
        continue
    name = norm(dep)
    if name in ("PERU",):
        print("Control nacional 2024:", int(tot))
        continue
    if "CALLAO" in name:
        name = "CALLAO"
    rows.append({"region": name, "poblacion_2024": int(tot)})

out = pd.DataFrame(rows)
out.to_csv("data/inei_poblacion_2024.csv", index=False, encoding="utf-8-sig")
print(out.to_string(index=False))
print("Departamentos:", len(out))
