# -*- coding: utf-8 -*-
"""
Figuras del manuscrito (ingles), estilo minimalista de revista:
- sin titulos ni subtitulos dentro de la imagen (el caption del docx los lleva)
- letras de panel (a, b) en figuras multipanel
- paleta contenida: azul primario + grises; acento solo donde codifica algo
- PNG 300 dpi -> outputs/figures_en/
"""
import json
import os
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Patch
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.cm as cm

AZUL = "#1c5cab"          # primario
AZUL_OSC = "#0d366b"
GRIS = "#9a9a94"          # serie secundaria
GRIS_CLARO = "#d4d2cb"    # barras de fondo
CARBON = "#55534e"        # Lima en fig7
INK = "#1a1a19"
INK2 = "#6b6a64"
GRID = "#eceae5"
SEQ = ["#dce9f9", "#b7d3f6", "#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]
CMAP_SEQ = LinearSegmentedColormap.from_list("seq_blue", SEQ)
ORDEN_NIVEL = ["Distinguished", "I", "II", "III", "IV", "V", "VI", "VII"]

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 9, "axes.labelsize": 9, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5, "axes.edgecolor": "#c9c7c0", "axes.linewidth": 0.7,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "figure.dpi": 110, "savefig.dpi": 300, "savefig.bbox": "tight",
    "legend.frameon": False, "legend.fontsize": 8.5,
})

ren = pd.read_csv("data/renacyt_limpio.csv", encoding="utf-8-sig")
ia = pd.read_csv("outputs/investigadores_ia_limpio.csv", encoding="utf-8-sig")
oa_aut = pd.read_csv("data/openalex_autores_ia.csv", encoding="utf-8-sig")
oa_works = pd.read_csv("data/openalex_authorships_ia_pe.csv", encoding="utf-8-sig")
brecha = pd.read_csv("outputs/brecha_regional.csv", encoding="utf-8-sig", index_col=0)
ren["nivel"] = ren["nivel"].replace({"Distinguido": "Distinguished"})
ia["nivel"] = ia["nivel"].replace({"Distinguido": "Distinguished"})
ESP_EN = {
    "IA aplicada (otros dominios)": "Applied AI (sectoral domains)",
    "Visión computacional": "Computer vision",
    "IA en salud": "AI in health",
    "Aprendizaje automático (general)": "Machine learning (general)",
    "PLN (NLP)": "NLP",
    "Redes neuronales / Deep Learning": "Neural networks / deep learning",
    "Robótica y control": "Robotics and control",
    "IA en educación": "AI in education",
    "Optimización y metaheurísticas": "Optimization / metaheuristics",
    "Web semántica y ontologías": "Semantic web and ontologies",
}
ia["especialidad"] = ia["especialidad"].map(ESP_EN)
FIG = "outputs/figures_en/"
os.makedirs(FIG, exist_ok=True)

