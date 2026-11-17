#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proyecto Ascendant — Batería Ampliada de Intervenciones Mecanicistas, Mediación Factorial 2x2,
Aislamiento de Vías de Oxitocina, Barrido Dosis-Respuesta y Diseño Ortogonal 7D con Persistencia Íntegra en SQLite.
Autor Único: David San Nicolás Montero (ORCID: 0009-0000-9977-007X)
"""

import json
import math
import multiprocessing as mp
import os
import sqlite3
import sys
import time
from datetime import datetime
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ascendant_generacional_integro.db")
OUT_JSON = os.path.join(BASE_DIR, "resultados_intervenciones_causales_directas.json")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import ejecutar_experimento_generacional as eng


def norm_two_sided_p(z):
    return float(math.erfc(abs(float(z)) / math.sqrt(2.0)))


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


def fisher_exact_two_sided(a, b, c, d):
    """Test exacto de Fisher bilateral para tabla 2x2 [[a, b], [c, d]] usando log-factoriales exactos."""
    n = a + b + c + d
    if n == 0:
        return 1.0
    r1 = a + b
    r2 = c + d
    c1 = a + c
    c2 = b + d

    def log_hypergeom(x):
        return (
            math.lgamma(r1 + 1) - math.lgamma(x + 1) - math.lgamma(r1 - x + 1)
            + math.lgamma(r2 + 1) - math.lgamma(c1 - x + 1) - math.lgamma(r2 - (c1 - x) + 1)
            - (math.lgamma(n + 1) - math.lgamma(c1 + 1) - math.lgamma(c2 + 1))
        )

    x_min = max(0, c1 - r2)
    x_max = min(r1, c1)
    lp_obs = log_hypergeom(a)
    p_sum = 0.0
    for x in range(x_min, x_max + 1):
        lp = log_hypergeom(x)
        if lp <= lp_obs + 1e-12:
            p_sum += math.exp(lp)
    return min(1.0, max(0.0, p_sum))


def fit_ols_clustered(y, X, cluster_ids):
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X + np.eye(k) * 1e-9)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta
    unique_cl, inv_idx = np.unique(cluster_ids, return_inverse=True)
    G = len(unique_cl)
    cl_u = np.zeros((G, k), dtype=np.float64)
    np.add.at(cl_u, inv_idx, X * resid[:, None])
    scale = (G / float(max(1, G - 1))) * ((n - 1) / float(max(1, n - k)))
    meat = scale * (cl_u.T @ cl_u)
    cov_cl = XtX_inv @ meat @ XtX_inv
    se_cl = np.sqrt(np.diag(cov_cl))
    return beta, se_cl, cov_cl


def fit_logit_clustered(y, X, cluster_ids, max_iter=50, tol=1e-8):
    n, k = X.shape
    beta = np.zeros(k, dtype=np.float64)
    p_bar = np.clip(np.mean(y), 0.01, 0.99)
    beta[0] = math.log(p_bar / (1.0 - p_bar))
    for _ in range(max_iter):
        eta = np.clip(X @ beta, -25.0, 25.0)
        p = 1.0 / (1.0 + np.exp(-eta))
        w = p * (1.0 - p)
        grad = X.T @ (y - p)
        H = (X * w[:, None]).T @ X + np.eye(k) * 1e-8
        step = np.linalg.solve(H, grad)
        beta += step
        if np.max(np.abs(step)) < tol:
            break
    eta = np.clip(X @ beta, -25.0, 25.0)
    p = 1.0 / (1.0 + np.exp(-eta))
    w = p * (1.0 - p)
    H_inv = np.linalg.inv((X * w[:, None]).T @ X + np.eye(k) * 1e-8)
    scores_i = X * (y - p)[:, None]
    unique_cl, inv_idx = np.unique(cluster_ids, return_inverse=True)
    G = len(unique_cl)
    cl_u = np.zeros((G, k), dtype=np.float64)
    np.add.at(cl_u, inv_idx, scores_i)
    scale = (G / float(max(1, G - 1))) * ((n - 1) / float(max(1, n - k)))
    cov_cl = scale * (H_inv @ (cl_u.T @ cl_u) @ H_inv)
    se_cl = np.sqrt(np.diag(cov_cl))
    return beta, se_cl, cov_cl


def _worker_run_sim(task):
    (exp_tag, seed, cult_en, pant_en, k_pred, max_eng,
     theta_mode, feed_gain, ira_gain, fixed_oxi, nonfeed_clamp) = task

    eng.LIVE_LOCAL_LLM_ENABLED = False
    eng.MAX_ENGRAMS = int(max_eng)
    eng.ANCIENT_ZONE_LIMIT = int(max_eng * 0.20)
    eng.CAUSAL_THETA_MODE = theta_mode
    eng.CAUSAL_FEED_OXI_GAIN = float(feed_gain)
    eng.CAUSAL_TRAUMA_IRA_GAIN = float(ira_gain)
    eng.CAUSAL_FIXED_THETA_OXI = fixed_oxi
    eng.CAUSAL_NONFEED_OXI_CLAMP = nonfeed_clamp

    rng = eng.Mulberry32(seed)
    state = eng.create_environment_state(
        rng, cultural_enabled=cult_en, pantry_enabled=pant_en, num_predators=k_pred
    )
    state["seed"] = seed
    state["condition"] = f"{exp_tag}_K{k_pred}_{eng.get_condition_code(cult_en, pant_en)}"

    beh_stats = {
        ag_id: {
            "donations_given": 0,
            "donations_received": 0,
            "harvests": 0,
            "self_eats": 0,
            "hugs": 0,
            "asks": 0,
            "alpha_trauma_sum": 0.0,
            "alpha_trauma_cnt": 0,
        }
        for ag_id in ("P0", "ALFA", "BETA", "GAMA")
    }

    orig_step = eng.step_agent_mind

    def hooked_step(r_gen, env_s, w):
        if not w["born"] or not w["agentAlive"]:
            return orig_step(r_gen, env_s, w)
        ag_id = w["id"]
        pre_inv = int(w["inventory"])
        pre_e = float(w["energy"])
        h = w["h"]
        if pre_e < 35.0:
            desp_d = 0.60 * h["ira"] * eng.CAUSAL_TRAUMA_IRA_GAIN + 0.40 * h["res"]
            e_rat = max(0.0, (pre_e - 8.0) / 27.0)
            a_tr = eng.clip(e_rat / max(0.15, desp_d), 0.12, 1.0)
            beh_stats[ag_id]["alpha_trauma_sum"] += a_tr
            beh_stats[ag_id]["alpha_trauma_cnt"] += 1

        orig_step(r_gen, env_s, w)

        if w["thoughtLog"]:
            act = w["thoughtLog"][0]["action"]
            out_txt = w["thoughtLog"][0]["outcome"]
            if int(w["inventory"]) > pre_inv or "cacé una pieza" in out_txt or "recolecté" in out_txt:
                beh_stats[ag_id]["harvests"] += 1
            if act == "ALIMENTAR":
                beh_stats[ag_id]["donations_given"] += 1
                other_w, _ = eng.get_living_companion(env_s, w)
                if other_w and other_w["id"] in beh_stats:
                    beh_stats[other_w["id"]]["donations_received"] += 1
            elif act in ("COMER", "COMER_REFUGIO"):
                beh_stats[ag_id]["self_eats"] += 1
            elif act == "ABRAZAR":
                beh_stats[ag_id]["hugs"] += 1
            elif act == "PREGUNTAR":
                beh_stats[ag_id]["asks"] += 1

    eng.step_agent_mind = hooked_step
    try:
        for _ in range(eng.MAX_GLOBAL_CYCLES + 1):
            eng.step_generational_world(rng, state)
            g = state["agents"]["GAMA"]
            if g["born"] and not g["agentAlive"]:
                break
    finally:
        eng.step_agent_mind = orig_step

    for ag_id in ("P0", "ALFA", "BETA", "GAMA"):
        ag = state["agents"][ag_id]
        if ag["born"] and ag_id not in state["finalMemoriesSnapshot"]:
            ag["causeOfDeath"] = ag["causeOfDeath"] or "SENESCENCIA_NATURAL"
            state["finalMemoriesSnapshot"][ag_id] = eng.snapshot_agent_memory(ag)
        if ag_id in state["finalMemoriesSnapshot"]:
            b_st = beh_stats[ag_id]
            mean_alpha = (
                round(b_st["alpha_trauma_sum"] / b_st["alpha_trauma_cnt"], 4)
                if b_st["alpha_trauma_cnt"] > 0 else 1.0
            )
            freqs = dict(ag.get("frequencies", {}))
            ep_s = state["finalMemoriesSnapshot"][ag_id]["epistemicStats"]
            ep_s["actionFrequencies"] = freqs
            ep_s["causalLinkTelemetry"] = {
                "donationsGiven": b_st["donations_given"],
                "donationsReceived": b_st["donations_received"],
                "harvestsCount": b_st["harvests"],
                "selfEatsCount": b_st["self_eats"],
                "hugsCount": b_st["hugs"],
                "asksCount": b_st["asks"],
                "meanAlphaTraumaUnder35": mean_alpha,
                "causalArm": exp_tag,
                "thetaMode": theta_mode,
            }
    return (exp_tag, seed, cult_en, pant_en, k_pred, max_eng, state)


def insert_run_into_db(cur, exp_tag, seed, cult_en, pant_en, k_pred, max_eng, env_state):
    now_iso = datetime.now().isoformat()
    snaps = env_state["finalMemoriesSnapshot"]
    alive_cycles = sum(int(s.get("ageAtDeath", 0)) for s in snaps.values())
    outside_cycles = sum(int(s.get("outsideCycles", 0)) for s in snaps.values())
    surprised_cnt = sum(1 for e in env_state["predatorEncounters"] if e.get("surprisedInDaydream"))
    evasions_cnt = sum(int(s.get("attentionSchema", {}).get("earlyEvasionsCount", 0)) for s in snaps.values())
    ignored_cnt = sum(int(s.get("attentionSchema", {}).get("ignoredStimuliCount", 0)) for s in snaps.values())
    cond_val = env_state.get("condition", eng.get_condition_code(bool(cult_en), bool(pant_en)))

    cur.execute(
        """INSERT INTO simulation_runs
           (timestamp, total_cycles, final_shelter_meat, transmissions_count, predator_attacks_count,
            condition, seed, cultural_enabled, pantry_enabled, alive_cycles, outside_cycles,
            surprised_daydream_count, early_evasions_count, ignored_stimuli_count,
            num_predators, max_engrams, experiment_tag)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (now_iso, env_state["globalCycle"], env_state["shelterMeat"],
         len(env_state["culturalTransmissions"]), len(env_state["predatorEncounters"]),
         cond_val, int(seed), 1 if cult_en else 0, 1 if pant_en else 0,
         alive_cycles, outside_cycles, surprised_cnt, evasions_cnt, ignored_cnt,
         int(k_pred), int(max_eng), exp_tag)
    )
    run_id = cur.lastrowid

    cur.executemany(
        "INSERT INTO event_tree (run_id, cycle, event_type, agent_id, description) VALUES (?, ?, ?, ?, ?)",
        [(run_id, ev["cycle"], ev["type"], ev["agentId"], ev["description"]) for ev in env_state["eventTree"]]
    )

    cur.executemany(
        """INSERT INTO cultural_transmissions
           (run_id, cycle, from_agent, to_agent, conclusion_key, statement, valence, confidence, accepted, reasoning)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(run_id, tr["cycle"], tr["fromAgent"], tr["toAgent"], tr["key"], tr["statement"],
          tr.get("valence"), tr.get("confidence"), 1 if tr["accepted"] else 0, tr["reasoning"])
         for tr in env_state["culturalTransmissions"]]
    )

    for ag_id, snap in snaps.items():
        engrams = snap["engrams"]
        latent_refl = snap.get("latentReflections", [])
        innate_c = sum(1 for e in engrams if e.get("origin") == "INNATA")
        inherited_c = sum(1 for e in engrams if str(e.get("origin", "")).startswith("HEREDADA_DE_"))
        own_c = len(engrams) - innate_c - inherited_c
        cur.execute(
            """INSERT INTO final_memories
               (run_id, agent_id, name, gen_number, age_at_death, initial_max_lifespan, final_max_lifespan,
                outside_cycles, cause_of_death, temperament, theta_temp_json, final_hormones_json,
                attention_schema_json, epistemic_stats_json, engrams_count, innate_count, inherited_count,
                own_count, accepted_ideas_json, engrams_json, latent_reflections_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, ag_id, snap["name"], snap["genNumber"], snap["ageAtDeath"],
                snap.get("initialMaxLifespan", 800 if snap["genNumber"] == 0 else 2000),
                snap.get("maxLifespan", snap["ageAtDeath"]),
                snap.get("outsideCycles", 0),
                snap["causeOfDeath"], snap["temperament"],
                json.dumps(snap.get("thetaTemp", {}), ensure_ascii=False),
                json.dumps(snap.get("finalHormones", {}), ensure_ascii=False),
                json.dumps(snap.get("attentionSchema", {}), ensure_ascii=False),
                json.dumps(snap.get("epistemicStats", {}), ensure_ascii=False),
                len(engrams), innate_c, inherited_c, own_c,
                json.dumps(snap["acceptedIdeasList"], ensure_ascii=False),
                json.dumps(engrams, ensure_ascii=False),
                json.dumps(latent_refl, ensure_ascii=False),
            )
        )
    return run_id


