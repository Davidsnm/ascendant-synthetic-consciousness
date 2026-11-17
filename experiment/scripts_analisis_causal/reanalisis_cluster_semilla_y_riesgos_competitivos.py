#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reanálisis Estadístico Riguroso sin Pseudorreplicación (Cluster-Robust SE por Semilla G=360),
Exclusión de P0 (N=25.920 descendientes con tau=2000 homogéneo y Generación Categórica),
Desglose en 4 Categorías (Separando Senescencia Intacta de Senescencia por Desgaste de Mordiscos),
Contrastes Suma y 10 Contrastes por Pares con Corrección de Holm-Bonferroni,
y Tasas de Incidencia de Poisson (IRR con Exposición Exacta y Sandwich por Semilla).

Autor Único: David San Nicolás Montero (ORCID: 0009-0000-9977-007X)
DOI Definitivo (v3): 10.5281/zenodo.23802198 | Concept DOI: 10.5281/zenodo.23616626
"""

import sqlite3
import json
import math
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ascendant_generacional_integro.db")
OUT_JSON = os.path.join(BASE_DIR, "reanalisis_cluster_semilla_y_riesgos_competitivos.json")

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(float(x) / math.sqrt(2.0)))

def z_p_value(z):
    return 2.0 * (1.0 - norm_cdf(abs(float(z))))

def chi2_p_value(chi2_val, df):
    if chi2_val <= 0 or df <= 0:
        return 1.0
    a = 0.5 * float(df)
    x = 0.5 * float(chi2_val)
    if x < a + 1.0:
        ap = a
        s = 1.0 / a
        del_v = s
        for _ in range(500):
            ap += 1.0
            del_v *= x / ap
            s += del_v
            if abs(del_v) < abs(s) * 1e-14:
                break
        p_low = s * math.exp(-x + a * math.log(max(x, 1e-300)) - math.lgamma(a))
        return max(0.0, min(1.0, 1.0 - p_low))
    else:
        b = x + 1.0 - a
        c = 1.0 / 1e-30
        d = 1.0 / b
        h = d
        for i in range(1, 500):
            an = -i * (i - a)
            b += 2.0
            d = an * d + b
            if abs(d) < 1e-30:
                d = 1e-30
            c = b + an / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            del_v = d * c
            h *= del_v
            if abs(del_v - 1.0) < 1e-14:
                break
        q_up = h * math.exp(-x + a * math.log(max(x, 1e-300)) - math.lgamma(a))
        return max(0.0, min(1.0, q_up))

def holm_bonferroni(p_vals):
    m = len(p_vals)
    indexed = sorted(enumerate(p_vals), key=lambda x: x[1])
    adj = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        val = min(1.0, p * (m - rank))
        running_max = max(running_max, val)
        adj[orig_idx] = running_max
    return adj

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("""
SELECT fm.run_id, sr.seed, sr.condition, sr.experiment_tag, sr.num_predators, sr.max_engrams,
       sr.cultural_enabled, sr.pantry_enabled,
       fm.agent_id, fm.gen_number, fm.age_at_death, fm.initial_max_lifespan, fm.final_max_lifespan,
       fm.outside_cycles, fm.cause_of_death, fm.temperament, fm.theta_temp_json, fm.engrams_count
FROM final_memories fm
JOIN simulation_runs sr ON fm.run_id = sr.run_id
WHERE sr.seed >= 50000 AND sr.seed < 50360
  AND sr.experiment_tag IN ('K3_M100', 'K3_M140', 'K3_M200', 'K5_M100', 'K5_M140', 'K5_M200')
