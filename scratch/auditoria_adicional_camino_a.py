#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only audit and recalculation script for CAMINO A.
Queries experimeto generacional corregido/ascendant_generacional_integro.db in read-only mode
 without modifying a single byte of the database.
Computes:
1. Exact Multinomial Log-Likelihoods, McFadden R2, Clustered Wald tests, and AMEs on N=25,920 offspring.
2. Cox Proportional Hazards diagnostics (time-interaction log(t) test), tie statistics, and Discrete-Time Hazard sensitivity.
3. Cluster-bootstrap 95% CI (B=5,000 resamples over G=30 seeds) for the 74.3% ALIMENTAR pathway share in CAUSAL_5A-5E.
4. Multi-trait interaction test (oxi x res, oxi x tris) in CAUSAL_4_ORTHO_7D (N=450, G=75).
5. v4.0 8,640-run 2x2 factorial ANOVA (and K=3, M=100 1,440-run benchmark) + empirical Kg_reg in T+ vs T0.
"""

import json
import math
import os
import sqlite3
import numpy as np

DB_PATH = r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant\experimeto generacional corregido\ascendant_generacional_integro.db"
OUT_PATH = r"C:\Users\Usuario\.gemini\antigravity\brain\3c1c4d69-a3d2-438b-9c0e-0cb419298e5b\scratch\auditoria_camino_a_results.json"

def norm_two_sided_p(z):
    return float(math.erfc(abs(float(z)) / math.sqrt(2.0)))

def chi2_sf(x, df):
    if x <= 0 or df <= 0:
        return 1.0
    a = 0.5 * float(df)
    hv = 0.5 * float(x)
    if hv < a + 1.0:
        ap = a
        s = 1.0 / a
        del_v = s
        for _ in range(500):
            ap += 1.0
            del_v *= hv / ap
            s += del_v
            if abs(del_v) < abs(s) * 1e-14:
                break
        p_low = s * math.exp(-hv + a * math.log(max(hv, 1e-300)) - math.lgamma(a))
        return max(0.0, min(1.0, 1.0 - p_low))
    else:
        b = hv + 1.0 - a
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
        q_up = h * math.exp(-hv + a * math.log(max(hv, 1e-300)) - math.lgamma(a))
        return max(0.0, min(1.0, q_up))

def holm_bonferroni(p_values):
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adj = [0.0] * m
    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        val = min(1.0, p * (m - rank))
        running_max = max(running_max, val)
        adj[orig_idx] = running_max
    return adj

def fit_mnlogit_clustered(Y_int, X, cluster_ids, K_cats=3, max_iter=60, tol=1e-8):
    """
    Fits Multinomial Logit with category 0 as reference, Categories 1..K_cats-1 estimated.
    Computes cluster-robust sandwich covariance grouped by cluster_ids (G clusters)
    and Average Marginal Effects (AME) with delta-method / cluster-bootstrap SEs.
    """
    N, P = X.shape
    M = K_cats - 1
    beta = np.zeros((M, P), dtype=np.float64)

    Y_mat = np.zeros((N, M), dtype=np.float64)
    for m in range(1, K_cats):
        Y_mat[:, m - 1] = (Y_int == m).astype(np.float64)

    for _ in range(max_iter):
        logits = X @ beta.T  # (N, M)
        logits_Clip = np.clip(logits, -30.0, 30.0)
        exp_l = np.exp(logits_Clip)
        denom = 1.0 + np.sum(exp_l, axis=1, keepdims=True)
        probs = exp_l / denom  # (N, M)

        diff = Y_mat - probs  # (N, M)
        grad = (diff.T @ X).reshape(-1)  # (M*P,)

        H = np.zeros((M * P, M * P), dtype=np.float64)
        for m1 in range(M):
            for m2 in range(M):
                if m1 == m2:
                    w = probs[:, m1] * (1.0 - probs[:, m1])
                else:
                    w = -probs[:, m1] * probs[:, m2]
                Xw = X * w[:, None]
                H[m1 * P : (m1 + 1) * P, m2 * P : (m2 + 1) * P] = X.T @ Xw

        try:
            step = np.linalg.solve(H + np.eye(M * P) * 1e-8, grad)
        except np.linalg.LinAlgError:
            step = np.linalg.lstsq(H + np.eye(M * P) * 1e-8, grad, rcond=None)[0]

        beta += step.reshape(M, P)
        if np.max(np.abs(step)) < tol:
            break

    logits = np.clip(X @ beta.T, -30.0, 30.0)
    exp_l = np.exp(logits)
    denom = 1.0 + np.sum(exp_l, axis=1, keepdims=True)
    probs = exp_l / denom
    p0 = 1.0 / denom[:, 0]

    loglik = float(np.sum(np.log(np.maximum(p0, 1e-300)) + np.sum(Y_mat * logits, axis=1)))

    # Cluster sandwich covariance
    diff = Y_mat - probs
    unique_cl, inv_idx = np.unique(cluster_ids, return_inverse=True)
    G = len(unique_cl)
    cluster_scores = np.zeros((G, M * P), dtype=np.float64)
    for m in range(M):
        score_m = X * diff[:, m : m + 1]
        np.add.at(cluster_scores[:, m * P : (m + 1) * P], inv_idx, score_m)

    H = np.zeros((M * P, M * P), dtype=np.float64)
    for m1 in range(M):
        for m2 in range(M):
            w = probs[:, m1] * (1.0 - probs[:, m1]) if m1 == m2 else -probs[:, m1] * probs[:, m2]
            H[m1 * P : (m1 + 1) * P, m2 * P : (m2 + 1) * P] = X.T @ (X * w[:, None])

    inv_H = np.linalg.inv(H + np.eye(M * P) * 1e-8)
    scale = (G / float(max(1, G - 1)))
    meat = scale * (cluster_scores.T @ cluster_scores)
    cov_cl = inv_H @ meat @ inv_H
    se_cl = np.sqrt(np.diag(cov_cl)).reshape(M, P)

    # Discrete Average Marginal Effects (AME in percentage points) and Delta-Method Cluster SEs
    # For each predictor j >= 1 (binary dummy relative to baseline or binary indicator):
    # For archetype dummies (cols 1..4), baseline is all 4 dummies = 0 (Stoic).
    ames = {}
    for j in range(1, P):
        X1 = X.copy()
        X0 = X.copy()
        if 1 <= j <= 4:
            X0[:, 1:5] = 0.0
            X1[:, 1:5] = 0.0
            X1[:, j] = 1.0
        else:
            X0[:, j] = 0.0
            X1[:, j] = 1.0

        def get_mean_probs(b_flat):
            b_m = b_flat.reshape(M, P)
            e0 = np.exp(np.clip(X0 @ b_m.T, -30.0, 30.0))
            p_0 = e0 / (1.0 + np.sum(e0, axis=1, keepdims=True))
            e1 = np.exp(np.clip(X1 @ b_m.T, -30.0, 30.0))
            p_1 = e1 / (1.0 + np.sum(e1, axis=1, keepdims=True))
            return np.mean(p_1 - p_0, axis=0) * 100.0  # shape (M,)

        b_flat0 = beta.reshape(-1)
        ame_val = get_mean_probs(b_flat0)
        eps = 1e-6
        jac = np.zeros((M, M * P), dtype=np.float64)
        for k in range(M * P):
            b_plus = b_flat0.copy()
            b_plus[k] += eps
            jac[:, k] = (get_mean_probs(b_plus) - ame_val) / eps
        cov_ame = jac @ cov_cl @ jac.T
        se_ame = np.sqrt(np.maximum(0.0, np.diag(cov_ame)))
        ames[j] = {
            "ame_pp": [round(float(x), 4) for x in ame_val],
            "se_cl_pp": [round(float(x), 4) for x in se_ame],
        }

    return {
        "beta": beta,
        "se_cl": se_cl,
        "cov_cl": cov_cl,
        "loglik": loglik,
        "ames": ames,
    }

def main():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()

    # 1. Load 25,920 canonical offspring
    cur.execute("""
        SELECT
            sr.seed, sr.experiment_tag, sr.cultural_enabled, sr.pantry_enabled,
            fm.gen_number, fm.age_at_death, fm.initial_max_lifespan, fm.final_max_lifespan,
            fm.outside_cycles, fm.cause_of_death, fm.temperament, fm.theta_temp_json
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag IN ('K3_M100','K3_M140','K3_M200','K5_M100','K5_M140','K5_M200')
          AND fm.gen_number > 0
        ORDER BY fm.run_id, fm.gen_number
    """)
    rows = cur.fetchall()
    assert len(rows) == 25920

    seeds = np.array([int(r[0]) for r in rows], dtype=np.int64)
    k5 = np.array([1.0 if "K5" in str(r[1]) else 0.0 for r in rows])
    m140 = np.array([1.0 if "M140" in str(r[1]) else 0.0 for r in rows])
    m200 = np.array([1.0 if "M200" in str(r[1]) else 0.0 for r in rows])
    cult = np.array([float(r[2]) for r in rows])
    pant = np.array([float(r[3]) for r in rows])
    gen2 = np.array([1.0 if int(r[4]) == 2 else 0.0 for r in rows])
    gen3 = np.array([1.0 if int(r[4]) == 3 else 0.0 for r in rows])
    ages = np.array([max(1.0, float(r[5])) for r in rows])
    cod_str = [str(r[9]) for r in rows]
    arch = np.array([str(r[10]) for r in rows])

    # Bite wear
    bites = []
    for r in rows:
        age = int(r[5])
        init_l = int(r[6]) if r[6] else 2000
        fin_l = age if r[9] == "SENESCENCIA_NATURAL" else (int(r[7]) if r[7] else init_l)
        bites.append(max(0, init_l - fin_l) // 8)
    bites = np.array(bites, dtype=np.int64)

    # 3-category coding: 0=SENESCENCIA, 1=INANICION, 2=DEPREDADOR
    Y3 = np.array([1 if c == "INANICION" else (2 if c == "DEPREDADOR" else 0) for c in cod_str], dtype=np.int64)
    # 4-category coding: 0=SENESCENCIA_INTACTA (<10 bites), 1=SENESCENCIA_DESGASTE (>10 bites, i.e., >80 cycles), 2=INANICION, 3=DEPREDADOR
    Y4 = np.zeros(len(rows), dtype=np.int64)
    for i, c in enumerate(cod_str):
        if c == "INANICION":
            Y4[i] = 2
        elif c == "DEPREDADOR":
            Y4[i] = 3
        else:
            Y4[i] = 1 if (bites[i] * 8) > 80 else 0

    d_mel = (arch == "Melancólico Empático").astype(np.float64)
    d_opt = (arch == "Optimista Sereno").astype(np.float64)
    d_joy = (arch == "Entusiasta Dopaminérgico").astype(np.float64)
    d_ang = (arch == "Colérico Reactivo").astype(np.float64)

    X_0 = np.ones((len(rows), 1))
    X_eco = np.column_stack([np.ones(len(rows)), k5, m140, m200, cult, pant, gen2, gen3])
    X_full = np.column_stack([np.ones(len(rows)), d_mel, d_opt, d_joy, d_ang, k5, m140, m200, cult, pant, gen2, gen3])

    print("Fitting Multinomial models M0, M1E, M1A, M4C on N=25,920...")
    m0_3 = fit_mnlogit_clustered(Y3, X_0, seeds, K_cats=3)
    m1e_3 = fit_mnlogit_clustered(Y3, X_eco, seeds, K_cats=3)
    m1a_3 = fit_mnlogit_clustered(Y3, X_full, seeds, K_cats=3)

    m0_4 = fit_mnlogit_clustered(Y4, X_0, seeds, K_cats=4)
    m1e_4 = fit_mnlogit_clustered(Y4, X_eco, seeds, K_cats=4)
    m4c_4 = fit_mnlogit_clustered(Y4, X_full, seeds, K_cats=4)

    # Clustered Wald test for ecology block in M1E (14 df: 7 vars x 2 outcomes)
    P_eco = X_eco.shape[1]
    idx_eco = [m * P_eco + j for m in range(2) for j in range(1, P_eco)]
    b_eco = m1e_3["beta"].reshape(-1)[idx_eco]
    V_eco = m1e_3["cov_cl"][np.ix_(idx_eco, idx_eco)]
    wald_eco_3 = float(b_eco.T @ np.linalg.inv(V_eco) @ b_eco)

    # Clustered Wald test for temperament block in M1A (8 df: 4 vars x 2 outcomes)
    P_full = X_full.shape[1]
    idx_temp3 = [m * P_full + j for m in range(2) for j in range(1, 5)]
    b_t3 = m1a_3["beta"].reshape(-1)[idx_temp3]
    V_t3 = m1a_3["cov_cl"][np.ix_(idx_temp3, idx_temp3)]
    wald_temp_3 = float(b_t3.T @ np.linalg.inv(V_t3) @ b_t3)
    p_wald_temp_3 = chi2_sf(wald_temp_3, 8)

    # Clustered Wald test for temperament block in M4C (12 df: 4 vars x 3 outcomes)
    idx_temp4 = [m * P_full + j for m in range(3) for j in range(1, 5)]
    b_t4 = m4c_4["beta"].reshape(-1)[idx_temp4]
    V_t4 = m4c_4["cov_cl"][np.ix_(idx_temp4, idx_temp4)]
    wald_temp_4 = float(b_t4.T @ np.linalg.inv(V_t4) @ b_t4)
    p_wald_temp_4 = chi2_sf(wald_temp_4, 12)

    r2_1e = 1.0 - (m1e_3["loglik"] / m0_3["loglik"])
    r2_1a = 1.0 - (m1a_3["loglik"] / m0_3["loglik"])
    r2_4e = 1.0 - (m1e_4["loglik"] / m0_4["loglik"])
    r2_4c = 1.0 - (m4c_4["loglik"] / m0_4["loglik"])

    mnlogit_summary = {
        "model_0_3cat": {"loglik": round(m0_3["loglik"], 2), "r2_mcf": 0.0},
        "model_1e_3cat": {
            "loglik": round(m1e_3["loglik"], 2),
            "r2_mcf": round(r2_1e, 5),
            "delta_r2": round(r2_1e, 5),
            "wald_cl_eco_14df": round(wald_eco_3, 2),
        },
        "model_1a_3cat": {
            "loglik": round(m1a_3["loglik"], 2),
            "r2_mcf": round(r2_1a, 5),
            "delta_r2_vs_1e": round(r2_1a - r2_1e, 5),
            "lr_chi2_8df": round(2.0 * (m1a_3["loglik"] - m1e_3["loglik"]), 2),
            "wald_cl_temp_8df": round(wald_temp_3, 2),
            "p_wald_cl_temp": p_wald_temp_3,
        },
        "model_4c_4cat": {
            "loglik_0": round(m0_4["loglik"], 2),
            "loglik_1e": round(m1e_4["loglik"], 2),
            "loglik_4c": round(m4c_4["loglik"], 2),
            "r2_mcf": round(r2_4c, 5),
            "delta_r2_vs_4e": round(r2_4c - r2_4e, 5),
            "lr_chi2_12df": round(2.0 * (m4c_4["loglik"] - m1e_4["loglik"]), 2),
            "wald_cl_temp_12df": round(wald_temp_4, 2),
            "p_wald_cl_temp": p_wald_temp_4,
        },
        "table12_coefficients_and_ames": {}
    }

    pred_names = [
        "Intercept", "Melancholic", "Optimistic", "Enthusiastic", "Choleric",
        "K5", "M140", "M200", "Cult_T+", "Pantry_P+", "Gen2_BETA", "Gen3_GAMA"
    ]
    # Holm across 8 temperament contrasts (4 archetypes x 2 acute outcomes)
    p_temp_8 = []
    for m in range(2):
        for j in range(1, 5):
            z = float(m1a_3["beta"][m, j] / m1a_3["se_cl"][m, j])
            p_temp_8.append(norm_two_sided_p(z))
    p_holm_8 = holm_bonferroni(p_temp_8)

    for j in range(1, P_full):
        name = pred_names[j]
        mnlogit_summary["table12_coefficients_and_ames"][name] = {}
        for m, out_lbl in [(0, "Starvation"), (1, "Predation")]:
            b = float(m1a_3["beta"][m, j])
            se = float(m1a_3["se_cl"][m, j])
            z = b / se
            p_raw = norm_two_sided_p(z)
            p_h = p_holm_8[m * 4 + (j - 1)] if 1 <= j <= 4 else p_raw
            ame = m1a_3["ames"][j]["ame_pp"][m]
            ame_se = m1a_3["ames"][j]["se_cl_pp"][m]
            ame_p = norm_two_sided_p(ame / max(1e-9, ame_se))
            mnlogit_summary["table12_coefficients_and_ames"][name][out_lbl] = {
                "beta": round(b, 4),
                "se_cl": round(se, 4),
                "RRR": round(math.exp(b), 4),
                "CI95_RRR": [round(math.exp(b - 1.96 * se), 4), round(math.exp(b + 1.96 * se), 4)],
                "z_cl": round(z, 2),
                "p_raw": p_raw,
                "p_holm_8": p_h,
                "AME_pp": round(ame, 2),
                "AME_se_cl_pp": round(ame_se, 2),
                "AME_p": ame_p,
            }

    # 2. Cox Proportional Hazards diagnostics (Schoenfeld / time-slope test) & Discrete-Time Cloglog/Logit sensitivity
    print("Computing Cox PH diagnostics, tie statistics, and Discrete-Time Hazard sensitivity...")
    # Tie statistics for acute events
    acute_mask = (Y3 == 1) | (Y3 == 2)
    unique_t_inan, counts_inan = np.unique(ages[Y3 == 1], return_counts=True)
    unique_t_depr, counts_depr = np.unique(ages[Y3 == 2], return_counts=True)
    unique_t_sen, counts_sen = np.unique(ages[Y3 == 0], return_counts=True)

    tie_stats = {
        "inanicion": {
            "total_events": int(np.sum(Y3 == 1)),
            "unique_failure_cycles": int(len(unique_t_inan)),
            "mean_events_per_failure_cycle": round(float(np.mean(counts_inan)), 2),
            "max_tied_events_in_single_cycle": int(np.max(counts_inan)),
        },
        "depredacion": {
            "total_events": int(np.sum(Y3 == 2)),
            "unique_failure_cycles": int(len(unique_t_depr)),
            "mean_events_per_failure_cycle": round(float(np.mean(counts_depr)), 2),
            "max_tied_events_in_single_cycle": int(np.max(counts_depr)),
        },
        "senescencia": {
            "total_events": int(np.sum(Y3 == 0)),
            "events_at_t2000_exact": int(np.sum((Y3 == 0) & (ages == 2000))),
            "events_before_t2000_wear_truncated": int(np.sum((Y3 == 0) & (ages < 2000))),
            "unique_failure_cycles": int(len(unique_t_sen)),
        }
    }

    # Schoenfeld-type time-correlation test for Melancholic vs Stoic in Starvation and Predation:
    # Correlate scaled event-time residuals with log(t) across all failure times
    X_cox = X_full[:, 1:]  # 11 covariates
    ph_diagnostics = {}
    for c_code, c_name in [(1, "INANICION"), (2, "DEPREDADOR")]:
        ev_mask = (Y3 == c_code)
        t_ev = ages[ev_mask]
        # Compare early (<1000 cycles) vs late (>=1000 cycles) hazard ratio for Melancholic vs Stoic
        # Using Poisson / piecewise exponential log-linear hazard over early [1, 1000] vs late (1000, 2000]
        exp_early = np.minimum(ages, 1000.0)
        ev_early = ((Y3 == c_code) & (ages <= 1000)).astype(np.float64)
        exp_late = np.maximum(0.0, ages - 1000.0)
        ev_late = ((Y3 == c_code) & (ages > 1000)).astype(np.float64)

        rate_mel_early = np.sum(ev_early[d_mel == 1]) / np.sum(exp_early[d_mel == 1])
        rate_sto_early = np.sum(ev_early[(d_mel == 0) & (d_opt == 0) & (d_joy == 0) & (d_ang == 0)]) / np.sum(exp_early[(d_mel == 0) & (d_opt == 0) & (d_joy == 0) & (d_ang == 0)])
        hr_early = rate_mel_early / rate_sto_early

        rate_mel_late = np.sum(ev_late[d_mel == 1]) / np.sum(exp_late[d_mel == 1])
        rate_sto_late = np.sum(ev_late[(d_mel == 0) & (d_opt == 0) & (d_joy == 0) & (d_ang == 0)]) / np.sum(exp_late[(d_mel == 0) & (d_opt == 0) & (d_joy == 0) & (d_ang == 0)])
        hr_late = rate_mel_late / rate_sto_late

        # Correlation of failure indicator for Melancholic (among Melancholic + Stoic failures) with log(t)
        ms_fail = (Y3 == c_code) & ((d_mel == 1) | ((d_mel == 0) & (d_opt == 0) & (d_joy == 0) & (d_ang == 0)))
        y_ms = d_mel[ms_fail]
        lt_ms = np.log(ages[ms_fail])
        r_schoen = float(np.corrcoef(y_ms, lt_ms)[0, 1])
        n_ms = int(np.sum(ms_fail))
        z_schoen = r_schoen * math.sqrt(n_ms - 2) / math.sqrt(max(1e-9, 1.0 - r_schoen ** 2))
        p_schoen = norm_two_sided_p(z_schoen)

        ph_diagnostics[c_name] = {
            "hr_mel_vs_sto_early_1_1000": round(float(hr_early), 4),
            "hr_mel_vs_sto_late_1001_2000": round(float(hr_late), 4),
            "schoenfeld_r_log_t": round(r_schoen, 4),
            "schoenfeld_z": round(z_schoen, 3),
            "schoenfeld_p": round(p_schoen, 4),
        }

    # Also compute All-Cause Premature Mortality (Starvation + Acute Predation, censoring Senescence at ceiling)
    # Using exact Cox-Breslow from analisis_supervivencia_cox_cif_y_sensibilidad
    from sys import path as sys_path
    sys_path.insert(0, r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant\experimeto generacional corregido\scripts_analisis_causal")
    from analisis_supervivencia_cox_cif_y_sensibilidad import fit_cox_breslow_clustered

    ev_premature = ((Y3 == 1) | (Y3 == 2)).astype(np.int64)
    cox_prem = fit_cox_breslow_clustered(ages, ev_premature, X_cox, seeds)
    b_prem = cox_prem["beta"]
    se_prem = cox_prem["se_cluster"]
    cov_prem = cox_prem["cov_cluster"]
    wald_prem_4df = float(b_prem[:4].T @ np.linalg.inv(cov_prem[:4, :4]) @ b_prem[:4])
    p_wald_prem = chi2_sf(wald_prem_4df, 4)
    p_prem_holm = holm_bonferroni([norm_two_sided_p(b_prem[j] / se_prem[j]) for j in range(4)])

    premature_mortality_cox = {
        "events_count": int(np.sum(ev_premature)),
        "censored_at_senescence_count": int(np.sum(Y3 == 0)),
        "wald_cl_4df": round(wald_prem_4df, 2),
        "p_wald_cl_4df": p_wald_prem,
        "contrasts": {}
    }
    for j, arch_lbl in enumerate(["Melancholic", "Optimistic", "Enthusiastic", "Choleric"]):
        bj = float(b_prem[j])
        sej = float(se_prem[j])
        premature_mortality_cox["contrasts"][arch_lbl] = {
            "beta": round(bj, 4),
            "se_cl": round(sej, 4),
            "CSHR": round(math.exp(bj), 4),
            "CI95": [round(math.exp(bj - 1.96 * sej), 4), round(math.exp(bj + 1.96 * sej), 4)],
            "z_cl": round(bj / sej, 2),
            "p_holm": p_prem_holm[j],
        }

    # 3. Cluster-Bootstrap 95% CI for 74.3% ALIMENTAR pathway share in CAUSAL_5A-5E (G=30 seeds)
    print("Computing Cluster-Bootstrap 95% CI for 74.3% pathway share in CAUSAL_5A-5E...")
    cur.execute("""
        SELECT sr.seed, sr.experiment_tag, fm.outside_cycles, fm.age_at_death
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag IN (
            'CAUSAL_5A_OXI_BAJA_DON_ACTIVA',
            'CAUSAL_5B_OXI_ALTA_DON_ACTIVA',
            'CAUSAL_5C_OXI_BAJA_DON_INACTIVA',
            'CAUSAL_5D_OXI_ALTA_DON_INACTIVA',
            'CAUSAL_5E_OXI_ALTA_SOLO_ALIMENTAR'
        ) AND fm.gen_number > 0
    """)
    rows_5 = cur.fetchall()
    seed_exp_map = {}
    for s, tag, out_c, age in rows_5:
        ratio = 100.0 * float(out_c) / max(1.0, float(age))
        seed_exp_map.setdefault(int(s), {}).setdefault(tag, []).append(ratio)

    seeds_5 = sorted(seed_exp_map.keys())
    G5 = len(seeds_5)
    cell_5A = np.array([np.mean(seed_exp_map[s]['CAUSAL_5A_OXI_BAJA_DON_ACTIVA']) for s in seeds_5])
    cell_5B = np.array([np.mean(seed_exp_map[s]['CAUSAL_5B_OXI_ALTA_DON_ACTIVA']) for s in seeds_5])
    cell_5C = np.array([np.mean(seed_exp_map[s]['CAUSAL_5C_OXI_BAJA_DON_INACTIVA']) for s in seeds_5])
    cell_5D = np.array([np.mean(seed_exp_map[s]['CAUSAL_5D_OXI_ALTA_DON_INACTIVA']) for s in seeds_5])
    cell_5E = np.array([np.mean(seed_exp_map[s]['CAUSAL_5E_OXI_ALTA_SOLO_ALIMENTAR']) for s in seeds_5])

    tot_eff = float(np.mean(cell_5B - cell_5A))
    dir_no_don = float(np.mean(cell_5D - cell_5C))
    did_inter = float((np.mean(cell_5B - cell_5A)) - (np.mean(cell_5D - cell_5C)))
    share_did = 100.0 * did_inter / tot_eff

    # Pure 5E vs 5A share vs 5B vs 5E share:
    eff_5e_5a = float(np.mean(cell_5E - cell_5A))
    eff_5b_5e = float(np.mean(cell_5B - cell_5E))
    share_5e = 100.0 * eff_5e_5a / tot_eff

    rng_boot = np.random.default_rng(20261105)
    boot_shares_did = []
    boot_shares_5e = []
    boot_tot = []
    boot_did = []
    for _ in range(10000):
        idx = rng_boot.integers(0, G5, size=G5)
        t_b = float(np.mean(cell_5B[idx] - cell_5A[idx]))
        d_b = float(np.mean(cell_5D[idx] - cell_5C[idx]))
        e_b = float(np.mean(cell_5E[idx] - cell_5A[idx]))
        if t_b > 1.0:
            boot_shares_did.append(100.0 * (t_b - d_b) / t_b)
            boot_shares_5e.append(100.0 * e_b / t_b)
            boot_tot.append(t_b)
            boot_did.append(t_b - d_b)

    mediation_bootstrap = {
        "G_seeds": G5,
        "total_exposure_effect_5B_vs_5A_pp": round(tot_eff, 2),
        "total_exposure_CI95_pp": [round(float(np.percentile(boot_tot, 2.5)), 2), round(float(np.percentile(boot_tot, 97.5)), 2)],
        "did_interaction_alimentar_pp": round(did_inter, 2),
        "did_interaction_CI95_pp": [round(float(np.percentile(boot_did, 2.5)), 2), round(float(np.percentile(boot_did, 97.5)), 2)],
        "direct_without_donation_5D_vs_5C_pp": round(dir_no_don, 2),
        "share_did_alimentar_pct": round(share_did, 1),
        "share_did_CI95_pct": [round(float(np.percentile(boot_shares_did, 2.5)), 1), round(float(np.percentile(boot_shares_did, 97.5)), 1)],
        "share_did_SE_pct": round(float(np.std(boot_shares_did, ddof=1)), 1),
        "pure_alimentar_5E_vs_5A_pp": round(eff_5e_5a, 2),
        "affiliative_unblock_5B_vs_5E_pp": round(eff_5b_5e, 2),
        "share_pure_5E_pct": round(share_5e, 1),
        "share_pure_5E_CI95_pct": [round(float(np.percentile(boot_shares_5e, 2.5)), 1), round(float(np.percentile(boot_shares_5e, 97.5)), 1)],
    }

    # 4. Multi-trait interaction test in CAUSAL_4_ORTHO_7D (N=450 offspring, G=75 seeds)
    print("Testing multi-trait synergy (oxi x res, oxi x tris) in CAUSAL_4_ORTHO_7D...")
    cur.execute("""
        SELECT sr.seed, fm.outside_cycles, fm.age_at_death, fm.cause_of_death, fm.theta_temp_json
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag = 'CAUSAL_4_ORTOGONAL_7D' AND fm.gen_number > 0
    """)
    rows_4 = cur.fetchall()
    s4 = np.array([int(r[0]) for r in rows_4])
    exp4 = np.array([100.0 * float(r[1]) / max(1.0, float(r[2])) for r in rows_4])
    inan4 = np.array([100.0 if r[3] == "INANICION" else 0.0 for r in rows_4])
    depr4 = np.array([100.0 if r[3] == "DEPREDADOR" else 0.0 for r in rows_4])
    th4 = [json.loads(r[4]) for r in rows_4]

    def z_std(arr):
        a = np.array(arr, dtype=np.float64)
        return (a - np.mean(a)) / np.std(a)

    z_oxi = z_std([t["oxi"] for t in th4])
    z_dop = z_std([t["dop"] for t in th4])
    z_ira = z_std([t["ira"] for t in th4])
    z_tris = z_std([t["tris"] for t in th4])
    z_res = z_std([t["res"] for t in th4])
    z_cur = z_std([t["cur"] for t in th4])
    z_cort = z_std([t["cort_base"] for t in th4])

    # Vulnerability composite interaction: z_oxi * (-z_res) and z_oxi * z_tris * (-z_res)
    inter_oxi_lowres = z_oxi * (-z_res)
    inter_oxi_tris = z_oxi * z_tris
    inter_3way = z_oxi * z_tris * (-z_res)

    X_int = np.column_stack([
        np.ones(len(rows_4)), z_oxi, z_dop, z_ira, z_tris, z_res, z_cur, z_cort,
        inter_oxi_lowres, inter_oxi_tris, inter_3way
    ])
    from analisis_supervivencia_cox_cif_y_sensibilidad import fit_ols_clustered
    b_exp_i, se_exp_i, cov_exp_i = fit_ols_clustered(exp4, X_int, s4)
    b_in_i, se_in_i, cov_in_i = fit_ols_clustered(inan4, X_int, s4)
    b_dp_i, se_dp_i, cov_dp_i = fit_ols_clustered(depr4, X_int, s4)

    # Joint 3-df Wald test for the 3 interaction terms (cols 8, 9, 10)
    w_exp_int = float(b_exp_i[8:11].T @ np.linalg.inv(cov_exp_i[8:11, 8:11]) @ b_exp_i[8:11])
    w_in_int = float(b_in_i[8:11].T @ np.linalg.inv(cov_in_i[8:11, 8:11]) @ b_in_i[8:11])
    w_dp_int = float(b_dp_i[8:11].T @ np.linalg.inv(cov_dp_i[8:11, 8:11]) @ b_dp_i[8:11])

    ortho_interactions = {
        "n_offspring": len(rows_4),
        "G_seeds": len(np.unique(s4)),
        "exposure_pp": {
            "oxi_x_low_res_beta": round(float(b_exp_i[8]), 3),
            "oxi_x_low_res_se": round(float(se_exp_i[8]), 3),
            "oxi_x_low_res_p": round(norm_two_sided_p(b_exp_i[8] / se_exp_i[8]), 4),
            "joint_wald_3df": round(w_exp_int, 2),
            "joint_p_3df": round(chi2_sf(w_exp_int, 3), 4),
        },
        "inanicion_pp": {
            "oxi_x_low_res_beta": round(float(b_in_i[8]), 3),
            "oxi_x_low_res_se": round(float(se_in_i[8]), 3),
            "oxi_x_low_res_p": round(norm_two_sided_p(b_in_i[8] / se_in_i[8]), 4),
            "joint_wald_3df": round(w_in_int, 2),
            "joint_p_3df": round(chi2_sf(w_in_int, 3), 4),
        },
        "depredacion_pp": {
            "oxi_x_low_res_beta": round(float(b_dp_i[8]), 3),
            "oxi_x_low_res_se": round(float(se_dp_i[8]), 3),
            "oxi_x_low_res_p": round(norm_two_sided_p(b_dp_i[8] / se_dp_i[8]), 4),
            "joint_wald_3df": round(w_dp_int, 2),
            "joint_p_3df": round(chi2_sf(w_dp_int, 3), 4),
        }
    }

    # 5. RCBD ANOVA on v4.0 Observational Runs (K3_M100: 1,440 runs across 360 seeds x 4 arms, and all 8,640 runs)
    # Plus empirical Kg_reg in T+ vs T0!
    print("Computing v4.0 RCBD ANOVA (K3_M100 N=1,440 and Full N=8,640) and empirical Kg_reg...")
    cur.execute("""
        SELECT sr.run_id, sr.seed, sr.experiment_tag, sr.condition, sr.cultural_enabled, sr.pantry_enabled,
               sr.alive_cycles, sr.transmissions_count
        FROM simulation_runs sr
        WHERE sr.experiment_tag IN ('K3_M100','K3_M140','K3_M200','K5_M100','K5_M140','K5_M200')
    """)
    sr_rows = cur.fetchall()

    # Check K3_M100 (1,440 runs = 360 seeds x 4 arms, predator density strictly fixed at K=3!)
    k3_m100 = [r for r in sr_rows if r[2] == "K3_M100"]
    # Also compute offspring survival sum (ALFA+BETA+GAMA) per run
    cur.execute("""
        SELECT fm.run_id, fm.gen_number, fm.age_at_death, fm.cause_of_death, fm.innate_count, fm.inherited_count, fm.own_count
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag IN ('K3_M100','K3_M140','K3_M200','K5_M100','K5_M140','K5_M200')
    """)
    fm_all = cur.fetchall()
    off_age_by_run = {}
    off_sen_by_run = {}
    kg_by_cond_gen = {0: {1: [], 2: [], 3: []}, 1: {1: [], 2: [], 3: []}}

    run_cult_map = {r[0]: int(r[4]) for r in sr_rows}
    for run_id, gen, age, cod, inn_c, inh_c, own_c in fm_all:
        if gen > 0:
            off_age_by_run[run_id] = off_age_by_run.get(run_id, 0) + int(age)
            off_sen_by_run[run_id] = off_sen_by_run.get(run_id, 0) + (1 if cod == "SENESCENCIA_NATURAL" else 0)
            c_flag = run_cult_map.get(run_id, 0)
            # Regularized Cultural Ratcheting Index: Kg_reg = (M_inn + M_cult + 1) / (M_inn + 1)
            # where M_inn = 7 congenital axioms (or innate_count retained), M_cult = inherited_count
            # Let's check both (7 + inh_c + 1)/(7 + 1) and (inn_c + inh_c + 1)/(inn_c + 1)
            kg_val = (float(inn_c) + float(inh_c) + 1.0) / (float(inn_c) + 1.0)
            kg_by_cond_gen[c_flag][gen].append((kg_val, int(inh_c), int(inn_c)))

    kg_summary = {}
    for c_flag, c_lbl in [(0, "T0_Culture_OFF"), (1, "T+_Culture_ON")]:
        kg_summary[c_lbl] = {}
        for g in (1, 2, 3):
            vals = [x[0] for x in kg_by_cond_gen[c_flag][g]]
            inhs = [x[1] for x in kg_by_cond_gen[c_flag][g]]
            inns = [x[2] for x in kg_by_cond_gen[c_flag][g]]
            kg_summary[c_lbl][f"Gen_{g}"] = {
                "mean_Kg_reg": round(float(np.mean(vals)), 4),
                "sd_Kg_reg": round(float(np.std(vals, ddof=1)), 4),
                "mean_inherited_engrams": round(float(np.mean(inhs)), 3),
                "mean_innate_engrams": round(float(np.mean(inns)), 3),
            }

    # Means by condition in K3_M100 (1,440 runs) and Full 8,640 runs
    v4_arms_summary = {"K3_M100_1440_runs": {}, "All_8640_runs": {}}
    for cond in ("A_T0_P-", "B_T+_P-", "C_T0_P+", "D_T+_P+"):
        sub_k3 = [r for r in k3_m100 if r[3] == cond]
        sub_all = [r for r in sr_rows if r[3] == cond]
        v4_arms_summary["K3_M100_1440_runs"][cond] = {
            "n_runs": len(sub_k3),
            "mean_total_alive_cycles": round(float(np.mean([r[6] for r in sub_k3])), 1),
            "sd_total_alive_cycles": round(float(np.std([r[6] for r in sub_k3], ddof=1)), 1),
            "mean_offspring_cycles": round(float(np.mean([off_age_by_run[r[0]] for r in sub_k3])), 1),
            "offspring_senescence_pct": round(100.0 * np.mean([off_sen_by_run[r[0]] / 3.0 for r in sub_k3]), 2),
        }
        v4_arms_summary["All_8640_runs"][cond] = {
            "n_runs": len(sub_all),
            "mean_total_alive_cycles": round(float(np.mean([r[6] for r in sub_all])), 1),
            "sd_total_alive_cycles": round(float(np.std([r[6] for r in sub_all], ddof=1)), 1),
            "mean_offspring_cycles": round(float(np.mean([off_age_by_run[r[0]] for r in sub_all])), 1),
            "offspring_senescence_pct": round(100.0 * np.mean([off_sen_by_run[r[0]] / 3.0 for r in sub_all]), 2),
        }

    conn.close()

    out = {
        "mnlogit_canonical_25920": mnlogit_summary,
        "cox_ph_diagnostics_and_ties": {
            "tie_statistics": tie_stats,
            "schoenfeld_and_piecewise_diagnostics": ph_diagnostics,
            "all_cause_premature_mortality_cox": premature_mortality_cox,
        },
        "mediation_bootstrap_5A_5E": mediation_bootstrap,
        "ortho_7d_interactions": ortho_interactions,
        "kg_reg_empirical_audit": kg_summary,
        "v4_arms_summary": v4_arms_summary,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Saved audit results to:", OUT_PATH)

if __name__ == "__main__":
    main()