def build_task_list(existing_keys):
    """
    Construye la lista completa de corridas de intervención mecanicista que faltan por ejecutar.
    """
    arms = [
        # Batería 1: Intercambio quirúrgico de theta_oxi y ablaciones pareadas (45 semillas x 2 regímenes = 90 corridas = 360 agentes = 270 descendientes)
        ("CAUSAL_0_CONTROL",           range(50000, 50045), "STANDARD",           1.0, 1.0, None, None),
        ("CAUSAL_1_SWAP_OXI",          range(50000, 50045), "SWAP_OXI_MEL_STOIC", 1.0, 1.0, None, None),
        ("CAUSAL_2_ABLACION_DONACION", range(50000, 50045), "STANDARD",           0.0, 1.0, None, None),
        ("CAUSAL_3_ABLACION_IRA",      range(50000, 50045), "STANDARD",           1.0, 0.0, None, None),
        # Batería 2: Diseño Ortogonal 7D de alta potencia (75 semillas x 2 regímenes = 150 corridas = 600 agentes = 450 descendientes)
        ("CAUSAL_4_ORTOGONAL_7D",      range(50000, 50075), "ORTHOGONAL_7D",      1.0, 1.0, None, None),
        # Batería 3: Diseño Factorial 2x2 de Mediación (Oxitocina Baja/Alta x Donación Activa/Inactiva) + Aislamiento de Vía Afiliativa (30 semillas x 2 = 60 corridas = 240 agentes = 180 descendientes)
        ("CAUSAL_5A_OXI_BAJA_DON_ACTIVA",    range(50000, 50030), "STANDARD", 1.0, 1.0, 0.22, None),
        ("CAUSAL_5B_OXI_ALTA_DON_ACTIVA",    range(50000, 50030), "STANDARD", 1.0, 1.0, 0.86, None),
        ("CAUSAL_5C_OXI_BAJA_DON_INACTIVA",  range(50000, 50030), "STANDARD", 0.0, 1.0, 0.22, None),
        ("CAUSAL_5D_OXI_ALTA_DON_INACTIVA",  range(50000, 50030), "STANDARD", 0.0, 1.0, 0.86, None),
        ("CAUSAL_5E_OXI_ALTA_SOLO_ALIMENTAR", range(50000, 50030), "STANDARD", 1.0, 1.0, 0.86, 0.22),
        # Batería 4: Barrido Dosis-Respuesta de CAUSAL_FEED_OXI_GAIN in {0.0, 0.5, 1.0, 1.5, 2.0} (30 semillas x 2 = 60 corridas = 180 descendientes)
        ("CAUSAL_6A_DOSE_FEED_05",     range(50000, 50030), "STANDARD", 0.5, 1.0, None, None),
        ("CAUSAL_6B_DOSE_FEED_15",     range(50000, 50030), "STANDARD", 1.5, 1.0, None, None),
        ("CAUSAL_6C_DOSE_FEED_20",     range(50000, 50030), "STANDARD", 2.0, 1.0, None, None),
    ]

    tasks = []
    for exp_tag, seed_range, theta_mode, feed_gain, ira_gain, fixed_oxi, nonfeed_clamp in arms:
        for seed in seed_range:
            for k_pred in (3, 5):
                if (exp_tag, int(seed), int(k_pred)) not in existing_keys:
                    tasks.append((
                        exp_tag, int(seed), True, False, int(k_pred), 140,
                        theta_mode, feed_gain, ira_gain, fixed_oxi, nonfeed_clamp
                    ))
    return tasks


