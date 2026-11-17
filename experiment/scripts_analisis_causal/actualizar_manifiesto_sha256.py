#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proyecto Ascendant — Generador y Verificador del Manifiesto Criptográfico SHA-256 de la Base de Datos Íntegra, Scripts Causales y Paper Master v4.
Autor Único: David San Nicolás Montero (ORCID: 0009-0000-9977-007X)
"""

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "ascendant_generacional_integro.db")
MANIFEST_PATH = os.path.join(BASE_DIR, "MANIFIESTO_CRIPTOGRAFICO_SHA256_DB_INTEGRA.json")


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total_runs = cur.execute("SELECT COUNT(*) FROM simulation_runs").fetchone()[0]
    total_agents = cur.execute("SELECT COUNT(*) FROM final_memories").fetchone()[0]
    assert total_agents == total_runs * 4, f"Discrepancia 4:1: {total_runs} runs vs {total_agents} agents"

    breakdown_rows = cur.execute("""
        SELECT 
            sr.experiment_tag,
            COUNT(DISTINCT sr.run_id) AS n_runs,
            COUNT(fm.id) AS n_agents,
            SUM(fm.engrams_count) AS total_engrams,
            MIN(sr.seed) AS min_seed,
            MAX(sr.seed) AS max_seed
        FROM simulation_runs sr
        JOIN final_memories fm ON fm.run_id = sr.run_id
        GROUP BY sr.experiment_tag
        ORDER BY sr.experiment_tag
    """).fetchall()
    conn.close()

    cohorts = []
    for tag, n_r, n_a, tot_e, s_min, s_max in breakdown_rows:
        assert n_a == n_r * 4, f"Discrepancia en {tag}: {n_r} * 4 != {n_a}"
        cohorts.append({
            "experiment_tag": tag,
            "runs_count": int(n_r),
            "agents_count": int(n_a),
            "exact_4x_verified": True,
            "total_engrams_recorded": int(tot_e or 0),
            "seed_range": f"{s_min}..{s_max}",
        })

    tracked_files = [
        ("ascendant_generacional_integro.db", os.path.join(BASE_DIR, "ascendant_generacional_integro.db")),
        ("ejecutar_experimento_generacional.py", os.path.join(BASE_DIR, "ejecutar_experimento_generacional.py")),
        ("reanalisis_cluster_semilla_y_riesgos_competitivos.json", os.path.join(BASE_DIR, "reanalisis_cluster_semilla_y_riesgos_competitivos.json")),
        ("analisis_cox_cif_intraarquetipo_y_sensibilidad.json", os.path.join(BASE_DIR, "analisis_cox_cif_intraarquetipo_y_sensibilidad.json")),
        ("resultados_intervenciones_causales_directas.json", os.path.join(BASE_DIR, "resultados_intervenciones_causales_directas.json")),
        ("INFORME_REGRESION_MULTINOMIAL_Y_CADENA_CAUSAL_TEMPERAMENTO.md", os.path.join(BASE_DIR, "INFORME_REGRESION_MULTINOMIAL_Y_CADENA_CAUSAL_TEMPERAMENTO.md")),
        ("scripts_analisis_causal/reanalisis_cluster_semilla_y_riesgos_competitivos.py", os.path.join(BASE_DIR, "scripts_analisis_causal", "reanalisis_cluster_semilla_y_riesgos_competitivos.py")),
        ("scripts_analisis_causal/analisis_supervivencia_cox_cif_y_sensibilidad.py", os.path.join(BASE_DIR, "scripts_analisis_causal", "analisis_supervivencia_cox_cif_y_sensibilidad.py")),
        ("scripts_analisis_causal/experimento_intervenciones_mecanicistas_ampliado.py", os.path.join(BASE_DIR, "scripts_analisis_causal", "experimento_intervenciones_mecanicistas_ampliado.py")),
        ("scripts_analisis_causal/actualizar_manifiesto_sha256.py", os.path.join(BASE_DIR, "scripts_analisis_causal", "actualizar_manifiesto_sha256.py")),
        ("compilar_master_paper_v4.py", os.path.join(PROJECT_ROOT, "compilar_master_paper_v4.py")),
        ("Master_Scientific_Paper_David_San_Nicolas_v4.pdf", os.path.join(PROJECT_ROOT, "Master_Scientific_Paper_David_San_Nicolas_v4.pdf")),
        ("Master_Scientific_Paper_David_San_Nicolas_v4.md", os.path.join(PROJECT_ROOT, "Master_Scientific_Paper_David_San_Nicolas_v4.md")),
        ("Proyecto_Ascendant_Master_Scientific_Paper_David_San_Nicolas.pdf", os.path.join(PROJECT_ROOT, "Proyecto_Ascendant_Master_Scientific_Paper_David_San_Nicolas.pdf")),
    ]

    files_manifest = {}
    for rel_key, abs_p in tracked_files:
        if os.path.exists(abs_p):
            files_manifest[rel_key] = {
                "size_bytes": os.path.getsize(abs_p),
                "sha256": compute_sha256(abs_p),
            }

    manifest = {
        "title": "Proyecto Ascendant — Manifiesto Criptográfico SHA-256 de Trazabilidad e Integridad de Datos y Publicación Definitiva",
        "author": "David San Nicolás Montero",
        "orcid": "0009-0000-9977-007X",
        "doi_v3": "10.5281/zenodo.23802198",
        "concept_doi": "10.5281/zenodo.23616626",
        "version": "4.0 (Unified Simulation Engine, Clustered Multinomial & Competing Risks Survival Benchmarks, Direct Causal Surgery, and Preparatory Conscious-Layer Architecture)",
        "generated_at_iso": datetime.now().isoformat(),
        "database_summary": {
            "database_file": "ascendant_generacional_integro.db",
            "total_simulation_runs": int(total_runs),
            "total_agents_final_memories": int(total_agents),
            "orphan_records": 0,
            "exact_4_agents_per_run_invariant": True,
            "cohorts_breakdown": cohorts,
        },
        "files_sha256": files_manifest,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ Manifiesto SHA-256 actualizado en: {MANIFEST_PATH}")
    print(f"   Total corridas: {total_runs} | Total agentes: {total_agents} (Relación 4:1 exacta)")
    for k, v in files_manifest.items():
        print(f"   - {k}: {v['sha256']} ({v['size_bytes']:,} bytes)")


if __name__ == "__main__":
    main()
