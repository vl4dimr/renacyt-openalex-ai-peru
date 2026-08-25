# -*- coding: utf-8 -*-
"""Full replication pipeline. Run from the package root:
    pip install -r requirements.txt
    python main.py                 # re-harvests OpenAlex (~2 min)
    python main.py --no-harvest    # uses the stored harvest in data/
"""
import subprocess
import sys

STAGES = [
    ("scripts/01_harvest_openalex.py", "OpenAlex harvest (AI + CV subfields, Peru)"),
    ("scripts/02_clean_renacyt.py", "RENACYT registry cleaning"),
    ("scripts/03_extract_inei_population.py", "INEI 2024 population extraction"),
    ("scripts/04_link_authors_to_registry.py", "Three-tier name linkage"),
    ("scripts/05_analysis.py", "Statistical analysis"),
    ("scripts/06_figures.py", "Manuscript figures (PNG 300 dpi)"),
    ("scripts/07_false_negative_inspection.py", "False-negative inspection (seed 42)"),
]

def main():
    skip = "--no-harvest" in sys.argv
    for script, desc in STAGES:
        if skip and "harvest" in script:
            print(f"[SKIP] {desc}")
            continue
        if "inei" in script or "population" in script:
            # requiere data/inei_poblacion_dep_2000_2026.xlsx (INEI); si no esta,
            # se usa el data/inei_poblacion_2024.csv ya incluido
            import os
            if not os.path.exists("data/inei_poblacion_dep_2000_2026.xlsx"):
                print(f"[SKIP] {desc} (using bundled data/inei_poblacion_2024.csv)")
                continue
        print(f"\n=== {desc} ===")
        r = subprocess.run([sys.executable, script])
        if r.returncode != 0:
            sys.exit(f"Stage failed: {script}")
    print("\nDone. See outputs/")

if __name__ == "__main__":
    main()
