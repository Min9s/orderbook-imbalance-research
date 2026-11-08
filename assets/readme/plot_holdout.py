"""Render the README comparison from published aggregates; no empirical refitting.

Run from the checkout: python assets/readme/plot_holdout.py
Requires Matplotlib. PNGs are rendered at 2x their intended CSS dimensions.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "results/final_v1/primary_holdout.json").read_text())
HORIZONS = (1, 5, 10)


def render(mobile=False, dark=False):
    bg, ink, muted, grid = (
        ("#0d1117", "#e6edf3", "#a6b0bb", "#30363d") if dark else
        ("#ffffff", "#1f2328", "#59636e", "#d8dee4")
    )
    accent = "#74bdd6" if dark else "#176987"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12 if mobile else 13})
    fig, ax = plt.subplots(figsize=(3.5, 2.95) if mobile else (6.2, 2.85), dpi=200)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    fig.text(.02, .94, "Final holdout: direction prediction" if mobile else
             "Direction prediction on the final holdout", color=ink,
             fontsize=12 if mobile else 15, weight="bold")
    fig.text(.02, .86, "Nonzero future returns only", color=muted, fontsize=11 if mobile else 12)
    for key, offset, color, marker in (
        ("obi", -.14, accent, "o"), ("price_change", .14, muted, "s")
    ):
        for index, horizon in enumerate(HORIZONS):
            row = DATA["horizons"][str(horizon)]
            model = row["models"][key]
            cm = model["confusion_matrix"]
            ba = sum(cm[i][i] / sum(cm[i]) for i in (0, 1)) / 2
            assert abs(ba - model["balanced_accuracy"]) < 1e-12
            lo, hi = row["bootstrap"]["60s_offset0"]["ci95"][key + "_balanced_accuracy"]
            ax.errorbar(ba, index + offset, xerr=[[ba-lo], [hi-ba]], fmt=marker,
                        color=color, markersize=5, capsize=3, elinewidth=1.4, zorder=3)
    ax.set(yticks=range(3), yticklabels=["1 s", "5 s", "10 s"],
           ylim=(2.45, -.45), xlim=(.47, .82), xticks=[.5, .6, .7, .8])
    ax.set_xlabel("Balanced accuracy (0–1)", color=ink, labelpad=7)
    ax.axvline(.5, color=muted, lw=1, ls=(0, (3, 3)), zorder=1)
    ax.xaxis.grid(True, color=grid, lw=.6)
    ax.tick_params(colors=ink, length=0, pad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    handles = [Line2D([], [], marker="o", color=accent, linestyle="", label="OBI logistic"),
               Line2D([], [], marker="s", color=muted, linestyle="", label="Past-price rule")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(.01, -.005),
               ncol=2, frameon=False, labelcolor=ink, fontsize=10 if mobile else 12,
               handletextpad=.3, columnspacing=1.2)
    fig.subplots_adjust(left=.15 if mobile else .09, right=.97, bottom=.29, top=.77)
    suffix = ("-mobile" if mobile else "") + ("-dark" if dark else "")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for text in fig.texts:
        bounds = text.get_window_extent(renderer)
        assert bounds.x0 >= 0 and bounds.x1 <= fig.bbox.width, text.get_text()
    fig.savefig(OUT / f"holdout{suffix}.png", facecolor=bg)
    plt.close(fig)


if __name__ == "__main__":
    for mobile in (False, True):
        for dark in ((False,) if mobile else (False, True)):
            render(mobile, dark)
    print("Rendered three display variants from unchanged primary_holdout.json.")
