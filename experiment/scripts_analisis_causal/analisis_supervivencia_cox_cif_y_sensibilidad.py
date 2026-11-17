#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proyecto Ascendant — Análisis de Supervivencia de Cox (Verosimilitud Parcial de Breslow + Lin-Wei Clusterizado),
Funciones de Incidencia Acumulada (CIF de Aalen-Johansen), Dosis-Respuesta Intra-Arquetipo y Sensibilidad de Mordiscos.
Autor Único: David San Nicolás Montero (ORCID: 0009-0000-9977-007X)
"""

import json
import math
import os
import sqlite3
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def norm_two_sided_p(z):
    return float(math.erfc(abs(float(z)) / math.sqrt(2.0)))


def chi2_even_df_sf(x, df):
    if x <= 0:
        return 1.0
    k = int(df) // 2
    half_x = 0.5 * float(x)
    s = 0.0
    term = 1.0
    for j in range(k):
        if j > 0:
            term *= half_x / j
        s += term
    return float(math.exp(-half_x) * s)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ascendant_generacional_integro.db")
OUT_JSON = os.path.join(BASE_DIR, "analisis_cox_cif_intraarquetipo_y_sensibilidad.json")

ARCHETYPES_ORDER = [
    "Estoico Desapegado",
    "Melancólico Empático",
    "Optimista Sereno",
    "Entusiasta Dopaminérgico",
    "Colérico Reactivo",
]


def holm_bonferroni(p_values):
    """Ajuste secuencial de Holm-Bonferroni para una lista de p-valores."""
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adj = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        val = min(1.0, p * (m - rank))
        running_max = max(running_max, val)
        adj[orig_idx] = running_max
    return adj


def fit_cox_breslow_clustered(times, events, X, cluster_ids, max_iter=50, tol=1e-8):
    """
    Ajusta un modelo de riesgos proporcionales de Cox por causa específica (CSHR)
    mediante verosimilitud parcial exacta de Breslow sobre tiempos discretos/continuos
    y calcula la matriz de covarianzas robusta tipo sándwich de Lin-Wei (1989)
    agrupada por semilla (cluster_ids, G=360).
    """
    n, p = X.shape
    beta = np.zeros(p, dtype=np.float64)

    # Ordenar tiempos únicos de fallo donde events == 1
    unique_t = np.sort(np.unique(times[events == 1]))

    for _ in range(max_iter):
        exp_xb = np.exp(np.clip(X @ beta, -30.0, 30.0))
        grad = np.zeros(p, dtype=np.float64)
        hess = np.zeros((p, p), dtype=np.float64)
        loglik = 0.0

        for t_k in unique_t:
            risk_mask = (times >= t_k)
            fail_mask = (times == t_k) & (events == 1)
            d_k = int(np.sum(fail_mask))
            if d_k == 0:
                continue

            w_r = exp_xb[risk_mask]
            X_r = X[risk_mask]
            S0 = float(np.sum(w_r))
            S1 = X_r.T @ w_r
            E_x = S1 / S0

            # S2 = sum_{j in R(t_k)} w_j X_j X_j^T
            Xw = X_r * w_r[:, None]
            S2 = X_r.T @ Xw
            V_x = (S2 / S0) - np.outer(E_x, E_x)

            x_fail_sum = np.sum(X[fail_mask], axis=0)
            loglik += float(x_fail_sum @ beta) - d_k * math.log(S0)
            grad += x_fail_sum - d_k * E_x
            hess += d_k * V_x

        try:
            step = np.linalg.solve(hess + np.eye(p) * 1e-9, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(hess + np.eye(p) * 1e-9, grad, rcond=None)[0]

        beta += step
        if np.max(np.abs(step)) < tol:
            break

    # Residuos de score individuales de Lin-Wei (1989):
    # u_i = delta_i * (X_i - E(t_i)) - sum_{t_k <= t_i} (d_k / S0(t_k)) * exp(X_i beta) * (X_i - E(t_k))
    exp_xb = np.exp(np.clip(X @ beta, -30.0, 30.0))
    hess = np.zeros((p, p), dtype=np.float64)
    score_resid = np.zeros((n, p), dtype=np.float64)

    # Acumuladores en el tiempo para eficiencia O(N + K*p)
    cum_h0 = np.zeros(n, dtype=np.float64)
    cum_h0_Ex = np.zeros((n, p), dtype=np.float64)

    for t_k in unique_t:
        risk_mask = (times >= t_k)
        fail_mask = (times == t_k) & (events == 1)
        d_k = int(np.sum(fail_mask))
        if d_k == 0:
            continue
        w_r = exp_xb[risk_mask]
        X_r = X[risk_mask]
        S0 = float(np.sum(w_r))
        S1 = X_r.T @ w_r
        E_x = S1 / S0
        Xw = X_r * w_r[:, None]
        S2 = X_r.T @ Xw
        V_x = (S2 / S0) - np.outer(E_x, E_x)
        hess += d_k * V_x

        if np.any(fail_mask):
            score_resid[fail_mask] += (X[fail_mask] - E_x)

        dh0 = d_k / S0
        cum_h0[risk_mask] += dh0
        cum_h0_Ex[risk_mask] += dh0 * E_x

    score_resid -= exp_xb[:, None] * (X * cum_h0[:, None] - cum_h0_Ex)

    inv_hess = np.linalg.inv(hess + np.eye(p) * 1e-9)
    se_naive = np.sqrt(np.diag(inv_hess))

    # Agrupación por semilla G=360
    unique_clusters, inv_idx = np.unique(cluster_ids, return_inverse=True)
    G = len(unique_clusters)
    cluster_scores = np.zeros((G, p), dtype=np.float64)
    np.add.at(cluster_scores, inv_idx, score_resid)

    dof_scale = G / float(max(1, G - 1))
    meat = dof_scale * (cluster_scores.T @ cluster_scores)
    cov_cluster = inv_hess @ meat @ inv_hess
    se_cluster = np.sqrt(np.diag(cov_cluster))

    return {
        "beta": beta,
        "se_naive": se_naive,
        "se_cluster": se_cluster,
        "cov_cluster": cov_cluster,
        "loglik": loglik,
    }


def compute_aalen_johansen_cif(times, causes, eval_times=(500, 1000, 1500, 2000)):
    """
    Calcula la Función de Incidencia Acumulada (CIF_c(t)) no paramétrica de Aalen-Johansen
    para 3 riesgos competitivos mutuamente excluyentes (c in {0: Senescencia, 1: Inanición, 2: Depredación}).
    """
    max_t = 2000
    n_total = len(times)
    S_prev = 1.0
    cif = {0: np.zeros(max_t + 1), 1: np.zeros(max_t + 1), 2: np.zeros(max_t + 1)}

    for t in range(1, max_t + 1):
        n_risk = int(np.sum(times >= t))
        for c in (0, 1, 2):
            cif[c][t] = cif[c][t - 1]
        if n_risk > 0:
            d_total = 0
            for c in (0, 1, 2):
                d_c = int(np.sum((times == t) & (causes == c)))
                cif[c][t] += S_prev * (d_c / float(n_risk))
                d_total += d_c
            S_prev = S_prev * (1.0 - d_total / float(n_risk))

    out = {}
    for et in eval_times:
        out[str(et)] = {
            "inanicion_pct": round(float(cif[1][et]) * 100.0, 2),
            "depredacion_pct": round(float(cif[2][et]) * 100.0, 2),
            "senescencia_pct": round(float(cif[0][et]) * 100.0, 2),
            "supervivencia_S_t_pct": round(max(0.0, 100.0 - float(cif[0][et] + cif[1][et] + cif[2][et]) * 100.0), 2),
        }
    return out


def fit_ols_clustered(y, X, cluster_ids):
    """Regresión lineal con errores estándar robustos agrupados por semilla (CR1)."""
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta

    unique_clusters, inv_idx = np.unique(cluster_ids, return_inverse=True)
    G = len(unique_clusters)
    cluster_u = np.zeros((G, k), dtype=np.float64)
    np.add.at(cluster_u, inv_idx, X * resid[:, None])

    scale = (G / float(G - 1)) * ((n - 1) / float(n - k))
    meat = scale * (cluster_u.T @ cluster_u)
    cov_cl = XtX_inv @ meat @ XtX_inv
    se_cl = np.sqrt(np.diag(cov_cl))
    return beta, se_cl, cov_cl


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Sincronizar columnas explícitas en SQLite para consistencia 100% auditable
    cur.execute("UPDATE simulation_runs SET num_predators = 3 WHERE experiment_tag LIKE 'K3_%'")
    cur.execute("UPDATE simulation_runs SET num_predators = 5 WHERE experiment_tag LIKE 'K5_%'")
    cur.execute("UPDATE simulation_runs SET max_engrams = 100 WHERE experiment_tag LIKE '%_M100'")
    cur.execute("UPDATE simulation_runs SET max_engrams = 140 WHERE experiment_tag LIKE '%_M140'")
    cur.execute("UPDATE simulation_runs SET max_engrams = 200 WHERE experiment_tag LIKE '%_M200'")
    cur.execute("""
        UPDATE final_memories
        SET final_max_lifespan = age_at_death
        WHERE cause_of_death = 'SENESCENCIA_NATURAL' AND age_at_death < initial_max_lifespan
    """)
    conn.commit()

    cur.execute("""
        SELECT
            sr.seed,
            sr.experiment_tag,
            sr.num_predators,
            sr.max_engrams,
            sr.cultural_enabled,
            sr.pantry_enabled,
            fm.agent_id,
            fm.gen_number,
            fm.age_at_death,
            fm.initial_max_lifespan,
            fm.final_max_lifespan,
            fm.outside_cycles,
            fm.cause_of_death,
            fm.temperament,
            fm.theta_temp_json,
            fm.engrams_json
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag IN ('K3_M100','K3_M140','K3_M200','K5_M100','K5_M140','K5_M200')
          AND sr.seed >= 50000 AND sr.seed < 50360
          AND fm.gen_number > 0
    """)
    rows = cur.fetchall()
    conn.close()

    print(f"Descendientes cargados (ALFA, BETA, GAMA): N = {len(rows)} (esperado: 25920)")
    assert len(rows) == 25920, f"Se esperaban 25920 descendientes, se obtuvieron {len(rows)}"

    seeds = []
    k5_arr = []
    m140_arr = []
    m200_arr = []
    cult_arr = []
    pant_arr = []
    gen2_arr = []
    gen3_arr = []
    ages = []
    bites_arr = []
    outside_ratio_arr = []
    causes_arr = []
    arch_arr = []
    theta_vecs = []
    feed_rate_arr = []

    for r in rows:
        (seed, exp_tag, k_pred, m_eng, cult, pant, ag_id, gen_num, age,
         init_max, final_max, out_cyc, cause, temp_name, theta_j, eng_j) = r

        k_val = 5 if "K5" in str(exp_tag) else 3
        m_val = 140 if "M140" in str(exp_tag) else (200 if "M200" in str(exp_tag) else 100)

        seeds.append(int(seed))
        k5_arr.append(1.0 if k_val == 5 else 0.0)
        m140_arr.append(1.0 if m_val == 140 else 0.0)
        m200_arr.append(1.0 if m_val == 200 else 0.0)
        cult_arr.append(1.0 if int(cult) == 1 else 0.0)
        pant_arr.append(1.0 if int(pant) == 1 else 0.0)
        gen2_arr.append(1.0 if int(gen_num) == 2 else 0.0)
        gen3_arr.append(1.0 if int(gen_num) == 3 else 0.0)

        age_f = max(1.0, float(age))
        ages.append(age_f)
        init_l = int(init_max) if init_max and int(init_max) > 0 else 2000
        fin_l = int(age) if cause == "SENESCENCIA_NATURAL" else (int(final_max) if final_max and int(final_max) > 0 else init_l)
        loss = max(0, init_l - fin_l)
        bites = loss // 8
        bites_arr.append(bites)
        outside_ratio_arr.append(float(out_cyc) / age_f)

        if cause == "INANICION":
            causes_arr.append(1)
        elif cause == "DEPREDADOR":
            causes_arr.append(2)
        else:
            causes_arr.append(0)

        arch_arr.append(temp_name)
        th = json.loads(theta_j) if theta_j else {}
        theta_vecs.append([
            float(th.get("oxi", 0.5)),
            float(th.get("dop", 0.5)),
            float(th.get("ira", 0.5)),
            float(th.get("tris", 0.5)),
            float(th.get("res", 0.5)),
            float(th.get("cur", 0.5)),
            float(th.get("cort_base", 0.2)),
        ])

        engrams = json.loads(eng_j) if eng_j else []
        feed_cnt = 0
        for e in engrams:
            if e.get("action") == "ALIMENTAR" and e.get("origin") != "INNATA":
                feed_cnt += int(e.get("repetitionCount", 1)) if not e.get("isCompressed") else 1
        # Usar conteo exacto de episodios ALIMENTAR o repetitionCount máximo del tipo ALTRUISMO_NUTRICIONAL - 8 innatos
        max_rep_feed = 8
        for e in engrams:
            if e.get("type") == "ALTRUISMO_NUTRICIONAL" and not e.get("isCompressed"):
                max_rep_feed = max(max_rep_feed, int(e.get("repetitionCount", 8)))
        true_feeds = max(0, max_rep_feed - 8)
        feed_rate_arr.append((true_feeds / age_f) * 1000.0)

    seeds = np.array(seeds, dtype=np.int64)
    ages = np.array(ages, dtype=np.float64)
    bites_arr = np.array(bites_arr, dtype=np.int64)
    outside_ratio_arr = np.array(outside_ratio_arr, dtype=np.float64)
    causes_arr = np.array(causes_arr, dtype=np.int64)
    arch_arr = np.array(arch_arr)
    theta_mat = np.array(theta_vecs, dtype=np.float64)
    feed_rate_arr = np.array(feed_rate_arr, dtype=np.float64)

    # Matriz de diseño con Estoico como referencia (4 dummies de arquetipo + 7 covariables ecológicas)
    d_mel = (arch_arr == "Melancólico Empático").astype(np.float64)
    d_opt = (arch_arr == "Optimista Sereno").astype(np.float64)
    d_joy = (arch_arr == "Entusiasta Dopaminérgico").astype(np.float64)
    d_ang = (arch_arr == "Colérico Reactivo").astype(np.float64)

    X_cox = np.column_stack([
        d_mel, d_opt, d_joy, d_ang,
        np.array(k5_arr), np.array(m140_arr), np.array(m200_arr),
        np.array(cult_arr), np.array(pant_arr),
        np.array(gen2_arr), np.array(gen3_arr)
    ])
    var_names = [
        "Melancólico vs Estoico",
        "Optimista vs Estoico",
        "Entusiasta vs Estoico",
        "Colérico vs Estoico",
        "K=5 vs K=3",
        "M=140 vs M=100",
        "M=200 vs M=100",
        "Cultura T+ vs T0",
        "Despensa P+ vs P-",
        "Gen 2 (BETA) vs Gen 1 (ALFA)",
        "Gen 3 (GAMA) vs Gen 1 (ALFA)",
    ]

    print("1. Ajustando modelos de Cox por causa específica (Breslow + Lin-Wei clusterizado por semilla G=360)...")
    cox_results = {}
    for c_code, c_label in [(1, "INANICION"), (2, "DEPREDADOR"), (0, "SENESCENCIA_NATURAL")]:
        ev = (causes_arr == c_code).astype(np.int64)
        res = fit_cox_breslow_clustered(ages, ev, X_cox, seeds)
        beta = res["beta"]
        se_cl = res["se_cluster"]
        se_nv = res["se_naive"]
        cov_cl = res["cov_cluster"]

        # Test de Wald clusterizado del bloque de temperamento (primeros 4 coeficientes)
        b_temp = beta[:4]
        V_temp = cov_cl[:4, :4]
        wald_temp = float(b_temp.T @ np.linalg.inv(V_temp) @ b_temp)
        p_wald_temp = chi2_even_df_sf(wald_temp, df=4)

        p_vals_temp = [norm_two_sided_p(beta[j] / se_cl[j]) for j in range(4)]
        p_holm_temp = holm_bonferroni(p_vals_temp)

        coefs_dict = {}
        for j, name in enumerate(var_names):
            b_j = float(beta[j])
            se_j = float(se_cl[j])
            z_j = b_j / se_j
            p_j = norm_two_sided_p(z_j)
            cshr = math.exp(b_j)
            ci_lo = math.exp(b_j - 1.96 * se_j)
            ci_hi = math.exp(b_j + 1.96 * se_j)
            coefs_dict[name] = {
                "beta": round(b_j, 4),
                "se_naive": round(float(se_nv[j]), 4),
                "se_cluster": round(se_j, 4),
                "deff_se": round(se_j / max(1e-9, float(se_nv[j])), 3),
                "CSHR": round(cshr, 4),
                "IC95_CSHR": [round(ci_lo, 4), round(ci_hi, 4)],
                "z_cluster": round(z_j, 3),
                "p_cluster": p_j,
                "p_holm_4arch": round(p_holm_temp[j], 6) if j < 4 else None,
            }

        cox_results[c_label] = {
            "events_count": int(np.sum(ev)),
            "log_partial_likelihood": round(float(res["loglik"]), 2),
            "wald_temperament_block_4df": round(wald_temp, 2),
            "p_wald_temperament_block": p_wald_temp,
            "coefficients": coefs_dict,
        }

    print("2. Calculando Funciones de Incidencia Acumulada (CIF de Aalen-Johansen) por arquetipo...")
    cif_by_arch = {}
    for arch in ARCHETYPES_ORDER:
        m = (arch_arr == arch)
        cif_by_arch[arch] = compute_aalen_johansen_cif(ages[m], causes_arr[m])

    print("3. Evaluando Dosis-Respuesta Continua Intra-Arquetipo de theta_oxi...")
    theta_oxi = theta_mat[:, 0]
    # Centrar theta_oxi dentro de cada arquetipo para aislar exclusivamente el jitter aleatorio +/-8%
    theta_oxi_within = np.zeros_like(theta_oxi)
    arch_means_oxi = {}
    for arch in ARCHETYPES_ORDER:
        m = (arch_arr == arch)
        mu_a = float(np.mean(theta_oxi[m]))
        arch_means_oxi[arch] = round(mu_a, 4)
        theta_oxi_within[m] = (theta_oxi[m] - mu_a) * 10.0  # Por cada +0.10 de theta_oxi intra-arquetipo

    # Diseño con efectos fijos de arquetipo + variación intra-arquetipo de theta_oxi + ecología
    X_within = np.column_stack([
        np.ones(len(rows)),
        theta_oxi_within,
        d_mel, d_opt, d_joy, d_ang,
        np.array(k5_arr), np.array(m140_arr), np.array(m200_arr),
        np.array(cult_arr), np.array(pant_arr),
        np.array(gen2_arr), np.array(gen3_arr),
    ])
    b_feed_w, se_feed_w, _ = fit_ols_clustered(feed_rate_arr, X_within, seeds)
    b_exp_w, se_exp_w, _ = fit_ols_clustered(outside_ratio_arr * 100.0, X_within, seeds)
    b_inan_w, se_inan_w, _ = fit_ols_clustered((causes_arr == 1).astype(np.float64) * 100.0, X_within, seeds)

    # También regresión continua 7D estandarizada sobre los 25.920 descendientes
    theta_std = (theta_mat - np.mean(theta_mat, axis=0)) / np.std(theta_mat, axis=0)
    X_7d = np.column_stack([
        np.ones(len(rows)),
        theta_std,
        np.array(k5_arr), np.array(m140_arr), np.array(m200_arr),
        np.array(cult_arr), np.array(pant_arr),
        np.array(gen2_arr), np.array(gen3_arr),
    ])
    b_feed_7d, se_feed_7d, _ = fit_ols_clustered(feed_rate_arr, X_7d, seeds)
    b_exp_7d, se_exp_7d, _ = fit_ols_clustered(outside_ratio_arr * 100.0, X_7d, seeds)
    b_inan_7d, se_inan_7d, _ = fit_ols_clustered((causes_arr == 1).astype(np.float64) * 100.0, X_7d, seeds)
    b_depr_7d, se_depr_7d, _ = fit_ols_clustered((causes_arr == 2).astype(np.float64) * 100.0, X_7d, seeds)

    trait_names = ["oxi", "dop", "ira", "tris", "res", "cur", "cort_base"]
    continuous_7d_summary = {}
    p_list_7d = []
    for idx_t, t_name in enumerate(trait_names):
        j = 1 + idx_t
        for b_vec, se_vec in [(b_feed_7d, se_feed_7d), (b_exp_7d, se_exp_7d), (b_inan_7d, se_inan_7d), (b_depr_7d, se_depr_7d)]:
            z_v = float(b_vec[j] / se_vec[j])
            p_list_7d.append(norm_two_sided_p(z_v))
    p_holm_7d = holm_bonferroni(p_list_7d)

    for idx_t, t_name in enumerate(trait_names):
        j = 1 + idx_t
        base_k = idx_t * 4
        continuous_7d_summary[t_name] = {
            "feed_per_1k_beta_SD": round(float(b_feed_7d[j]), 4),
            "feed_se_cluster": round(float(se_feed_7d[j]), 4),
            "feed_p_holm": round(p_holm_7d[base_k + 0], 6),
            "exposure_pp_beta_SD": round(float(b_exp_7d[j]), 4),
            "exposure_se_cluster": round(float(se_exp_7d[j]), 4),
            "exposure_p_holm": round(p_holm_7d[base_k + 1], 6),
            "inanicion_pp_beta_SD": round(float(b_inan_7d[j]), 4),
            "inanicion_se_cluster": round(float(se_inan_7d[j]), 4),
            "inanicion_p_holm": round(p_holm_7d[base_k + 2], 6),
            "depredacion_pp_beta_SD": round(float(b_depr_7d[j]), 4),
            "depredacion_se_cluster": round(float(se_depr_7d[j]), 4),
            "depredacion_p_holm": round(p_holm_7d[base_k + 3], 6),
        }

    print("4. Calculando Rejilla de Sensibilidad del Umbral de Mordiscos Recibidos (>=1, >=5, >=10, >=15, >=20)...")
    # Regla operacional exacta: mordiscos_recibidos = (initial_max_lifespan - final_max_lifespan) // 8
    sensitivity_grid = {}
    for thresh in (1, 5, 10, 15, 20):
        cycles_lost_thresh = thresh * 8
        by_arch = {}
        tot_sen_pure = 0
        tot_sen_wear = 0
        for arch in ARCHETYPES_ORDER:
            m = (arch_arr == arch)
            n_a = int(np.sum(m))
            n_inan = int(np.sum(m & (causes_arr == 1)))
            n_depr = int(np.sum(m & (causes_arr == 2)))
            n_sen_wear = int(np.sum(m & (causes_arr == 0) & (bites_arr >= thresh)))
            n_sen_pure = int(np.sum(m & (causes_arr == 0) & (bites_arr < thresh)))
            assert n_inan + n_depr + n_sen_wear + n_sen_pure == n_a
            tot_sen_pure += n_sen_pure
            tot_sen_wear += n_sen_wear
            by_arch[arch] = {
                "n_total": n_a,
                "inanicion_n": n_inan,
                "inanicion_pct": round(100.0 * n_inan / n_a, 2),
                "depredacion_aguda_n": n_depr,
                "depredacion_aguda_pct": round(100.0 * n_depr / n_a, 2),
                "senescencia_desgaste_n": n_sen_wear,
                "senescencia_desgaste_pct": round(100.0 * n_sen_wear / n_a, 2),
                "senescencia_pura_n": n_sen_pure,
                "senescencia_pura_pct": round(100.0 * n_sen_pure / n_a, 2),
            }

        # Cox CSHR para el evento de Senescencia Acelerada por Desgaste (>= thresh mordiscos) vs Estoico
        ev_wear = ((causes_arr == 0) & (bites_arr >= thresh)).astype(np.int64)
        cox_w = fit_cox_breslow_clustered(ages, ev_wear, X_cox, seeds)
        mel_b = float(cox_w["beta"][0])
        mel_se = float(cox_w["se_cluster"][0])
        mel_z = mel_b / mel_se
        mel_p = norm_two_sided_p(mel_z)

        sensitivity_grid[f"umbral_{thresh}_mordiscos_{cycles_lost_thresh}_ciclos"] = {
            "threshold_bites": thresh,
            "threshold_cycles_lost": cycles_lost_thresh,
            "total_senescencia_desgaste_n": tot_sen_wear,
            "total_senescencia_desgaste_pct": round(100.0 * tot_sen_wear / len(rows), 2),
            "total_senescencia_pura_n": tot_sen_pure,
            "total_senescencia_pura_pct": round(100.0 * tot_sen_pure / len(rows), 2),
            "melancolico_vs_estoico_CSHR_desgaste": round(math.exp(mel_b), 4),
            "melancolico_vs_estoico_IC95": [round(math.exp(mel_b - 1.96 * mel_se), 4), round(math.exp(mel_b + 1.96 * mel_se), 4)],
            "melancolico_vs_estoico_z_cluster": round(mel_z, 3),
            "melancolico_vs_estoico_p_cluster": mel_p,
            "by_archetype": by_arch,
        }

    # Estadísticos descriptivos exactos de mordiscos recibidos por arquetipo
    bites_descriptives = {}
    for arch in ARCHETYPES_ORDER:
        m = (arch_arr == arch)
        b_sub = bites_arr[m]
        bites_descriptives[arch] = {
            "n": int(np.sum(m)),
            "mean_bites": round(float(np.mean(b_sub)), 3),
            "sd_bites": round(float(np.std(b_sub)), 3),
            "median_bites": float(np.median(b_sub)),
            "iqr_bites": [float(np.percentile(b_sub, 25)), float(np.percentile(b_sub, 75))],
            "mean_cycles_lost": round(float(np.mean(b_sub * 8.0)), 2),
        }

    output = {
        "metadata": {
            "author": "David San Nicolás Montero",
            "orcid": "0009-0000-9977-007X",
            "sample": "N = 25.920 descendientes homogéneos (ALFA, BETA, GAMA; techo inicial 2.000 ciclos; G = 360 semillas independientes)",
            "operational_bite_rule": "mordiscos_recibidos = (initial_max_lifespan - final_max_lifespan) / 8 (exactamente 8 ciclos vitales transferidos por mordisco en línea 2046 del motor)",
        },
        "cox_breslow_cause_specific_clustered": cox_results,
        "aalen_johansen_cif_by_archetype": cif_by_arch,
        "intra_archetype_continuous_oxi": {
            "archetype_mean_theta_oxi": arch_means_oxi,
            "within_archetype_per_010_theta_oxi": {
                "feed_per_1k_beta": round(float(b_feed_w[1]), 4),
                "feed_per_1k_se_cluster": round(float(se_feed_w[1]), 4),
                "feed_per_1k_z": round(float(b_feed_w[1] / se_feed_w[1]), 3),
                "feed_per_1k_p": norm_two_sided_p(b_feed_w[1] / se_feed_w[1]),
                "exposure_pp_beta": round(float(b_exp_w[1]), 4),
                "exposure_pp_se_cluster": round(float(se_exp_w[1]), 4),
                "exposure_pp_z": round(float(b_exp_w[1] / se_exp_w[1]), 3),
                "exposure_pp_p": norm_two_sided_p(b_exp_w[1] / se_exp_w[1]),
                "inanicion_pp_beta": round(float(b_inan_w[1]), 4),
                "inanicion_pp_se_cluster": round(float(se_inan_w[1]), 4),
                "inanicion_pp_z": round(float(b_inan_w[1] / se_inan_w[1]), 3),
                "inanicion_pp_p": norm_two_sided_p(b_inan_w[1] / se_inan_w[1]),
            },
            "standardized_7d_continuous_regressions": continuous_7d_summary,
        },
        "bite_wear_descriptives_by_archetype": bites_descriptives,
        "bite_wear_sensitivity_grid": sensitivity_grid,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ Guardado exitosamente en: {OUT_JSON}")
    print("\n--- RESUMEN COX BRESLOW CLUSTERIZADO (Melancólico vs Estoico) ---")
    for k, v in cox_results.items():
        c_mel = v["coefficients"]["Melancólico vs Estoico"]
        print(f"  {k}: CSHR = {c_mel['CSHR']} {c_mel['IC95_CSHR']}, z_cl = {c_mel['z_cluster']}, p = {c_mel['p_cluster']:.3e} (p_Holm = {c_mel['p_holm_4arch']}) | Wald bloque 4df = {v['wald_temperament_block_4df']} (p = {v['p_wald_temperament_block']:.3e})")


if __name__ == "__main__":
    main()