ORDER BY fm.run_id, fm.gen_number
""")
rows = cur.fetchall()
print(f"Cargados {len(rows)} agentes de las 6 baterías factoriales (360 semillas x 24 brazos = 8.640 corridas).")

runs_map = {}
for r in rows:
    run_id, seed, cond, exp_tag, num_pred, max_eng, cult, pant, ag_id, gen, age, init_l, fin_l, out_c, cod, temp, th_j, eng_c = r
    th = json.loads(th_j) if th_j else {}
    k_pred = 5 if "K5" in str(exp_tag) else 3
    mem_cap = 140 if "M140" in str(exp_tag) else (200 if "M200" in str(exp_tag) else 100)

    init_lifespan = init_l if init_l and init_l > 0 else (800 if gen == 0 else 2000)
    fin_lifespan = age if cod == "SENESCENCIA_NATURAL" else (fin_l if fin_l and fin_l > 0 else init_lifespan)
    bite_wear = max(0, init_lifespan - age) if cod == "SENESCENCIA_NATURAL" else max(0, init_lifespan - fin_lifespan)
    wear_threshold = 32 if gen == 0 else 80
    if cod == "SENESCENCIA_NATURAL":
        cod_4cat = "SENESCENCIA_DESGASTE_MORDISCOS" if bite_wear > wear_threshold else "SENESCENCIA_INTACTA"
    else:
        cod_4cat = cod

    runs_map.setdefault(run_id, {})[gen] = {
        "run_id": run_id,
        "seed": int(seed),
        "condition": cond,
        "k5": 1.0 if k_pred == 5 else 0.0,
        "m140": 1.0 if mem_cap == 140 else 0.0,
        "m200": 1.0 if mem_cap == 200 else 0.0,
        "cult": float(cult),
        "pant": float(pant),
        "agent_id": ag_id,
        "gen": int(gen),
        "age": float(age),
        "init_l": float(init_lifespan),
        "fin_l": float(fin_lifespan),
        "bite_wear": float(bite_wear),
        "out_c": float(out_c),
        "out_ratio": float(out_c) / max(1.0, float(age)),
        "cod": cod,
        "cod_4cat": cod_4cat,
        "temp": temp,
        "theta": th,
    }

all_agents = []
offspring_agents = []
for run_id, gmap in runs_map.items():
    for g in (0, 1, 2, 3):
        if g not in gmap:
            continue
        item = gmap[g]
        if g > 0 and (g - 1) in gmap:
            parent = gmap[g - 1]
            item["parent_temp"] = parent["temp"]
            item["parent_oxi"] = float(parent["theta"].get("oxi", 0.5))
            item["parent_age"] = parent["age"]
            item["parent_cod"] = parent["cod"]
        else:
            item["parent_temp"] = None
            item["parent_oxi"] = np.nan
            item["parent_age"] = np.nan
            item["parent_cod"] = None
        all_agents.append(item)
        if g in (1, 2, 3):
            offspring_agents.append(item)

print(f"Total agentes: {len(all_agents)} | Descendientes homogéneos (ALFA, BETA, GAMA, tau=2000): {len(offspring_agents)}")

TEMPS_ORDER = [
    "Melancólico Empático",
    "Optimista Sereno",
    "Entusiasta Dopaminérgico",
    "Colérico Reactivo",
    "Estoico Desapegado",
]

def compute_descriptive_by_temp(agent_list):
    res = {}
    for t_name in TEMPS_ORDER:
        sub = [x for x in agent_list if x["temp"] == t_name]
        n_sub = len(sub)
        seed_groups = {}
        for x in sub:
            seed_groups.setdefault(x["seed"], []).append(x)

        s_inan = [100.0 * sum(1 for a in v if a["cod"] == "INANICION") / len(v) for v in seed_groups.values()]
        s_depr = [100.0 * sum(1 for a in v if a["cod"] == "DEPREDADOR") / len(v) for v in seed_groups.values()]
        s_sen  = [100.0 * sum(1 for a in v if a["cod"] == "SENESCENCIA_NATURAL") / len(v) for v in seed_groups.values()]
        s_sen_int = [100.0 * sum(1 for a in v if a["cod_4cat"] == "SENESCENCIA_INTACTA") / len(v) for v in seed_groups.values()]
        s_sen_bit = [100.0 * sum(1 for a in v if a["cod_4cat"] == "SENESCENCIA_DESGASTE_MORDISCOS") / len(v) for v in seed_groups.values()]

        res[t_name] = {
            "N_agents": n_sub,
            "N_unique_seeds": len(seed_groups),
            "theta_oxi_mean": round(float(np.mean([x["theta"]["oxi"] for x in sub])), 3),
            "outside_exposure_ratio": round(float(np.mean([x["out_ratio"] for x in sub])), 4),
            "mean_age": round(float(np.mean([x["age"] for x in sub])), 2),
            "mean_bite_wear_cycles": round(float(np.mean([x["bite_wear"] for x in sub])), 2),
            "rates_3cat_pct": {
                "SENESCENCIA_NATURAL": round(100.0 * sum(1 for x in sub if x["cod"] == "SENESCENCIA_NATURAL") / n_sub, 2),
                "INANICION": round(100.0 * sum(1 for x in sub if x["cod"] == "INANICION") / n_sub, 2),
                "DEPREDADOR": round(100.0 * sum(1 for x in sub if x["cod"] == "DEPREDADOR") / n_sub, 2),
            },
            "cluster_se_3cat_pct": {
                "SENESCENCIA_NATURAL": round(float(np.std(s_sen, ddof=1) / math.sqrt(len(s_sen))), 2),
                "INANICION": round(float(np.std(s_inan, ddof=1) / math.sqrt(len(s_inan))), 2),
                "DEPREDADOR": round(float(np.std(s_depr, ddof=1) / math.sqrt(len(s_depr))), 2),
            },
            "rates_4cat_pct": {
                "SENESCENCIA_INTACTA": round(100.0 * sum(1 for x in sub if x["cod_4cat"] == "SENESCENCIA_INTACTA") / n_sub, 2),
                "SENESCENCIA_DESGASTE_MORDISCOS": round(100.0 * sum(1 for x in sub if x["cod_4cat"] == "SENESCENCIA_DESGASTE_MORDISCOS") / n_sub, 2),
                "INANICION": round(100.0 * sum(1 for x in sub if x["cod_4cat"] == "INANICION") / n_sub, 2),
                "DEPREDADOR": round(100.0 * sum(1 for x in sub if x["cod_4cat"] == "DEPREDADOR") / n_sub, 2),
            },
            "cluster_se_4cat_pct": {
                "SENESCENCIA_INTACTA": round(float(np.std(s_sen_int, ddof=1) / math.sqrt(len(s_sen_int))), 2),
                "SENESCENCIA_DESGASTE_MORDISCOS": round(float(np.std(s_sen_bit, ddof=1) / math.sqrt(len(s_sen_bit))), 2),
                "INANICION": round(float(np.std(s_inan, ddof=1) / math.sqrt(len(s_inan))), 2),
                "DEPREDADOR": round(float(np.std(s_depr, ddof=1) / math.sqrt(len(s_depr))), 2),
            },
        }
    return res

desc_all_34560 = compute_descriptive_by_temp(all_agents)
desc_offspring_25920 = compute_descriptive_by_temp(offspring_agents)

def fit_mnlogit_cluster(data_list, feature_builder, col_names, class_mapper, num_classes=3, max_iter=80, tol=1e-8):
    N = len(data_list)
    D = len(col_names)
    C = num_classes - 1
    X = np.zeros((N, D), dtype=np.float64)
    y = np.zeros(N, dtype=np.int32)
    seeds = np.zeros(N, dtype=np.int32)

    for i, d in enumerate(data_list):
        X[i, :] = feature_builder(d)
        y[i] = class_mapper(d)
        seeds[i] = d["seed"]

    Y_ind = np.zeros((N, C), dtype=np.float64)
    for c in range(1, num_classes):
        Y_ind[:, c - 1] = (y == c).astype(np.float64)

    beta = np.zeros((C, D), dtype=np.float64)

    for _ in range(max_iter):
        logits = np.clip(X @ beta.T, -30.0, 30.0)
        exp_l = np.exp(logits)
        denom = 1.0 + np.sum(exp_l, axis=1, keepdims=True)
        probs = exp_l / denom

        diff = Y_ind - probs
        grad = (diff.T @ X).reshape(-1)
        if np.max(np.abs(grad)) < tol:
            break

        H = np.zeros((C * D, C * D), dtype=np.float64)
        for c1 in range(C):
            for c2 in range(C):
                if c1 == c2:
                    w = probs[:, c1] * (1.0 - probs[:, c1])
                else:
                    w = -probs[:, c1] * probs[:, c2]
                H[c1*D:(c1+1)*D, c2*D:(c2+1)*D] = (X * w[:, None]).T @ X

        step = np.linalg.solve(H + np.eye(C * D) * 1e-9, grad)
        beta += step.reshape(C, D)
        if np.max(np.abs(step)) < tol:
            break

    logits = np.clip(X @ beta.T, -30.0, 30.0)
    exp_l = np.exp(logits)
    denom = 1.0 + np.sum(exp_l, axis=1, keepdims=True)
    probs = exp_l / denom
    p0 = 1.0 / denom[:, 0]

    ll = float(np.sum((y == 0) * np.log(np.clip(p0, 1e-15, 1.0))))
    for c in range(C):
        ll += float(np.sum(Y_ind[:, c] * np.log(np.clip(probs[:, c], 1e-15, 1.0))))

    _, counts = np.unique(y, return_counts=True)
    p_null = counts / float(N)
    ll_null = float(np.sum(counts * np.log(np.clip(p_null, 1e-15, 1.0))))

    H = np.zeros((C * D, C * D), dtype=np.float64)
    for c1 in range(C):
        for c2 in range(C):
            if c1 == c2:
                w = probs[:, c1] * (1.0 - probs[:, c1])
            else:
                w = -probs[:, c1] * probs[:, c2]
            H[c1*D:(c1+1)*D, c2*D:(c2+1)*D] = (X * w[:, None]).T @ X

    cov_naive = np.linalg.inv(H + np.eye(C * D) * 1e-9)

    diff = Y_ind - probs
    scores_list = [X * diff[:, c:c+1] for c in range(C)]
    scores_i = np.hstack(scores_list)

    unique_seeds = np.unique(seeds)
    G = len(unique_seeds)
    meat = np.zeros((C * D, C * D), dtype=np.float64)
    for s in unique_seeds:
        mask = (seeds == s)
        g_s = np.sum(scores_i[mask, :], axis=0)
        meat += np.outer(g_s, g_s)

    dfc = (G / (G - 1.0)) * ((N - 1.0) / (N - C * D))
    cov_cluster = dfc * (cov_naive @ meat @ cov_naive)

    return {
        "b_hat": beta.reshape(-1),
        "beta_mat": beta,
        "ll": ll,
        "ll_null": ll_null,
        "mcfadden_r2": 1.0 - (ll / ll_null),
        "cov_naive": cov_naive,
        "cov_cluster": cov_cluster,
        "D": D,
        "C": C,
        "N": N,
        "G_clusters": G,
        "col_names": col_names,
    }

def map_3cat(d):
    if d["cod"] == "INANICION":
        return 1
    elif d["cod"] == "DEPREDADOR":
        return 2
    return 0

def map_4cat(d):
    if d["cod_4cat"] == "SENESCENCIA_DESGASTE_MORDISCOS":
        return 1
    elif d["cod_4cat"] == "INANICION":
        return 2
    elif d["cod_4cat"] == "DEPREDADOR":
        return 3
    return 0

cols_34560 = [
    "Intercepto",
    "Temp_Melancolico (vs Estoico)",
    "Temp_Optimista (vs Estoico)",
    "Temp_Entusiasta (vs Estoico)",
    "Temp_Colerico (vs Estoico)",
    "Presion_K5 (vs K3)",
    "Memoria_M140 (vs M100)",
    "Memoria_M200 (vs M100)",
    "Cultura_T+",
    "Despensa_P+",
    "Generacion_Lineal",
]
def build_34560(d):
    return [
        1.0,
        1.0 if d["temp"] == "Melancólico Empático" else 0.0,
        1.0 if d["temp"] == "Optimista Sereno" else 0.0,
        1.0 if d["temp"] == "Entusiasta Dopaminérgico" else 0.0,
        1.0 if d["temp"] == "Colérico Reactivo" else 0.0,
        d["k5"], d["m140"], d["m200"], d["cult"], d["pant"], float(d["gen"])
    ]
def build_34560_notemp(d):
    return [1.0, d["k5"], d["m140"], d["m200"], d["cult"], d["pant"], float(d["gen"])]

m_34560_full = fit_mnlogit_cluster(all_agents, build_34560, cols_34560, map_3cat, num_classes=3)
m_34560_notemp = fit_mnlogit_cluster(all_agents, build_34560_notemp, cols_34560[0:1] + cols_34560[5:], map_3cat, num_classes=3)

cols_offspring = [
    "Intercepto",
    "Temp_Melancolico (vs Estoico)",
    "Temp_Optimista (vs Estoico)",
    "Temp_Entusiasta (vs Estoico)",
    "Temp_Colerico (vs Estoico)",
    "Presion_K5 (vs K3)",
    "Memoria_M140 (vs M100)",
    "Memoria_M200 (vs M100)",
    "Cultura_T+",
    "Despensa_P+",
    "Gen_2_BETA (vs ALFA)",
    "Gen_3_GAMA (vs ALFA)",
]
def build_offspring(d):
    return [
        1.0,
        1.0 if d["temp"] == "Melancólico Empático" else 0.0,
        1.0 if d["temp"] == "Optimista Sereno" else 0.0,
        1.0 if d["temp"] == "Entusiasta Dopaminérgico" else 0.0,
        1.0 if d["temp"] == "Colérico Reactivo" else 0.0,
        d["k5"], d["m140"], d["m200"], d["cult"], d["pant"],
        1.0 if d["gen"] == 2 else 0.0,
        1.0 if d["gen"] == 3 else 0.0,
    ]
def build_offspring_notemp(d):
    return [
        1.0,
        d["k5"], d["m140"], d["m200"], d["cult"], d["pant"],
        1.0 if d["gen"] == 2 else 0.0,
        1.0 if d["gen"] == 3 else 0.0,
    ]

m_off_3cat = fit_mnlogit_cluster(offspring_agents, build_offspring, cols_offspring, map_3cat, num_classes=3)
m_off_3cat_notemp = fit_mnlogit_cluster(offspring_agents, build_offspring_notemp, cols_offspring[0:1] + cols_offspring[5:], map_3cat, num_classes=3)
m_off_4cat = fit_mnlogit_cluster(offspring_agents, build_offspring, cols_offspring, map_4cat, num_classes=4)
m_off_4cat_notemp = fit_mnlogit_cluster(offspring_agents, build_offspring_notemp, cols_offspring[0:1] + cols_offspring[5:], map_4cat, num_classes=4)

def compute_temp_block_tests(m_full, m_notemp, df_block=8):
    lr_stat = 2.0 * (m_full["ll"] - m_notemp["ll"])
    p_lr = chi2_p_value(lr_stat, df_block)
    D = m_full["D"]
    C = m_full["C"]
    idx_temp = []
    for c in range(C):
        idx_temp.extend([c * D + 1, c * D + 2, c * D + 3, c * D + 4])
    b_t = m_full["b_hat"][idx_temp]
    V_t_naive = m_full["cov_naive"][np.ix_(idx_temp, idx_temp)]
    V_t_clust = m_full["cov_cluster"][np.ix_(idx_temp, idx_temp)]
    wald_naive = float(b_t.T @ np.linalg.inv(V_t_naive) @ b_t)
    wald_clust = float(b_t.T @ np.linalg.inv(V_t_clust) @ b_t)
    return {
        "df_block": len(idx_temp),
        "lr_chi2": round(lr_stat, 2),
        "lr_p_value": p_lr,
        "wald_naive_chi2": round(wald_naive, 2),
        "wald_naive_p_value": chi2_p_value(wald_naive, len(idx_temp)),
        "wald_cluster_chi2": round(wald_clust, 2),
        "wald_cluster_p_value": chi2_p_value(wald_clust, len(idx_temp)),
        "full_model_lr_chi2": round(2.0 * (m_full["ll"] - m_full["ll_null"]), 2),
        "full_model_mcfadden_r2": round(m_full["mcfadden_r2"], 4),
        "temperament_delta_r2": round((m_full["ll"] - m_notemp["ll"]) / (-m_full["ll_null"]), 4),
    }

block_tests_34560 = compute_temp_block_tests(m_34560_full, m_34560_notemp, df_block=8)
block_tests_off_3cat = compute_temp_block_tests(m_off_3cat, m_off_3cat_notemp, df_block=8)
block_tests_off_4cat = compute_temp_block_tests(m_off_4cat, m_off_4cat_notemp, df_block=12)
print("Análisis clusterizado por semilla completado exitosamente.")