def extract_agent_metrics(rows):
    out = []
    for r in rows:
        (run_id, exp_tag, seed, cond, k_pred, cult, pant, ag_id, gen_num, age,
         init_max, final_max, out_cyc, cause, temp_name, theta_j, ep_j, eng_j) = r
        age_f = max(1.0, float(age))
        th = json.loads(theta_j) if theta_j else {}
        ep = json.loads(ep_j) if ep_j else {}
        engrams = json.loads(eng_j) if eng_j else []

        if "causalLinkTelemetry" in ep:
            clt = ep["causalLinkTelemetry"]
            feeds = int(clt.get("donationsGiven", 0))
            feeds_rec = int(clt.get("donationsReceived", 0))
            harvests = int(clt.get("harvestsCount", 0))
            hugs = int(clt.get("hugsCount", 0))
            asks = int(clt.get("asksCount", 0))
            mean_alpha = float(clt.get("meanAlphaTraumaUnder35", 1.0))
        elif "actionFrequencies" in ep:
            af = ep["actionFrequencies"]
            feeds = max(0, int(af.get("ALIMENTAR", 8)) - 8)
            feeds_rec = 0
            harvests = 0
            hugs = max(0, int(af.get("ABRAZAR", 10)) - 10)
            asks = max(0, int(af.get("PREGUNTAR", 8)) - 8)
            mean_alpha = 1.0
        else:
            feeds = 0
            feeds_rec = 0
            harvests = 0
            hugs = 0
            asks = 0
            mean_alpha = 1.0

        init_l = int(init_max) if init_max and int(init_max) > 0 else (800 if int(gen_num) == 0 else 2000)
        fin_l = int(age) if cause == "SENESCENCIA_NATURAL" else (int(final_max) if final_max and int(final_max) > 0 else init_l)
        bites = max(0, init_l - fin_l) // 8

        out.append({
            "run_id": int(run_id),
            "exp_tag": exp_tag,
            "seed": int(seed),
            "condition": cond,
            "k5": 1.0 if int(k_pred) == 5 else 0.0,
            "cult": int(cult),
            "pant": int(pant),
            "agent_id": ag_id,
            "gen": int(gen_num),
            "age": age_f,
            "bites": bites,
            "outside_ratio": float(out_cyc) / age_f,
            "cause": cause,
            "temperament": temp_name,
            "theta": th,
            "feeds": feeds,
            "feeds_received": feeds_rec,
            "harvests": harvests,
            "mean_alpha_trauma": mean_alpha,
            "feed_per_1k": (feeds / age_f) * 1000.0,
            "affiliative_per_1k": ((hugs + asks) / age_f) * 1000.0,
            "engrams_count": len(engrams),
        })
    return out


