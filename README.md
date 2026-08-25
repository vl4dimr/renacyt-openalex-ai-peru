# Replication package — The invisible majority

[![DOI](https://zenodo.org/badge/1343786861.svg)](https://doi.org/10.5281/zenodo.22070643)

Data and code for: *The invisible majority: linking a national researcher
registry to OpenAlex reveals Peru's uncertified artificial intelligence
workforce* (manuscript under review).

## Reproduce

```
pip install -r requirements.txt
python main.py --no-harvest   # from the stored harvest (recommended)
python main.py                # re-harvests OpenAlex (results may drift as
                              # OpenAlex updates)
```

## Contents

| Path | Description |
|---|---|
| `data/renacyt_2024_05_raw.csv` | Complete public RENACYT registry, cut-off 2024-05-30 (CONCYTEC, Plataforma Nacional de Datos Abiertos, ODC-By) |
| `data/renacyt_limpio.csv` | Cleaned registry, levels harmonized to the 2021 scale |
| `data/openalex_*.csv` | OpenAlex harvest: subfields 1702 (AI) and 1707 (Computer Vision), 2015–2026, Peru-affiliated (harvested 2026-08; CC0) |
| `data/investigadores_ia_limpio.csv` | Linked dataset: 856 certified AI researchers (main analytical file) |
| `data/match_no_encontrados.csv` | Unmatched OpenAlex authors with reason codes |
| `data/inei_poblacion_2024.csv` | Official INEI population estimates, 30 June 2024, by department |
| `data/peru_departamentos.geojson` | Department polygons (choropleth) |
| `scripts/01…07` | Pipeline in execution order: harvest → clean → population → linkage → analysis → figures → false-negative inspection |
| `outputs/*.json`, `outputs/*.csv` | Statistics backing every figure and table in the manuscript |
| `outputs/figures/` | Manuscript figures, PNG 300 dpi |

## Licences

Code: MIT. Derived data and outputs: CC BY 4.0. RENACYT source: ODC-By
(CONCYTEC). OpenAlex records: CC0.

## Cite

[Authors] (2026). Replication package — The invisible majority. Zenodo.
https://doi.org/10.5281/zenodo.22070643
