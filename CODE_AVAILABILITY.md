# Statement on Code Availability, Open Data, and Cryptographic Reproducibility

## Project Ascendant v4.0
**Principal Investigator & Sole Author:** David San Nicolás Montero (`Independent Researcher | Project Ascendant`)  
**ORCID:** [0009-0000-9977-007X](https://orcid.org/0009-0000-9977-007X)  
**Definitive Version DOI (v4.0):** [10.5281/zenodo.23990811](https://doi.org/10.5281/zenodo.23990811) ([https://zenodo.org/records/23990811](https://zenodo.org/records/23990811))  
**Permanent Concept DOI (All Versions):** [10.5281/zenodo.23616626](https://doi.org/10.5281/zenodo.23616626)  
**GitHub Repository:** [https://github.com/Davidsnm/ascendant-synthetic-consciousness](https://github.com/Davidsnm/ascendant-synthetic-consciousness)  
**License:** Creative Commons Attribution-NonCommercial 4.0 International ([CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/))

---

### 1. Full Open-Science Code and Data Availability (v4.0)

In **Project Ascendant v4.0**, the complete unified generational simulation engine, causal intervention scripts, statistical verification pipelines, and cryptographic SHA-256 manifest are publicly available in this repository and archived on Zenodo:

* **Unified Generational Simulation Engine:** [`experiment/ejecutar_experimento_generacional.py`](./experiment/ejecutar_experimento_generacional.py) (`178,836 bytes`, SHA-256: `aab43e441ebfffdea5e3ef4b36ffdeff7c7d90ccca433f7b756f590464761b89`). Implements the 7 coupled differential equations, the exact `-8 cycle/bite` somatic wear invariant, the 100/140/200-slot autobiographical memory tape, and the direct `do(...)` causal intervention switches (`CAUSAL_THETA_MODE`, `CAUSAL_FIXED_THETA_OXI`, `CAUSAL_FEED_OXI_GAIN`, `CAUSAL_NONFEED_OXI_CLAMP`, `CAUSAL_TRAUMA_IRA_GAIN`). Note: while hooks for local LLM inference (`LIVE_LOCAL_LLM_ENABLED`) are implemented as preparatory scaffolding for Phase III, **the LLM was strictly inactive (`False`) across all 9,655 simulation runs reported in v4.0**.
* **Complete Audited SQLite Database (`845.3 MB`):** `ascendant_generacional_integro.db` (SHA-256: `13249851f86648742f8b5ab943c7ac21bd6f96fdcabe5c72ad6e07ecf2780909`), containing **9,655 simulation runs** ($25\text{ BASE} + 8,640\text{ factorial} + 990\text{ causal interventions}$) and **38,620 agent biographies** (exact 4:1 ratio, 0 orphan records, and 539,201 episodic engrams in the causal cohort). Due to GitHub's 100 MB per-file limit, the full 845.3 MB SQLite binary is permanently hosted on Zenodo at [https://zenodo.org/records/23990811](https://zenodo.org/records/23990811).
* **Audited Statistical & Causal Outputs:**
  * [`experiment/reanalisis_cluster_semilla_y_riesgos_competitivos.json`](./experiment/reanalisis_cluster_semilla_y_riesgos_competitivos.json) — Clustered multinomial logistic regression models ($N = 25,920$ offspring, $G = 360$ seeds) and Average Marginal Effects (AME).
  * [`experiment/analisis_cox_cif_intraarquetipo_y_sensibilidad.json`](./experiment/analisis_cox_cif_intraarquetipo_y_sensibilidad.json) — Competing-risks Cox-Breslow cause-specific proportional hazards with Lin-Wei seed-clustered covariance, Aalen-Johansen CIFs, and the 5-threshold bite-wear sensitivity grid.
  * [`experiment/resultados_intervenciones_causales_directas.json`](./experiment/resultados_intervenciones_causales_directas.json) — Complete results of the 990 direct mechanistic intervention runs (`CAUSAL_0` through `CAUSAL_6C`).
  * [`experiment/auditoria_camino_a_results.json`](./experiment/auditoria_camino_a_results.json) — Additional revision diagnostics (Schoenfeld proportionality tests, tie statistics, all-cause premature mortality Cox model, 10,000-resample seed-cluster bootstrap 95% CI for the `ALIMENTAR` DiD pathway share, and 7D interaction audit).
  * [`experiment/MANIFIESTO_CRIPTOGRAFICO_SHA256_DB_INTEGRA.json`](./experiment/MANIFIESTO_CRIPTOGRAFICO_SHA256_DB_INTEGRA.json) — Complete SHA-256 cryptographic manifest verifying all 9,655 runs and tracked files.

---

### 2. Licensing Terms

All v4.0 materials in this repository (manuscript PDF, figures, documentation, data tables, and analysis scripts) are licensed under the **Creative Commons Attribution-NonCommercial 4.0 International Public License (CC BY-NC 4.0)** — see [`LICENSE`](./LICENSE). Earlier versions (v1–v3) remain available under the terms of their original release.