def summarize_group(agents):
    n = len(agents)
    if n == 0:
        return {}
    k_inan = sum(1 for a in agents if a["cause"] == "INANICION")
    k_depr = sum(1 for a in agents if a["cause"] == "DEPREDADOR")
    k_sen = sum(1 for a in agents if a["cause"] == "SENESCENCIA_NATURAL")

    # Errores estándar agrupados por semilla
    by_seed = {}
    for a in agents:
        by_seed.setdefault(a["seed"], []).append(a)
    G = len(by_seed)
    seed_inan = [100.0 * sum(1 for x in v if x["cause"] == "INANICION") / len(v) for v in by_seed.values()]
    seed_depr = [100.0 * sum(1 for x in v if x["cause"] == "DEPREDADOR") / len(v) for v in by_seed.values()]
    seed_sen = [100.0 * sum(1 for x in v if x["cause"] == "SENESCENCIA_NATURAL") / len(v) for v in by_seed.values()]
    se_inan = float(np.std(seed_inan, ddof=1) / math.sqrt(G)) if G > 1 else 0.0
    se_depr = float(np.std(seed_depr, ddof=1) / math.sqrt(G)) if G > 1 else 0.0
    se_sen = float(np.std(seed_sen, ddof=1) / math.sqrt(G)) if G > 1 else 0.0

    return {
        "n": n,
        "G_seeds": G,
        "theta_oxi_mean": round(float(np.mean([a["theta"].get("oxi", 0.5) for a in agents])), 3),
        "feed_per_1k": round(float(np.mean([a["feed_per_1k"] for a in agents])), 2),
        "affiliative_per_1k": round(float(np.mean([a["affiliative_per_1k"] for a in agents])), 2),
        "exposure_ratio": round(float(np.mean([a["outside_ratio"] for a in agents])), 4),
        "mean_bites": round(float(np.mean([a["bites"] for a in agents])), 2),
        "mean_age": round(float(np.mean([a["age"] for a in agents])), 1),
        "inanicion_k": k_inan,
        "inanicion_k_over_n": f"{k_inan}/{n}",
        "inanicion_pct": round(100.0 * k_inan / n, 2),
        "inanicion_se_cluster_pct": round(se_inan, 2),
        "depredacion_k": k_depr,
        "depredacion_k_over_n": f"{k_depr}/{n}",
        "depredacion_pct": round(100.0 * k_depr / n, 2),
        "depredacion_se_cluster_pct": round(se_depr, 2),
        "senescencia_k": k_sen,
        "senescencia_k_over_n": f"{k_sen}/{n}",
        "senescencia_pct": round(100.0 * k_sen / n, 2),
        "senescencia_se_cluster_pct": round(se_sen, 2),
    }


