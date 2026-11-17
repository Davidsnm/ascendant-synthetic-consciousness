#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates 3 high-resolution (300 DPI, 2x supersampled LANCZOS anti-aliased) publication figures
for the Project Ascendant v4.0 Master Paper using Pillow (PIL) directly from the canonical SQLite
database and verified JSON outputs.
"""

import json
import os
import sqlite3
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DB_PATH = r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant\experimeto generacional corregido\ascendant_generacional_integro.db"
COX_JSON = r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant\experimeto generacional corregido\analisis_cox_cif_intraarquetipo_y_sensibilidad.json"
OUT_DIR = r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant\experimeto generacional corregido\figuras_paper_v4"

os.makedirs(OUT_DIR, exist_ok=True)


def get_font(size, bold=False):
    candidates = (
        [r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\calibrib.ttf"]
        if bold
        else [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\calibri.ttf"]
    )
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_dashed_line(draw, p1, p2, fill, width=3, dash_len=14, gap_len=9):
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    dist = float(np.hypot(dx, dy))
    if dist < 1e-3:
        return
    ux, uy = dx / dist, dy / dist
    pos = 0.0
    while pos < dist:
        end = min(dist, pos + dash_len)
        draw.line(
            [(x1 + ux * pos, y1 + uy * pos), (x1 + ux * end, y1 + uy * end)],
            fill=fill,
            width=width,
        )
        pos += dash_len + gap_len


def make_fig1_cif():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("""
        SELECT fm.age_at_death, fm.cause_of_death, fm.temperament
        FROM final_memories fm
        JOIN simulation_runs sr ON fm.run_id = sr.run_id
        WHERE sr.experiment_tag IN ('K3_M100','K3_M140','K3_M200','K5_M100','K5_M140','K5_M200')
          AND fm.gen_number > 0
    """)
    rows = cur.fetchall()
    conn.close()

    ages = np.array([max(1, int(r[0])) for r in rows], dtype=np.int64)
    causes = np.array([1 if r[1] == "INANICION" else (2 if r[1] == "DEPREDADOR" else 0) for r in rows], dtype=np.int64)
    archs = np.array([r[2] for r in rows])

    arch_specs = [
        ("Melancólico Empático", "Melancholic (theta_oxi=0.86) [13.80% | 19.67%]", (197, 48, 48), "solid", 6),
        ("Optimista Sereno", "Optimistic (theta_oxi=0.74) [11.87% | 17.57%]", (221, 107, 32), "dash", 5),
        ("Entusiasta Dopaminérgico", "Enthusiastic (theta_oxi=0.60) [10.61% | 17.57%]", (214, 158, 46), "solid", 4),
        ("Colérico Reactivo", "Choleric (theta_oxi=0.40) [10.95% | 16.25%]", (49, 130, 206), "dash", 4),
        ("Estoico Desapegado", "Stoic Baseline (theta_oxi=0.22) [11.19% | 15.19%]", (26, 54, 93), "solid", 6),
    ]

    cif_curves = {}
    for arch, _, _, _, _ in arch_specs:
        m = (archs == arch)
        a_sub = ages[m]
        c_sub = causes[m]
        S_prev = 1.0
        cif1 = np.zeros(2001)
        cif2 = np.zeros(2001)
        for t in range(1, 2001):
            n_risk = int(np.sum(a_sub >= t))
            cif1[t] = cif1[t - 1]
            cif2[t] = cif2[t - 1]
            if n_risk > 0:
                d1 = int(np.sum((a_sub == t) & (c_sub == 1)))
                d2 = int(np.sum((a_sub == t) & (c_sub == 2)))
                d0 = int(np.sum((a_sub == t) & (c_sub == 0)))
                cif1[t] += S_prev * (d1 / float(n_risk))
                cif2[t] += S_prev * (d2 / float(n_risk))
                S_prev = S_prev * (1.0 - (d0 + d1 + d2) / float(n_risk))
        cif_curves[arch] = (cif1 * 100.0, cif2 * 100.0)

    # Render at 2x resolution (4400 x 1650) then downsample to (2200 x 825)
    W, H = 4400, 1650
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(44, bold=True)
    f_axis = get_font(36, bold=True)
    f_tick = get_font(32, bold=False)
    f_leg = get_font(29, bold=False)
    f_box = get_font(30, bold=True)

    panels = [
        {
            "x0": 230, "y0": 140, "x1": 2060, "y1": 1320,
            "title": "A. Cumulative Incidence of Starvation CIF_inan(t) [3,033 Events]",
            "ymax": 15.0, "yticks": [0, 3, 6, 9, 12, 15],
            "idx": 0,
            "box_txt": [
                "Melancholic vs. Stoic Baseline:",
                "CSHR = 1.3058 [95% CI: 1.1428, 1.4921]",
                "z_cl = +3.921, p_Holm = 0.000352",
                "CIF(2000): 13.80% vs. 11.19% (+2.61 pp)"
            ],
            "box_bg": (255, 245, 245), "box_bd": (254, 178, 178)
        },
        {
            "x0": 2430, "y0": 140, "x1": 4260, "y1": 1320,
            "title": "B. Cumulative Incidence of Acute Predation CIF_depr(t) [4,488 Events]",
            "ymax": 21.0, "yticks": [0, 3, 6, 9, 12, 15, 18, 21],
            "idx": 1,
            "box_txt": [
                "Melancholic vs. Stoic Baseline:",
                "CSHR = 1.4908 [95% CI: 1.3388, 1.6602]",
                "z_cl = +7.276, p_Holm = 1.38e-12",
                "CIF(2000): 19.67% vs. 15.19% (+4.48 pp)"
            ],
            "box_bg": (235, 248, 255), "box_bd": (144, 205, 244)
        },
    ]

    for p in panels:
        x0, y0, x1, y1 = p["x0"], p["y0"], p["x1"], p["y1"]
        ymax = p["ymax"]
        draw.text((x0, y0 - 75), p["title"], fill=(26, 54, 93), font=f_title)

        # Grid and Y ticks
        for yt in p["yticks"]:
            yy = y1 - (yt / ymax) * (y1 - y0)
            draw.line([(x0, yy), (x1, yy)], fill=(226, 232, 240), width=2)
            lbl = f"{yt}%"
            bbox = draw.textbbox((0, 0), lbl, font=f_tick)
            draw.text((x0 - (bbox[2] - bbox[0]) - 18, yy - (bbox[3] - bbox[1]) / 2), lbl, fill=(74, 85, 104), font=f_tick)

        # X ticks
        for xt in [0, 400, 800, 1200, 1600, 2000]:
            xx = x0 + (xt / 2000.0) * (x1 - x0)
            draw.line([(xx, y0), (xx, y1)], fill=(226, 232, 240), width=2)
            draw.line([(xx, y1), (xx, y1 + 12)], fill=(45, 55, 72), width=3)
            lbl = str(xt)
            bbox = draw.textbbox((0, 0), lbl, font=f_tick)
            draw.text((xx - (bbox[2] - bbox[0]) / 2, y1 + 20), lbl, fill=(74, 85, 104), font=f_tick)

        # Border
        draw.rectangle([x0, y0, x1, y1], outline=(74, 85, 104), width=4)

        # Plot CIF curves (stepped every 10 cycles for smooth rendering)
        t_steps = list(range(0, 2001, 10))
        for arch, lbl, col, style, lw in arch_specs:
            vals = cif_curves[arch][p["idx"]]
            pts = []
            for t in t_steps:
                xx = x0 + (t / 2000.0) * (x1 - x0)
                yy = y1 - (vals[t] / ymax) * (y1 - y0)
                pts.append((xx, yy))
            if style == "solid":
                draw.line(pts, fill=col, width=lw, joint="curve")
            else:
                for i in range(len(pts) - 1):
                    draw_dashed_line(draw, pts[i], pts[i + 1], fill=col, width=lw, dash_len=16, gap_len=10)

        # Annotation Box (bottom-right of each panel)
        bx0, by0, bx1, by1 = x1 - 760, y1 - 245, x1 - 30, y1 - 25
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=p["box_bg"], outline=p["box_bd"], width=3)
        for idx_l, line_t in enumerate(p["box_txt"]):
            draw.text((bx0 + 24, by0 + 18 + idx_l * 48), line_t, fill=(26, 54, 93), font=f_box)

        # Axis label X
        xlbl = "Age in Cycles t (Homogeneous Offspring Cohort, N = 25,920, tau_0 = 2,000)"
        bbox = draw.textbbox((0, 0), xlbl, font=f_axis)
        draw.text(((x0 + x1) / 2 - (bbox[2] - bbox[0]) / 2, y1 + 78), xlbl, fill=(26, 54, 93), font=f_axis)

    # Legend in Panel A top-left
    lx0, ly0, lx1, ly1 = 260, 170, 1180, 455
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=14, fill=(255, 255, 255), outline=(203, 213, 224), width=3)
    for i, (arch, lbl, col, style, lw) in enumerate(arch_specs):
        yy = ly0 + 32 + i * 52
        if style == "solid":
            draw.line([(lx0 + 24, yy), (lx0 + 104, yy)], fill=col, width=lw)
        else:
            draw_dashed_line(draw, (lx0 + 24, yy), (lx0 + 104, yy), fill=col, width=lw, dash_len=14, gap_len=8)
        draw.text((lx0 + 122, yy - 18), lbl, fill=(45, 55, 72), font=f_leg)

    out_img = img.resize((2200, 825), Image.Resampling.LANCZOS)
    p1 = os.path.join(OUT_DIR, "fig1_cif_aalen_johansen.png")
    out_img.save(p1, dpi=(300, 300))
    print("Saved:", p1)


def make_fig2_cox_and_bite_wear():
    with open(COX_JSON, "r", encoding="utf-8") as f:
        cox_data = json.load(f)

    W, H = 4400, 1650
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(44, bold=True)
    f_axis = get_font(35, bold=True)
    f_tick = get_font(31, bold=False)
    f_tick_b = get_font(32, bold=True)
    f_leg = get_font(29, bold=False)
    f_val = get_font(29, bold=True)

    # Panel A: Forest plot of Cause-Specific Hazard Ratios
    x0, y0, x1, y1 = 440, 140, 2120, 1320
    draw.text((x0 - 200, y0 - 75), "A. Cause-Specific Cox Hazard Ratios (CSHR, 95% Cluster CI)", fill=(26, 54, 93), font=f_title)

    xmin, xmax = 0.75, 1.75
    for xt in [0.8, 1.0, 1.2, 1.4, 1.6]:
        xx = x0 + ((xt - xmin) / (xmax - xmin)) * (x1 - x0)
        col_g = (113, 128, 150) if abs(xt - 1.0) < 1e-6 else (226, 232, 240)
        w_g = 4 if abs(xt - 1.0) < 1e-6 else 2
        if abs(xt - 1.0) < 1e-6:
            draw_dashed_line(draw, (xx, y0), (xx, y1), fill=col_g, width=w_g, dash_len=16, gap_len=10)
        else:
            draw.line([(xx, y0), (xx, y1)], fill=col_g, width=w_g)
        lbl = f"{xt:.1f}"
        bbox = draw.textbbox((0, 0), lbl, font=f_tick)
        draw.text((xx - (bbox[2] - bbox[0]) / 2, y1 + 20), lbl, fill=(74, 85, 104), font=f_tick)

    draw.rectangle([x0, y0, x1, y1], outline=(74, 85, 104), width=4)

    archs = [
        ("Melancólico vs Estoico", "Melancholic\nvs. Stoic"),
        ("Optimista vs Estoico", "Optimistic\nvs. Stoic"),
        ("Entusiasta vs Estoico", "Enthusiastic\nvs. Stoic"),
        ("Colérico vs Estoico", "Choleric\nvs. Stoic"),
    ]
    causes_cfg = [
        (-55, "INANICION", "Starvation (3,033 events)", (197, 48, 48)),
        (0, "DEPREDADOR", "Acute Predation (4,488 events)", (43, 108, 176)),
        (+55, "SENESCENCIA_NATURAL", "Wear-Truncated Ceiling (18,399)", (47, 133, 90)),
    ]

    for i, (k_arch, lbl_arch) in enumerate(archs):
        yy_base = y0 + 170 + i * 275
        if i > 0:
            draw.line([(x0, yy_base - 137), (x1, yy_base - 137)], fill=(237, 242, 247), width=2)
        for idx_l, line_a in enumerate(lbl_arch.split("\n")):
            draw.text((x0 - 255, yy_base - 32 + idx_l * 38), line_a, fill=(26, 54, 93), font=f_tick_b)

        for y_off, c_key, c_lbl, col in causes_cfg:
            c_info = cox_data["cox_breslow_cause_specific_clustered"][c_key]["coefficients"][k_arch]
            hr = c_info["CSHR"]
            lo, hi = c_info["IC95_CSHR"]
            yy = yy_base + y_off
            xx_hr = x0 + ((hr - xmin) / (xmax - xmin)) * (x1 - x0)
            xx_lo = x0 + ((lo - xmin) / (xmax - xmin)) * (x1 - x0)
            xx_hi = x0 + ((hi - xmin) / (xmax - xmin)) * (x1 - x0)
            draw.line([(xx_lo, yy), (xx_hi, yy)], fill=col, width=5)
            draw.line([(xx_lo, yy - 12), (xx_lo, yy + 12)], fill=col, width=4)
            draw.line([(xx_hi, yy - 12), (xx_hi, yy + 12)], fill=col, width=4)
            draw.ellipse([xx_hr - 11, yy - 11, xx_hr + 11, yy + 11], fill=col, outline=(255, 255, 255), width=2)
            draw.text((xx_hi + 14, yy - 16), f"{hr:.2f}", fill=col, font=f_val)

    # Legend in Panel A bottom-right
    lx0, ly0, lx1, ly1 = x1 - 630, y1 - 215, x1 - 25, y1 - 20
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=14, fill=(255, 255, 255), outline=(203, 213, 224), width=3)
    for idx_c, (_, _, c_lbl, col) in enumerate(causes_cfg):
        yy = ly0 + 35 + idx_c * 55
        draw.line([(lx0 + 22, yy), (lx0 + 82, yy)], fill=col, width=5)
        draw.ellipse([lx0 + 42, yy - 10, lx0 + 62, yy + 10], fill=col)
        draw.text((lx0 + 100, yy - 18), c_lbl, fill=(45, 55, 72), font=f_leg)

    xlbl_a = "Cause-Specific Hazard Ratio CSHR (Lin-Wei Seed-Clustered 95% CI, G = 360)"
    bbox = draw.textbbox((0, 0), xlbl_a, font=f_axis)
    draw.text(((x0 + x1) / 2 - (bbox[2] - bbox[0]) / 2, y1 + 78), xlbl_a, fill=(26, 54, 93), font=f_axis)

    # Panel B: Somatic Bite-Wear Sensitivity Grid
    bx0, by0, bx1, by1 = 2470, 140, 4260, 1320
    draw.text((bx0, by0 - 75), "B. Somatic Bite-Wear Sensitivity Grid (Melancholic vs. Stoic)", fill=(26, 54, 93), font=f_title)

    ymin_b, ymax_b = 0.0, 13.5
    for yt in [0, 1, 2, 4, 6, 8, 10, 12]:
        yy = by1 - (yt / ymax_b) * (by1 - by0)
        if yt == 1:
            draw_dashed_line(draw, (bx0, yy), (bx1, yy), fill=(113, 128, 150), width=4, dash_len=16, gap_len=10)
        else:
            draw.line([(bx0, yy), (bx1, yy)], fill=(226, 232, 240), width=2)
        lbl = f"{yt}x"
        bbox = draw.textbbox((0, 0), lbl, font=f_tick)
        draw.text((bx0 - (bbox[2] - bbox[0]) - 18, yy - (bbox[3] - bbox[1]) / 2), lbl, fill=(74, 85, 104), font=f_tick)

    draw.rectangle([bx0, by0, bx1, by1], outline=(74, 85, 104), width=4)

    grid_keys = [
        ("umbral_1_mordiscos_8_ciclos", ">=1 bite (-8c)\n[18,379 ev]"),
        ("umbral_5_mordiscos_40_ciclos", ">=5 bites (-40c)\n[16,568 ev]"),
        ("umbral_10_mordiscos_80_ciclos", ">=10 bites (-80c)\n[8,396 ev]"),
        ("umbral_15_mordiscos_120_ciclos", ">=15 bites (-120c)\n[1,960 ev]"),
        ("umbral_20_mordiscos_160_ciclos", ">=20 bites (-160c)\n[231 ev]"),
    ]
    pts_b = []
    for idx_g, (gk, glbl) in enumerate(grid_keys):
        xx = bx0 + 180 + idx_g * 355
        g_info = cox_data["bite_wear_sensitivity_grid"][gk]
        hr = g_info["melancolico_vs_estoico_CSHR_desgaste"]
        lo, hi = g_info["melancolico_vs_estoico_IC95"]
        yy_hr = by1 - (hr / ymax_b) * (by1 - by0)
        yy_lo = by1 - (lo / ymax_b) * (by1 - by0)
        yy_hi = by1 - (hi / ymax_b) * (by1 - by0)
        pts_b.append((xx, yy_hr, hr, lo, hi, yy_hi))

        draw.line([(xx, yy_lo), (xx, yy_hi)], fill=(155, 44, 44), width=5)
        draw.line([(xx - 16, yy_lo), (xx + 16, yy_lo)], fill=(155, 44, 44), width=4)
        draw.line([(xx - 16, yy_hi), (xx + 16, yy_hi)], fill=(155, 44, 44), width=4)

        for il, l_str in enumerate(glbl.split("\n")):
            bbox = draw.textbbox((0, 0), l_str, font=f_tick)
            draw.text((xx - (bbox[2] - bbox[0]) / 2, by1 + 16 + il * 36), l_str, fill=(45, 55, 72), font=f_tick)

    for i in range(len(pts_b) - 1):
        draw.line([(pts_b[i][0], pts_b[i][1]), (pts_b[i + 1][0], pts_b[i + 1][1])], fill=(197, 48, 48), width=6)

    for idx_p, (xx, yy_hr, hr, lo, hi, yy_hi) in enumerate(pts_b):
        draw.ellipse([xx - 13, yy_hr - 13, xx + 13, yy_hr + 13], fill=(197, 48, 48), outline=(255, 255, 255), width=3)
        txt_v = f"{hr:.2f}x"
        bbox = draw.textbbox((0, 0), txt_v, font=f_tick_b)
        if idx_p < 3:
            draw.text((xx - (bbox[2] - bbox[0]) / 2, yy_hi - 46), txt_v, fill=(155, 44, 44), font=f_tick_b)
        else:
            draw.text((xx + 22, yy_hr - 22), txt_v, fill=(155, 44, 44), font=f_tick_b)

    xlbl_b = "Cumulative Non-Lethal Bite-Wear Threshold (Delta tau = -8 cycles/bite)"
    bbox = draw.textbbox((0, 0), xlbl_b, font=f_axis)
    draw.text(((bx0 + bx1) / 2 - (bbox[2] - bbox[0]) / 2, by1 + 96), xlbl_b, fill=(26, 54, 93), font=f_axis)

    out_img = img.resize((2200, 825), Image.Resampling.LANCZOS)
    p2 = os.path.join(OUT_DIR, "fig2_cox_and_bite_wear.png")
    out_img.save(p2, dpi=(300, 300))
    print("Saved:", p2)


def make_fig3_causal_interventions():
    W, H = 4400, 1650
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    f_title = get_font(44, bold=True)
    f_axis = get_font(35, bold=True)
    f_tick = get_font(30, bold=False)
    f_tick_b = get_font(31, bold=True)
    f_leg = get_font(28, bold=False)
    f_val = get_font(27, bold=True)

    # Panel A: Factorial Pathway Isolation (CAUSAL_5A-5E, N=900 offspring across G=30 seeds)
    x0, y0, x1, y1 = 220, 140, 2100, 1320
    draw.text((x0, y0 - 75), "A. Factorial Pathway Isolation (CAUSAL_5A-5E, N = 900 Offspring)", fill=(26, 54, 93), font=f_title)

    ymax_a = 35.0
    for yt in [0, 5, 10, 15, 20, 25, 30, 35]:
        yy = y1 - (yt / ymax_a) * (y1 - y0)
        draw.line([(x0, yy), (x1, yy)], fill=(226, 232, 240), width=2)
        lbl = f"{yt}%"
        bbox = draw.textbbox((0, 0), lbl, font=f_tick)
        draw.text((x0 - (bbox[2] - bbox[0]) - 16, yy - (bbox[3] - bbox[1]) / 2), lbl, fill=(74, 85, 104), font=f_tick)

    draw.rectangle([x0, y0, x1, y1], outline=(74, 85, 104), width=4)

    arms = [
        ("5C: Oxi 0.22\nNo Feed", 18.30, 14.44, 14.44),
        ("5D: Oxi 0.86\nNo Feed", 19.74, 15.00, 21.67),
        ("5A: Oxi 0.22\nFeed ON", 20.75, 16.67, 10.00),
        ("5E: Oxi 0.86\nFeed Only", 23.91, 11.67, 18.89),
        ("5B: Oxi 0.86\nFull Synergy", 26.36, 20.00, 13.33),
    ]
    bar_cols = [
        ("Outside Exposure (%)", (43, 108, 176)),
        ("Starvation (%)", (197, 48, 48)),
        ("Acute Predation (%)", (214, 158, 46)),
    ]

    bw = 82
    for idx_a, (albl, v_exp, v_in, v_dp) in enumerate(arms):
        cx = x0 + 205 + idx_a * 365
        for j, (val, (_, col)) in enumerate(zip([v_exp, v_in, v_dp], bar_cols)):
            bx_l = cx + (j - 1.5) * bw + 6
            bx_r = bx_l + bw - 8
            by_t = y1 - (val / ymax_a) * (y1 - y0)
            draw.rectangle([bx_l, by_t, bx_r, y1], fill=col, outline=(255, 255, 255), width=2)
            v_str = f"{val:.1f}"
            bbox = draw.textbbox((0, 0), v_str, font=f_val)
            draw.text(((bx_l + bx_r) / 2 - (bbox[2] - bbox[0]) / 2, by_t - 34), v_str, fill=col, font=f_val)

        for il, l_s in enumerate(albl.split("\n")):
            bbox = draw.textbbox((0, 0), l_s, font=f_tick_b)
            draw.text((cx - (bbox[2] - bbox[0]) / 2, y1 + 16 + il * 36), l_s, fill=(26, 54, 93), font=f_tick_b)

    # Legend in Panel A top-left
    lx0, ly0, lx1, ly1 = x0 + 30, y0 + 25, x0 + 620, y0 + 210
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=14, fill=(255, 255, 255), outline=(203, 213, 224), width=3)
    for idx_b, (blbl, col) in enumerate(bar_cols):
        yy = ly0 + 28 + idx_b * 54
        draw.rectangle([lx0 + 24, yy - 12, lx0 + 70, yy + 18], fill=col)
        draw.text((lx0 + 88, yy - 16), blbl, fill=(45, 55, 72), font=f_leg)

    # DiD Box in Panel A top-right
    dx0, dy0, dx1, dy1 = x1 - 780, y0 + 25, x1 - 25, y0 + 175
    draw.rounded_rectangle([dx0, dy0, dx1, dy1], radius=14, fill=(235, 248, 255), outline=(144, 205, 244), width=3)
    draw.text((dx0 + 20, dy0 + 18), "2x2 DiD ALIMENTAR Mediation Share:", fill=(26, 54, 93), font=f_tick_b)
    draw.text((dx0 + 20, dy0 + 62), "+4.17 / +5.61 pp = 74.3% (p = 5.29e-9)", fill=(197, 48, 48), font=f_tick_b)
    draw.text((dx0 + 20, dy0 + 106), "Cluster-Boot 95% CI: [51.3%, 103.1%] (SE=13.0%)", fill=(45, 55, 72), font=f_leg)

    xlbl_a = "Experimental Arm (G = 30 Matched Lineage Seeds x 2 Regimes = 180 Offspring/Arm)"
    bbox = draw.textbbox((0, 0), xlbl_a, font=f_axis)
    draw.text(((x0 + x1) / 2 - (bbox[2] - bbox[0]) / 2, y1 + 96), xlbl_a, fill=(26, 54, 93), font=f_axis)

    # Panel B: 7D Continuous Orthogonal Trait Sampling (CAUSAL_4_ORTOGONAL_7D, N=450 offspring, G=75 seeds)
    bx0, by0, bx1, by1 = 2540, 140, 4260, 1320
    draw.text((bx0 - 140, by0 - 75), "B. 7D Orthogonal Trait Sampling (N = 450, G = 75 Seeds)", fill=(26, 54, 93), font=f_title)

    xmin_b, xmax_b = -1.6, 3.0
    for xt in [-1.0, 0.0, 1.0, 2.0, 3.0]:
        xx = bx0 + ((xt - xmin_b) / (xmax_b - xmin_b)) * (bx1 - bx0)
        if abs(xt) < 1e-6:
            draw_dashed_line(draw, (xx, by0), (xx, by1), fill=(113, 128, 150), width=4, dash_len=16, gap_len=10)
        else:
            draw.line([(xx, by0), (xx, by1)], fill=(226, 232, 240), width=2)
        lbl = f"{xt:+.1f}" if xt != 0 else "0.0"
        bbox = draw.textbbox((0, 0), lbl, font=f_tick)
        draw.text((xx - (bbox[2] - bbox[0]) / 2, by1 + 20), lbl, fill=(74, 85, 104), font=f_tick)

    draw.rectangle([bx0, by0, bx1, by1], outline=(74, 85, 104), width=4)

    traits = [
        ("Oxytocin (theta_oxi)", 1.973, 0.385, 1.430, 0.245),
        ("Dopamine (theta_dop)", 0.967, 0.353, 0.332, 0.266),
        ("Curiosity (theta_cur)", 0.083, 0.352, 0.433, 0.276),
        ("Sadness (theta_tris)", 0.063, 0.362, -0.204, 0.246),
        ("Anger (theta_ira)", 0.038, 0.381, -0.385, 0.280),
        ("Base Cortisol", -0.240, 0.398, 0.077, 0.300),
        ("Resilience (theta_res)", -0.642, 0.413, -0.150, 0.255),
    ]

    for i, (tlbl, b_exp, s_exp, b_fd, s_fd) in enumerate(traits):
        yy_base = by0 + 95 + i * 162
        if i > 0:
            draw.line([(bx0, yy_base - 81), (bx1, yy_base - 81)], fill=(237, 242, 247), width=2)
        bbox = draw.textbbox((0, 0), tlbl, font=f_tick_b)
        draw.text((bx0 - (bbox[2] - bbox[0]) - 18, yy_base - 18), tlbl, fill=(26, 54, 93), font=f_tick_b)

        for y_off, b_v, s_v, col in [(-24, b_exp, s_exp, (43, 108, 176)), (+24, b_fd, s_fd, (197, 48, 48))]:
            yy = yy_base + y_off
            lo, hi = b_v - 1.96 * s_v, b_v + 1.96 * s_v
            xx_m = bx0 + ((b_v - xmin_b) / (xmax_b - xmin_b)) * (bx1 - bx0)
            xx_l = bx0 + ((lo - xmin_b) / (xmax_b - xmin_b)) * (bx1 - bx0)
            xx_h = bx0 + ((hi - xmin_b) / (xmax_b - xmin_b)) * (bx1 - bx0)
            draw.line([(xx_l, yy), (xx_h, yy)], fill=col, width=5)
            draw.line([(xx_l, yy - 10), (xx_l, yy + 10)], fill=col, width=4)
            draw.line([(xx_h, yy - 10), (xx_h, yy + 10)], fill=col, width=4)
            draw.ellipse([xx_m - 10, yy - 10, xx_m + 10, yy + 10], fill=col, outline=(255, 255, 255), width=2)
            if i == 0:
                draw.text((xx_h + 12, yy - 16), f"+{b_v:.2f}***", fill=col, font=f_val)

    lx0, ly0, lx1, ly1 = bx1 - 690, by1 - 155, bx1 - 25, by1 - 20
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=14, fill=(255, 255, 255), outline=(203, 213, 224), width=3)
    for idx_m, (mlbl, col) in enumerate([
        ("Delta Outside Exposure (pp per +1 SD)", (43, 108, 176)),
        ("Delta Donations ALIMENTAR (/1k per +1 SD)", (197, 48, 48)),
    ]):
        yy = ly0 + 35 + idx_m * 55
        draw.line([(lx0 + 22, yy), (lx0 + 82, yy)], fill=col, width=5)
        draw.ellipse([lx0 + 42, yy - 10, lx0 + 62, yy + 10], fill=col)
        draw.text((lx0 + 100, yy - 18), mlbl, fill=(45, 55, 72), font=f_leg)

    xlbl_b = "Standardized OLS Slope per +1 SD of Trait (95% Cluster CI)"
    bbox = draw.textbbox((0, 0), xlbl_b, font=f_axis)
    draw.text(((bx0 + bx1) / 2 - (bbox[2] - bbox[0]) / 2, by1 + 96), xlbl_b, fill=(26, 54, 93), font=f_axis)

    out_img = img.resize((2200, 825), Image.Resampling.LANCZOS)
    p3 = os.path.join(OUT_DIR, "fig3_causal_interventions_and_7d.png")
    out_img.save(p3, dpi=(300, 300))
    print("Saved:", p3)


if __name__ == "__main__":
    make_fig1_cif()
    make_fig2_cox_and_bite_wear()
    make_fig3_causal_interventions()