def f1(v):
    """Redondeo half-up a 1 decimal (6.85 -> 6.9), consistente con el texto."""
    return str(Decimal(str(float(v))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

def panel(ax, letra, x=-0.06, y=1.03):
    ax.text(x, y, letra, transform=ax.transAxes, fontsize=12, fontweight="bold",
            color=INK, va="bottom")

# fig 1 — mapa ---------------------------------------------------------------
with open("data/peru_departamentos.geojson", encoding="utf-8") as f:
    geo = json.load(f)
ia_pe = ia[~ia["region"].isin(["RESIDE EN EXTRANJERO", "NO REGISTRA"])]
n_ia = ia_pe.groupby("region").size()
vals_abs = {d: int(n_ia.get(d, 0)) for d in
            [ft["properties"]["NOMBDEP"] for ft in geo["features"]]}
if "CALLAO" in vals_abs:
    vals_abs["LIMA"] = vals_abs.get("LIMA", 0) + int(n_ia.get("CALLAO", 0))
vals_100k = {d: float(brecha["ia_por_100k"].get(d, np.nan)) for d in vals_abs}

def mapa(ax, vals, fmt=lambda v: f"{v:.0f}", cbar_label=""):
    v = np.array([vals[d] for d in vals if not np.isnan(vals[d])])
    norm = Normalize(vmin=0, vmax=v.max())
    patches, colors, centros = [], [], {}
    for ft in geo["features"]:
        dep = ft["properties"]["NOMBDEP"]
        geom = ft["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        allx, ally = [], []
        for poly in polys:
            ring = np.array(poly[0])
            patches.append(MplPolygon(ring, closed=True))
            val = vals.get(dep, np.nan)
            colors.append(CMAP_SEQ(norm(val)) if not np.isnan(val) else "#f0efeb")
            allx += ring[:, 0].tolist(); ally += ring[:, 1].tolist()
        centros[dep] = (np.mean(allx), np.mean(ally))
    pc = PatchCollection(patches, edgecolor="white", linewidth=0.6)
    pc.set_facecolor(colors)
    ax.add_collection(pc)
    ax.autoscale(); ax.set_aspect("equal"); ax.axis("off")
    DESP = {"LIMA": (-0.4, 0), "MOQUEGUA": (-1.9, -0.5), "TACNA": (1.3, -0.6)}
    top = sorted(((d, x) for d, x in vals.items() if not np.isnan(x)),
                 key=lambda t: -t[1])[:6]
    for d, x in top:
        cx, cy = centros[d]
        dx, dy = DESP.get(d, (0, 0))
        ax.annotate(f"{d.title()}\n{fmt(x)}", (cx + dx, cy + dy), ha="center",
                    fontsize=7, color=INK,
                    bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none", alpha=0.72))
    sm = cm.ScalarMappable(norm=norm, cmap=CMAP_SEQ)
    cb = plt.colorbar(sm, ax=ax, shrink=0.5, pad=0.01)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7.5, color=INK2)
    if cbar_label:
        cb.set_label(cbar_label, fontsize=7.5, color=INK2)

fig, axes = plt.subplots(1, 2, figsize=(10.6, 6.4))
mapa(axes[0], vals_abs, cbar_label="researchers (N)")
mapa(axes[1], vals_100k, fmt=f1, cbar_label="per 100,000 inhabitants")
panel(axes[0], "a", x=0.02); panel(axes[1], "b", x=0.02)
fig.subplots_adjust(wspace=0.02)
fig.savefig(FIG + "fig1_geographic_distribution.png"); plt.close(fig)
print("fig1 ok")

# fig 2 — niveles ------------------------------------------------------------
pct_all = ren["nivel"].value_counts(normalize=True).reindex(ORDEN_NIVEL).fillna(0) * 100
pct_ia = ia["nivel"].value_counts(normalize=True).reindex(ORDEN_NIVEL).fillna(0) * 100
x = np.arange(len(ORDEN_NIVEL)); w = 0.36
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.bar(x - w/2, pct_all, w, color=GRIS, label=f"Full registry (N = {len(ren):,})")
ax.bar(x + w/2, pct_ia, w, color=AZUL, label=f"AI subset (N = {len(ia)})")
for xi, v in zip(x - w/2, pct_all):
    ax.annotate(f"{v:.0f}", (xi, v), ha="center", va="bottom", fontsize=7, color=INK2)
for xi, v in zip(x + w/2, pct_ia):
    ax.annotate(f"{v:.0f}", (xi, v), ha="center", va="bottom", fontsize=7, color=INK2)
ax.set_xticks(x, ORDEN_NIVEL)
ax.set_ylabel("% of researchers")
ax.legend(loc="upper left")
ax.grid(axis="x", visible=False)
fig.savefig(FIG + "fig2_level_distribution.png"); plt.close(fig)
print("fig2 ok")

# fig 3 — temporal -----------------------------------------------------------
wy = oa_works.drop_duplicates("work_id").groupby("anio").size()
anios = list(range(2015, 2027))
serie = [int(wy.get(a, 0)) for a in anios]
first_all = oa_aut.groupby("primer_anio_ia").size()
first_ren = ia.groupby("primer_anio_ia").size()
s_all = [int(first_all.get(a, 0)) for a in anios]
s_ren = [int(first_ren.get(a, 0)) for a in anios]

fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.7))
ax = axes[0]
ax.plot(anios[:11], serie[:11], color=AZUL, lw=1.8, marker="o", ms=3.5)
ax.plot(anios[10:], serie[10:], color=AZUL, lw=1.4, marker="o", ms=3.5,
        ls=(0, (3, 3)), alpha=0.65)
ax.annotate("340", (2025, serie[10]), textcoords="offset points", xytext=(0, 7),
            ha="center", fontsize=8, color=INK)
ax.annotate("2026 partial", (2026, serie[11]), textcoords="offset points",
            xytext=(-4, -13), ha="center", fontsize=7.5, color=INK2)
ax.set_xticks(anios[::2]); ax.set_ylabel("AI works per year")
ax.grid(axis="x", visible=False)
panel(ax, "a")
ax = axes[1]
ax.plot(anios, s_all, color=GRIS, lw=1.8, marker="o", ms=3.5)
ax.plot(anios, s_ren, color=AZUL, lw=1.8, marker="o", ms=3.5)
ax.annotate("All authors", (anios[-1], s_all[-1]), textcoords="offset points",
            xytext=(6, 0), va="center", fontsize=8, color=GRIS)
ax.annotate("RENACYT-\ncertified", (anios[-1], s_ren[-1]), textcoords="offset points",
            xytext=(6, 0), va="center", fontsize=8, color=AZUL)
ax.set_xticks(anios[::2]); ax.set_ylabel("New AI authors per year")
ax.set_xlim(2014.5, 2028.4)
ax.grid(axis="x", visible=False)
panel(ax, "b")
fig.subplots_adjust(wspace=0.22)
fig.savefig(FIG + "fig3_temporal_growth.png"); plt.close(fig)
print("fig3 ok")

# fig 4 — instituciones ------------------------------------------------------
inst = json.load(open("outputs/analisis_institucional.json", encoding="utf-8"))
top10 = pd.DataFrame(inst["top15_instituciones"]).head(10).iloc[::-1]
cols = [AZUL if s == "Pública" else GRIS for s in top10["sector"]]
fig, ax = plt.subplots(figsize=(7.4, 3.9))
bars = ax.barh(top10["institucion"], top10["n_investigadores"], color=cols, height=0.58)
for r, v in zip(bars, top10["n_investigadores"]):
    ax.annotate(f" {v}", (r.get_width(), r.get_y() + r.get_height()/2),
                va="center", fontsize=8, color=INK2)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Certified researchers with AI output")
ax.legend(handles=[Patch(fc=AZUL, label="Public"), Patch(fc=GRIS, label="Private")],
          loc="lower right")
fig.savefig(FIG + "fig4_top_institutions.png"); plt.close(fig)
print("fig4 ok")

# fig 5 — especialidades -----------------------------------------------------
esp = ia["especialidad"].value_counts().iloc[::-1]
fig, ax = plt.subplots(figsize=(7.2, 3.7))
bars = ax.barh(esp.index, esp.values, color=AZUL, height=0.58)
for r, v in zip(bars, esp.values):
    ax.annotate(f" {v} ({100*v/len(ia):.0f}%)", (r.get_width(), r.get_y() + r.get_height()/2),
                va="center", fontsize=8, color=INK2)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Researchers")
fig.savefig(FIG + "fig5_specialties.png"); plt.close(fig)
print("fig5 ok")

# fig 6 — productividad vs nivel ---------------------------------------------
ia_niv = ia.dropna(subset=["nivel"]).copy()
rng = np.random.default_rng(42)
present = [n for n in ORDEN_NIVEL if n in set(ia_niv["nivel"])]
pos = {n: i for i, n in enumerate(present)}
xj = ia_niv["nivel"].map(pos) + rng.uniform(-0.15, 0.15, len(ia_niv))
fig, ax = plt.subplots(figsize=(7.2, 3.9))
ax.scatter(xj, ia_niv["n_obras_ia"], s=9, color=GRIS_CLARO, edgecolors="none")
medias = ia_niv.groupby("nivel")["n_obras_ia"].mean().reindex(present)
ax.plot(range(len(present)), medias.values, color=AZUL, lw=1.8, marker="o", ms=5)
for i, v in enumerate(medias.values):
    ax.annotate(f"{v:.1f}", (i, v), textcoords="offset points", xytext=(8, 3),
                fontsize=7.5, color=AZUL)
ax.annotate("level mean", (len(present) - 1, medias.values[-1]),
            textcoords="offset points", xytext=(8, -10), fontsize=8, color=AZUL)
ax.text(0.99, 0.96, "Spearman ρ = 0.09, p = 0.010", transform=ax.transAxes,
        ha="right", fontsize=8.5, color=INK2)
ax.set_xticks(range(len(present)), present)
ax.set_xlabel("RENACYT level (I = highest)")
ax.set_ylabel("AI works per researcher")
ax.grid(axis="x", visible=False)
fig.savefig(FIG + "fig6_productivity_level.png"); plt.close(fig)
print("fig6 ok")

# fig 7 — densidad regional --------------------------------------------------
b = brecha.dropna(subset=["ia_por_100k"]).sort_values("ia_por_100k")
SUR = {"PUNO", "CUSCO", "APURIMAC", "AYACUCHO", "HUANCAVELICA"}
def col_reg(r):
    if r in {"LIMA", "CALLAO"}: return CARBON
    if r in SUR: return AZUL
    return GRIS_CLARO
cols = [col_reg(r) for r in b.index]
fig, ax = plt.subplots(figsize=(6.8, 5.6))
bars = ax.barh([r.title() for r in b.index], b["ia_por_100k"], color=cols, height=0.6)
for r, v in zip(bars, b["ia_por_100k"]):
    ax.annotate(f" {f1(v)}", (r.get_width(), r.get_y() + r.get_height()/2),
                va="center", fontsize=7.5, color=INK2)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Certified AI researchers per 100,000 inhabitants")
ax.legend(handles=[Patch(fc=AZUL, label="Southern Andes"),
                   Patch(fc=CARBON, label="Lima and Callao"),
                   Patch(fc=GRIS_CLARO, label="Other regions")], loc="lower right")
fig.savefig(FIG + "fig7_regional_density.png"); plt.close(fig)
print("fig7 ok")

# fig 8 — genero -------------------------------------------------------------
gm_all = (pd.crosstab(ren["nivel"], ren["sexo"], normalize="index")["Femenino"]
          .reindex(ORDEN_NIVEL) * 100)
gm_ia = (pd.crosstab(ia["nivel"], ia["sexo"], normalize="index")["Femenino"]
         .reindex(ORDEN_NIVEL) * 100)
x = np.arange(len(ORDEN_NIVEL)); w = 0.36
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.bar(x - w/2, gm_all.values, w, color=GRIS, label="Full registry")
ax.bar(x + w/2, gm_ia.values, w, color=AZUL, label="AI subset")
ax.axhline(50, color=INK2, lw=0.8, ls=(0, (3, 3)))
ax.text(len(ORDEN_NIVEL) - 0.55, 51, "parity", fontsize=7.5, color=INK2, ha="right")
for xi, v in zip(x - w/2, gm_all.values):
    if not np.isnan(v):
        ax.annotate(f"{v:.0f}", (xi, v), ha="center", va="bottom", fontsize=7, color=INK2)
for xi, v in zip(x + w/2, gm_ia.values):
    if not np.isnan(v):
        ax.annotate(f"{v:.0f}", (xi, v), ha="center", va="bottom", fontsize=7, color=INK2)
ax.set_xticks(x, ORDEN_NIVEL)
ax.set_ylabel("% women")
ax.set_ylim(0, 58)
ax.legend(loc="upper right")
ax.grid(axis="x", visible=False)
fig.savefig(FIG + "fig8_gender_by_level.png"); plt.close(fig)
print("fig8 ok")
print("FIGURAS MINIMALISTAS EN LISTAS")