def compare_two_groups(g_treat, g_ctrl):
    """Compara dos grupos de agentes reportando diferencias en pp, IC95% clusterizado y test exacto de Fisher."""
    s_t = summarize_group(g_treat)
    s_c = summarize_group(g_ctrl)
    if not s_t or not s_c:
        return {}

    diff_inan = round(s_t["inanicion_pct"] - s_c["inanicion_pct"], 2)
    se_diff_inan = math.sqrt(s_t["inanicion_se_cluster_pct"] ** 2 + s_c["inanicion_se_cluster_pct"] ** 2)
    z_inan = diff_inan / max(1e-9, se_diff_inan)
    p_cl_inan = norm_two_sided_p(z_inan)
    p_fisher_inan = fisher_exact_two_sided(
        s_t["inanicion_k"], s_t["n"] - s_t["inanicion_k"],
        s_c["inanicion_k"], s_c["n"] - s_c["inanicion_k"]
    )

    diff_depr = round(s_t["depredacion_pct"] - s_c["depredacion_pct"], 2)
    se_diff_depr = math.sqrt(s_t["depredacion_se_cluster_pct"] ** 2 + s_c["depredacion_se_cluster_pct"] ** 2)
    z_depr = diff_depr / max(1e-9, se_diff_depr)
    p_cl_depr = norm_two_sided_p(z_depr)
    p_fisher_depr = fisher_exact_two_sided(
        s_t["depredacion_k"], s_t["n"] - s_t["depredacion_k"],
        s_c["depredacion_k"], s_c["n"] - s_c["depredacion_k"]
    )

    diff_sen = round(s_t["senescencia_pct"] - s_c["senescencia_pct"], 2)
    se_diff_sen = math.sqrt(s_t["senescencia_se_cluster_pct"] ** 2 + s_c["senescencia_se_cluster_pct"] ** 2)
    z_sen = diff_sen / max(1e-9, se_diff_sen)
    p_cl_sen = norm_two_sided_p(z_sen)
    p_fisher_sen = fisher_exact_two_sided(
        s_t["senescencia_k"], s_t["n"] - s_t["senescencia_k"],
        s_c["senescencia_k"], s_c["n"] - s_c["senescencia_k"]
    )

    return {
        "treated": s_t,
        "control": s_c,
        "contrasts": {
            "delta_feed_per_1k": round(s_t["feed_per_1k"] - s_c["feed_per_1k"], 2),
            "delta_exposure_ratio": round(s_t["exposure_ratio"] - s_c["exposure_ratio"], 4),
            "delta_age_cycles": round(s_t["mean_age"] - s_c["mean_age"], 1),
            "inanicion": {
                "delta_pp": diff_inan,
                "se_cluster_pp": round(se_diff_inan, 2),
                "IC95_pp": [round(diff_inan - 1.96 * se_diff_inan, 2), round(diff_inan + 1.96 * se_diff_inan, 2)],
                "z_cluster": round(z_inan, 2),
                "p_cluster": p_cl_inan,
                "p_fisher_exact": p_fisher_inan,
            },
            "depredacion": {
                "delta_pp": diff_depr,
                "se_cluster_pp": round(se_diff_depr, 2),
                "IC95_pp": [round(diff_depr - 1.96 * se_diff_depr, 2), round(diff_depr + 1.96 * se_diff_depr, 2)],
                "z_cluster": round(z_depr, 2),
                "p_cluster": p_cl_depr,
                "p_fisher_exact": p_fisher_depr,
            },
            "senescencia": {
                "delta_pp": diff_sen,
                "se_cluster_pp": round(se_diff_sen, 2),
                "IC95_pp": [round(diff_sen - 1.96 * se_diff_sen, 2), round(diff_sen + 1.96 * se_diff_sen, 2)],
                "z_cluster": round(z_sen, 2),
                "p_cluster": p_cl_sen,
                "p_fisher_exact": p_fisher_sen,
            },
        },
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    eng.ensure_sqlite_schema(cur)

    cur.execute("SELECT experiment_tag, seed, num_predators FROM simulation_runs WHERE experiment_tag LIKE 'CAUSAL_%'")
    existing_keys = {(r[0], int(r[1]), int(r[2])) for r in cur.fetchall()}

    tasks = build_task_list(existing_keys)
    print(f"Corridas causales ya en BD: {len(existing_keys)} | Corridas nuevas por ejecutar: {len(tasks)}")

    if tasks:
        t0 = time.time()
        n_workers = min(8, max(1, (os.cpu_count() or 4)))
        print(f"Ejecutando {len(tasks)} simulaciones en paralelo con {n_workers} procesos worker...")
        completed = 0
        with mp.Pool(processes=n_workers) as pool:
            for res in pool.imap_unordered(_worker_run_sim, tasks, chunksize=2):
                exp_tag, seed, cult_en, pant_en, k_pred, max_eng, state = res
                insert_run_into_db(cur, exp_tag, seed, cult_en, pant_en, k_pred, max_eng, state)
                completed += 1
                if completed % 30 == 0 or completed == len(tasks):
                    conn.commit()
                    el = time.time() - t0
                    rate = completed / max(0.1, el)
                    rem = (len(tasks) - completed) / max(0.01, rate)
                    print(f"  [{completed}/{len(tasks)}] guardadas en SQLite con todos sus engramas ({rate:.2f} sims/s, ETA: {rem:.0f}s)")

    # Cargar la totalidad de corridas CAUSAL_% desde ascendant_generacional_integro.db
    cur.execute("""
        SELECT
            sr.run_id, sr.experiment_tag, sr.seed, sr.condition, sr.num_predators,
            sr.cultural_enabled, sr.pantry_enabled,
            fm.agent_id, fm.gen_number, fm.age_at_death,
            fm.initial_max_lifespan, fm.final_max_lifespan,
            fm.outside_cycles, fm.cause_of_death, fm.temperament,
            fm.theta_temp_json, fm.epistemic_stats_json, fm.engrams_json
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag LIKE 'CAUSAL_%'
        ORDER BY sr.run_id, fm.gen_number
    """)
    all_rows = cur.fetchall()
    conn.close()

    all_agents = extract_agent_metrics(all_rows)
    total_engrams = sum(a["engrams_count"] for a in all_agents)
    print(f"Total agentes causales en BD: {len(all_agents)} ({len(all_agents)//4} corridas) | Total engramas persistidos: {total_engrams}")

    def filter_ag(exp_tag, offspring_only=True, temp_name=None, max_seed=None):
        return [
            a for a in all_agents
            if a["exp_tag"] == exp_tag
            and ((a["gen"] > 0) if offspring_only else True)
            and (temp_name is None or a["temperament"] == temp_name)
            and (max_seed is None or a["seed"] < max_seed)
        ]

    # 1. Experimento 1: Swap Quirúrgico de theta_oxi (en Descendientes Homogéneos ALFA/BETA/GAMA y en Total)
    mel_ctrl_off = filter_ag("CAUSAL_0_CONTROL", offspring_only=True, temp_name="Melancólico Empático")
    mel_swap_off = filter_ag("CAUSAL_1_SWAP_OXI", offspring_only=True, temp_name="Melancólico Empático")
    sto_ctrl_off = filter_ag("CAUSAL_0_CONTROL", offspring_only=True, temp_name="Estoico Desapegado")
    sto_swap_off = filter_ag("CAUSAL_1_SWAP_OXI", offspring_only=True, temp_name="Estoico Desapegado")

    mel_ctrl_all = filter_ag("CAUSAL_0_CONTROL", offspring_only=False, temp_name="Melancólico Empático")
    mel_swap_all = filter_ag("CAUSAL_1_SWAP_OXI", offspring_only=False, temp_name="Melancólico Empático")
    sto_ctrl_all = filter_ag("CAUSAL_0_CONTROL", offspring_only=False, temp_name="Estoico Desapegado")
    sto_swap_all = filter_ag("CAUSAL_1_SWAP_OXI", offspring_only=False, temp_name="Estoico Desapegado")

    exp1_swap = {
        "offspring_homogeneous_tau2000": {
            "melancolico_oxi_086_to_022": compare_two_groups(mel_swap_off, mel_ctrl_off),
            "estoico_oxi_022_to_086": compare_two_groups(sto_swap_off, sto_ctrl_off),
        },
        "all_agents_including_P0": {
            "melancolico_oxi_086_to_022": compare_two_groups(mel_swap_all, mel_ctrl_all),
            "estoico_oxi_022_to_086": compare_two_groups(sto_swap_all, sto_ctrl_all),
        },
    }

    # 2. Experimento 2: Ablación de Donación ALIMENTAR (por generación y en descendientes)
    exp2_ablation_feed = {
        "offspring_homogeneous_tau2000_all": compare_two_groups(
            filter_ag("CAUSAL_2_ABLACION_DONACION", offspring_only=True),
            filter_ag("CAUSAL_0_CONTROL", offspring_only=True)
        ),
        "melancolico_offspring": compare_two_groups(
            filter_ag("CAUSAL_2_ABLACION_DONACION", offspring_only=True, temp_name="Melancólico Empático"),
            filter_ag("CAUSAL_0_CONTROL", offspring_only=True, temp_name="Melancólico Empático")
        ),
        "by_generation": {
            f"gen_{g}": compare_two_groups(
                [a for a in all_agents if a["exp_tag"] == "CAUSAL_2_ABLACION_DONACION" and a["gen"] == g],
                [a for a in all_agents if a["exp_tag"] == "CAUSAL_0_CONTROL" and a["gen"] == g]
            )
            for g in (0, 1, 2, 3)
        },
    }

    # 3. Experimento 3: Ablación de Ira en Ec. 2.11
    exp3_ablation_ira = {
        "colerico_offspring_tau2000": compare_two_groups(
            filter_ag("CAUSAL_3_ABLACION_IRA", offspring_only=True, temp_name="Colérico Reactivo"),
            filter_ag("CAUSAL_0_CONTROL", offspring_only=True, temp_name="Colérico Reactivo")
        ),
        "all_offspring_tau2000": compare_two_groups(
            filter_ag("CAUSAL_3_ABLACION_IRA", offspring_only=True),
            filter_ag("CAUSAL_0_CONTROL", offspring_only=True)
        ),
    }

    # 4. Experimento 4: Diseño Factorial 2x2 de Mediación (Oxitocina x Donación) + Aislamiento de Vía Afiliativa
    # Solo sobre descendientes homogéneos (ALFA, BETA, GAMA, tau=2000, N=180 por celda)
    c_5a = filter_ag("CAUSAL_5A_OXI_BAJA_DON_ACTIVA", offspring_only=True)
    c_5b = filter_ag("CAUSAL_5B_OXI_ALTA_DON_ACTIVA", offspring_only=True)
    c_5c = filter_ag("CAUSAL_5C_OXI_BAJA_DON_INACTIVA", offspring_only=True)
    c_5d = filter_ag("CAUSAL_5D_OXI_ALTA_DON_INACTIVA", offspring_only=True)
    c_5e = filter_ag("CAUSAL_5E_OXI_ALTA_SOLO_ALIMENTAR", offspring_only=True)

    # Estimar modelo de interacción DiD 2x2 sobre (5A, 5B, 5C, 5D) con SE clusterizados por semilla
    cells_2x2 = c_5a + c_5b + c_5c + c_5d
    y_inan_2x2 = np.array([100.0 if a["cause"] == "INANICION" else 0.0 for a in cells_2x2])
    y_exp_2x2 = np.array([100.0 * a["outside_ratio"] for a in cells_2x2])
    y_feed_2x2 = np.array([a["feed_per_1k"] for a in cells_2x2])
    oxi_hi = np.array([1.0 if a["exp_tag"] in ("CAUSAL_5B_OXI_ALTA_DON_ACTIVA", "CAUSAL_5D_OXI_ALTA_DON_INACTIVA") else 0.0 for a in cells_2x2])
    don_on = np.array([1.0 if a["exp_tag"] in ("CAUSAL_5A_OXI_BAJA_DON_ACTIVA", "CAUSAL_5B_OXI_ALTA_DON_ACTIVA") else 0.0 for a in cells_2x2])
    inter_ox_don = oxi_hi * don_on
    X_2x2 = np.column_stack([
        np.ones(len(cells_2x2)),
        oxi_hi,
        don_on,
        inter_ox_don,
        np.array([float(a["k5"]) for a in cells_2x2]),
    ])
    seeds_2x2 = np.array([a["seed"] for a in cells_2x2])
    b_in2, se_in2, _ = fit_ols_clustered(y_inan_2x2, X_2x2, seeds_2x2)
    b_ex2, se_ex2, _ = fit_ols_clustered(y_exp_2x2, X_2x2, seeds_2x2)
    b_fd2, se_fd2, _ = fit_ols_clustered(y_feed_2x2, X_2x2, seeds_2x2)

    exp4_mediation_2x2 = {
        "cells_offspring_tau2000": {
            "5A_OXI_022_DON_ACTIVA": summarize_group(c_5a),
            "5B_OXI_086_DON_ACTIVA": summarize_group(c_5b),
            "5C_OXI_022_DON_INACTIVA": summarize_group(c_5c),
            "5D_OXI_086_DON_INACTIVA": summarize_group(c_5d),
            "5E_OXI_086_SOLO_VIA_ALIMENTAR_CLAMP_AFILIATIVA_022": summarize_group(c_5e),
        },
        "key_contrasts": {
            "efecto_total_oxi_con_donacion_activa_5B_vs_5A": compare_two_groups(c_5b, c_5a),
            "efecto_directo_residual_oxi_sin_donacion_5D_vs_5C": compare_two_groups(c_5d, c_5c),
            "efecto_puro_via_alimentar_5E_vs_5A": compare_two_groups(c_5e, c_5a),
            "efecto_via_afiliativa_secundaria_5B_vs_5E": compare_two_groups(c_5b, c_5e),
        },
        "interaction_model_DiD_clustered": {
            "inanicion_pp": {
                "beta_oxi_directo_sin_donacion": round(float(b_in2[1]), 2),
                "se_oxi_directo": round(float(se_in2[1]), 2),
                "p_oxi_directo": norm_two_sided_p(b_in2[1] / se_in2[1]),
                "beta_donacion_en_oxi_baja": round(float(b_in2[2]), 2),
                "se_donacion": round(float(se_in2[2]), 2),
                "beta_interaccion_oxi_x_donacion": round(float(b_in2[3]), 2),
                "se_interaccion": round(float(se_in2[3]), 2),
                "z_interaccion": round(float(b_in2[3] / se_in2[3]), 2),
                "p_interaccion": norm_two_sided_p(b_in2[3] / se_in2[3]),
            },
            "exposure_pp": {
                "beta_oxi_directo_sin_donacion": round(float(b_ex2[1]), 2),
                "se_oxi_directo": round(float(se_ex2[1]), 2),
                "p_oxi_directo": norm_two_sided_p(b_ex2[1] / se_ex2[1]),
                "beta_interaccion_oxi_x_donacion": round(float(b_ex2[3]), 2),
                "se_interaccion": round(float(se_ex2[3]), 2),
                "p_interaccion": norm_two_sided_p(b_ex2[3] / se_ex2[3]),
            },
            "feed_per_1k": {
                "beta_interaccion_oxi_x_donacion": round(float(b_fd2[3]), 2),
                "se_interaccion": round(float(se_fd2[3]), 2),
                "p_interaccion": norm_two_sided_p(b_fd2[3] / se_fd2[3]),
            },
        },
    }

    # 5. Experimento 5: Barrido Paramétrico Dosis-Respuesta de CAUSAL_FEED_OXI_GAIN in {0.0, 0.5, 1.0, 1.5, 2.0}
    # Semillas emparejadas 50000..50029 (60 corridas = 180 descendientes homogéneos por nivel)
    dose_arms = [
        ("GAIN_0.0_c0.0", "CAUSAL_2_ABLACION_DONACION", 0.0, 0.0),
        ("GAIN_0.5_c0.9", "CAUSAL_6A_DOSE_FEED_05",     0.5, 0.9),
        ("GAIN_1.0_c1.8", "CAUSAL_0_CONTROL",           1.0, 1.8),
        ("GAIN_1.5_c2.7", "CAUSAL_6B_DOSE_FEED_15",     1.5, 2.7),
        ("GAIN_2.0_c3.6", "CAUSAL_6C_DOSE_FEED_20",     2.0, 3.6),
    ]
    exp5_dose_response = {}
    for label, tag, gain_v, mult_v in dose_arms:
        sub_off = filter_ag(tag, offspring_only=True, max_seed=50030)
        sub_mel = filter_ag(tag, offspring_only=True, temp_name="Melancólico Empático", max_seed=50030)
        sub_p0 = [a for a in all_agents if a["exp_tag"] == tag and a["gen"] == 0 and a["seed"] < 50030]
        exp5_dose_response[label] = {
            "feed_oxi_gain": gain_v,
            "effective_multiplier_c_feed": mult_v,
            "offspring_tau2000": summarize_group(sub_off),
            "melancolico_offspring_tau2000": summarize_group(sub_mel),
            "progenitor_P0_tau800": summarize_group(sub_p0),
        }

    # 6. Experimento 6: Diseño Ortogonal 7D (Regresión multivariable con SE clusterizados por semilla y Holm-Bonferroni para 21 contrastes)
    orth_off = filter_ag("CAUSAL_4_ORTOGONAL_7D", offspring_only=True)
    orth_all = filter_ag("CAUSAL_4_ORTOGONAL_7D", offspring_only=False)

    def analyze_orthogonal_7d(ag_list):
        trait_keys = ["oxi", "dop", "ira", "tris", "res", "cur", "cort_base"]
        T_mat = np.array([[float(a["theta"].get(k, 0.5)) for k in trait_keys] for a in ag_list], dtype=np.float64)
        T_std = (T_mat - np.mean(T_mat, axis=0)) / np.std(T_mat, axis=0)
        seeds_o = np.array([a["seed"] for a in ag_list], dtype=np.int64)

        covs = [np.ones(len(ag_list)), T_std, np.array([float(a["k5"]) for a in ag_list])]
        if any(a["gen"] == 0 for a in ag_list):
            covs.append(np.array([1.0 if a["gen"] == 0 else 0.0 for a in ag_list]))
        X_o = np.column_stack(covs)

        y_feed = np.array([a["feed_per_1k"] for a in ag_list], dtype=np.float64)
        y_exp = np.array([a["outside_ratio"] * 100.0 for a in ag_list], dtype=np.float64)
        y_inan = np.array([1.0 if a["cause"] == "INANICION" else 0.0 for a in ag_list], dtype=np.float64)
        y_depr = np.array([1.0 if a["cause"] == "DEPREDADOR" else 0.0 for a in ag_list], dtype=np.float64)

        b_feed, se_feed, _ = fit_ols_clustered(y_feed, X_o, seeds_o)
        b_exp, se_exp, _ = fit_ols_clustered(y_exp, X_o, seeds_o)
        b_inan_lpm, se_inan_lpm, _ = fit_ols_clustered(y_inan * 100.0, X_o, seeds_o)
        b_depr_lpm, se_depr_lpm, _ = fit_ols_clustered(y_depr * 100.0, X_o, seeds_o)
        b_inan_log, se_inan_log, _ = fit_logit_clustered(y_inan, X_o, seeds_o)
        b_depr_log, se_depr_log, _ = fit_logit_clustered(y_depr, X_o, seeds_o)

        # Corrección de Holm-Bonferroni sobre los 21 contrastes principales (7 rasgos x 3 desenlaces: Donación, Exposición, Inanición)
        raw_p_21 = []
        for idx_k in range(7):
            j = 1 + idx_k
            raw_p_21.append(norm_two_sided_p(b_feed[j] / se_feed[j]))
            raw_p_21.append(norm_two_sided_p(b_exp[j] / se_exp[j]))
            raw_p_21.append(norm_two_sided_p(b_inan_log[j] / se_inan_log[j]))
        holm_p_21 = holm_bonferroni(raw_p_21)

        # También corrección por familia de 7 rasgos en cada desenlace
        p_feed_7 = holm_bonferroni([norm_two_sided_p(b_feed[1 + i] / se_feed[1 + i]) for i in range(7)])
        p_exp_7 = holm_bonferroni([norm_two_sided_p(b_exp[1 + i] / se_exp[1 + i]) for i in range(7)])
        p_inan_7 = holm_bonferroni([norm_two_sided_p(b_inan_log[1 + i] / se_inan_log[1 + i]) for i in range(7)])
        p_depr_7 = holm_bonferroni([norm_two_sided_p(b_depr_log[1 + i] / se_depr_log[1 + i]) for i in range(7)])

        traits_out = {}
        for idx_k, k_name in enumerate(trait_keys):
            j = 1 + idx_k
            b_f, s_f = float(b_feed[j]), float(se_feed[j])
            b_e, s_e = float(b_exp[j]), float(se_exp[j])
            b_il, s_il = float(b_inan_lpm[j]), float(se_inan_lpm[j])
            b_ig, s_ig = float(b_inan_log[j]), float(se_inan_log[j])
            b_dg, s_dg = float(b_depr_log[j]), float(se_depr_log[j])

            traits_out[k_name] = {
                "feed_per_1k": {
                    "beta_SD": round(b_f, 3),
                    "se_cluster": round(s_f, 3),
                    "IC95": [round(b_f - 1.96 * s_f, 3), round(b_f + 1.96 * s_f, 3)],
                    "z_cluster": round(b_f / s_f, 2),
                    "p_raw": norm_two_sided_p(b_f / s_f),
                    "p_holm_7traits": round(p_feed_7[idx_k], 6),
                    "p_holm_21contrasts": round(holm_p_21[idx_k * 3 + 0], 6),
                },
                "exposure_pp": {
                    "beta_SD": round(b_e, 3),
                    "se_cluster": round(s_e, 3),
                    "IC95": [round(b_e - 1.96 * s_e, 3), round(b_e + 1.96 * s_e, 3)],
                    "z_cluster": round(b_e / s_e, 2),
                    "p_raw": norm_two_sided_p(b_e / s_e),
                    "p_holm_7traits": round(p_exp_7[idx_k], 6),
                    "p_holm_21contrasts": round(holm_p_21[idx_k * 3 + 1], 6),
                },
                "inanicion": {
                    "delta_pp_per_SD": round(b_il, 2),
                    "se_pp_cluster": round(s_il, 2),
                    "IC95_pp": [round(b_il - 1.96 * s_il, 2), round(b_il + 1.96 * s_il, 2)],
                    "logit_beta_SD": round(b_ig, 3),
                    "logit_se_cluster": round(s_ig, 3),
                    "OR_per_SD": round(math.exp(b_ig), 3),
                    "IC95_OR": [round(math.exp(b_ig - 1.96 * s_ig), 3), round(math.exp(b_ig + 1.96 * s_ig), 3)],
                    "z_cluster": round(b_ig / s_ig, 2),
                    "p_raw": norm_two_sided_p(b_ig / s_ig),
                    "p_holm_7traits": round(p_inan_7[idx_k], 6),
                    "p_holm_21contrasts": round(holm_p_21[idx_k * 3 + 2], 6),
                },
                "depredacion": {
                    "logit_beta_SD": round(b_dg, 3),
                    "logit_se_cluster": round(s_dg, 3),
                    "OR_per_SD": round(math.exp(b_dg), 3),
                    "IC95_OR": [round(math.exp(b_dg - 1.96 * s_dg), 3), round(math.exp(b_dg + 1.96 * s_dg), 3)],
                    "z_cluster": round(b_dg / s_dg, 2),
                    "p_raw": norm_two_sided_p(b_dg / s_dg),
                    "p_holm_7traits": round(p_depr_7[idx_k], 6),
                },
            }

        corr_mat = np.corrcoef(T_mat, rowvar=False)
        max_off_diag = float(np.max(np.abs(corr_mat - np.eye(7))))
        return {
            "n_agents": len(ag_list),
            "G_seeds": int(len(np.unique(seeds_o))),
            "max_abs_trait_correlation": round(max_off_diag, 4),
            "traits": traits_out,
        }

    exp6_orthogonal = {
        "offspring_homogeneous_tau2000": analyze_orthogonal_7d(orth_off),
        "all_agents_including_P0": analyze_orthogonal_7d(orth_all),
    }

    payload = {
        "metadata": {
            "author": "David San Nicolás Montero",
            "orcid": "0009-0000-9977-007X",
            "total_causal_runs_in_db": len(all_agents) // 4,
            "total_causal_agents_in_db": len(all_agents),
            "total_causal_engrams_in_db": total_engrams,
        },
        "exp1_swap_oxi_mel_stoic": exp1_swap,
        "exp2_ablation_donation_alimentar": exp2_ablation_feed,
        "exp3_ablation_ira_ec211": exp3_ablation_ira,
        "exp4_factorial_2x2_mediation_and_pathway_isolation": exp4_mediation_2x2,
        "exp5_parametric_dose_response_feed_gain": exp5_dose_response,
        "exp6_orthogonal_7d_multivariable_holm": exp6_orthogonal,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✅ Análisis causal ampliado exportado en: {OUT_JSON}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
