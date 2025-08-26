#!/usr/bin/env python3
"""
UE8M0 enc/dec example plotter
- Generates two SVGs:
    1) encdec_timeseries.svg  (Input x vs Reconstructed x̂)
    2) encdec_tokens.svg      (Token timeline)

Usage:
    python encdec_plot.py
Requirements:
    - Python 3.x
    - matplotlib (no seaborn)
Notes:
    - This script does not set specific colors or styles.
    - Each chart is a single-figure plot.
"""

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import os

# ------------------------
# Example data (24 points)
# ------------------------
t = np.array([
    0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230
], dtype=float)

x = np.array([
    20.00,20.05,20.10,20.18,20.22,21.50,25.50,25.60,25.60,25.60,25.62,25.62,25.62,25.62,25.62,
    25.50,25.35,18.50,18.50,18.55,18.60,18.70,18.85,19.00
], dtype=float)

# Token list: (time_ms, type, payload)
tokens = [
    (20,  "ΣΔ+1", None),
    (40,  "ΣΔ+1", None),
    (50,  "NORM", 1.5),
    (60,  "MAX",  None),
    (130, "SILENT", None),
    (160, "ΣΔ-1", None),
    (170, "MIN",  None),
    (210, "ΣΔ+1", None),
    (230, "ΣΔ+1", None),
]

# ------------------------
# Simple reconstruction model for visualization
# ------------------------
xhat = []
cur = 20.0
sd_step = 0.10  # visual step per ΣΔ pulse (for demo)
for ti in t:
    for (t0, kind, payload) in tokens:
        if t0 == ti:
            if kind == "ΣΔ+1":
                cur += sd_step
            elif kind == "ΣΔ-1":
                cur -= sd_step
            elif kind == "NORM":
                cur = 21.5
            elif kind == "MAX":
                cur = 25.5
            elif kind == "MIN":
                cur = 18.5
            elif kind == "SILENT":
                cur = cur  # hold
    xhat.append(cur)

xhat = np.array(xhat, dtype=float)

# ------------------------
# Chart 1: Input vs Reconstructed
# ------------------------
plt.figure(figsize=(10,5), dpi=130)
plt.plot(t, x, marker='o', label='Input x')
plt.plot(t, xhat, marker='s', linestyle='--', label='Reconstructed x̂')
ymin, ymax = min(x.min(), xhat.min())-0.5, max(x.max(), xhat.max())+0.5
for (ti, kind, payload) in tokens:
    plt.axvline(ti, linestyle=':', alpha=0.6)
    label = kind if payload is None else f"{kind}({payload})"
    plt.text(ti, ymax, label, rotation=90, va='bottom', ha='center')
plt.title("UE8M0 Example: Input vs Reconstructed")
plt.xlabel("time (ms)")
plt.ylabel("value")
plt.legend()
plt.tight_layout()
plt.savefig("encdec_timeseries.svg", format="svg")
plt.close()

# ------------------------
# Chart 2: Token timeline
# ------------------------
levels = {"ΣΔ+1":1, "ΣΔ-1":-1, "NORM":2, "MAX":3, "MIN":-3, "SILENT":0}
tok_t = np.array([ti for ti,_,_ in tokens], dtype=float)
tok_y = np.array([levels[kind] for _,kind,_ in tokens], dtype=float)

plt.figure(figsize=(10,3.5), dpi=130)
markerline, stemlines, baseline = plt.stem(tok_t, tok_y, use_line_collection=True)
for ti, yi, (t0, kind, payload) in zip(tok_t, tok_y, tokens):
    lbl = kind if payload is None else f"{kind}({payload})"
    plt.text(ti, yi + (0.25 if yi>=0 else -0.35), lbl, ha='center', va='bottom' if yi>=0 else 'top')
plt.title("UE8M0 Example: Token timeline")
plt.xlabel("time (ms)")
plt.yticks(sorted(set(levels.values())), ["MIN(-3)","ΣΔ-1(-1)","SILENT(0)","ΣΔ+1(1)","NORM(2)","MAX(3)"])
plt.ylim(-3.8, 3.8)
plt.tight_layout()
plt.savefig("encdec_tokens.svg", format="svg")
plt.close()

print("Wrote encdec_timeseries.svg and encdec_tokens.svg")
