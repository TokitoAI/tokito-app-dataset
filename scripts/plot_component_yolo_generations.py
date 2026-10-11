from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/photo-model/component-yolo-generation-comparison.json"
OUT_DIR = ROOT / "docs/model-comparison"


def main() -> None:
    report = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    models = report["generations"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with (OUT_DIR / "component-yolo-generations-2026-10-11.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["generation", "name", "architecture", "parameters", "checkpoint_bytes", "images", "train_images", "validation_images", "test_images", "classes", "epochs_completed", "best_epoch", "reviewed_local_instances", "primary_scope", "confidence", "iou", "tp", "fp", "fn", "ignored", "precision", "recall", "map50", "map50_95", "evaluation_valid"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for m in models:
            p = m["primary_counts"]
            writer.writerow({"generation": m["generation"], "name": m["name"], "architecture": m["architecture"], "parameters": m["parameters"], "checkpoint_bytes": m["checkpoint_bytes"], "images": m["images"], "train_images": m["train_images"], "validation_images": m["validation_images"], "test_images": m["test_images"], "classes": m["classes"], "epochs_completed": m["epochs_completed"], "best_epoch": m["best_epoch"], "reviewed_local_instances": m["reviewed_local_instances"], "primary_scope": m["primary_scope"], "confidence": m["confidence"], "iou": m["iou"], "tp": p.get("tp"), "fp": p.get("fp"), "fn": p.get("fn"), "ignored": p.get("ignored"), "precision": m["precision"], "recall": m["recall"], "map50": m.get("map50"), "map50_95": m.get("map50_95"), "evaluation_valid": m["evaluation_valid"]})

    # Long-form table preserves every recorded operating point and class audit.
    audit_rows: list[dict] = []
    for m in models:
        def add(scope: str, metric_type: str, **kwargs: object) -> None:
            audit_rows.append({"generation": m["generation"], "model": m["name"], "scope": scope, "metric_type": metric_type, **kwargs})
        if m.get("validation_metrics"):
            add("G1 validation candidate boxes", "aggregate", **m["validation_metrics"])
        add(m["primary_scope"], "aggregate", confidence=m.get("confidence"), iou=m.get("iou"), **m.get("primary_counts", {}), precision=m.get("precision"), recall=m.get("recall"), map50=m.get("map50"), map50_95=m.get("map50_95"))
        if m.get("alternate_counts"):
            add(m["alternate_scope"], "aggregate", confidence=m.get("confidence"), iou=m.get("iou"), **m["alternate_counts"], precision=m.get("alternate_precision"), recall=m.get("alternate_recall"))
        for point in m.get("threshold_sweep", []):
            add("G2 same four-frame partial validation threshold sweep", "aggregate", **point, iou=0.5)
        for cls, value in m.get("per_class_map50_95", {}).items():
            add("G1 held-out candidate-box test", "class_metric", class_name=cls, map50_95=value)
        for cls, value in m.get("training_instance_counts_by_class", {}).items():
            add("G2 mask coverage, train plus validation", "class_label_count", class_name=cls, count=value)
        for cls, value in m.get("per_class_external_counts", {}).items():
            add("G3 external partial-region audit", "class_metric", class_name=cls, **value)
        for cls, value in m.get("per_class_tokito_counts", {}).items():
            add("G3 Tokito partial-mask audit", "class_metric", class_name=cls, **value)
    audit_path = OUT_DIR / "component-yolo-full-metrics-2026-10-11.csv"
    columns = ["generation", "model", "scope", "metric_type", "class_name", "confidence", "iou", "tp", "fp", "fn", "ignored", "precision", "recall", "map50", "map50_95", "count", "evaluation_valid", "note"]
    with audit_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(audit_rows)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, (ax_gen, ax_scale, ax_ap) = plt.subplots(1, 3, figsize=(19, 7.5), gridspec_kw={"width_ratios": [1.05, 1.1, 0.85]}, constrained_layout=True)
    colors = ["#3478B8", "#E28C2D", "#31966F"]
    x = np.arange(1, 4)

    # The main time series is explicitly the recorded primary diagnostic, not a controlled benchmark.
    for i, m in enumerate(models):
        ax_gen.scatter(x[i] - .08, m["precision"], color=colors[i], marker="o", s=85, edgecolor="white", zorder=4)
        ax_gen.scatter(x[i] + .08, m["recall"], color=colors[i], marker="s", s=85, edgecolor="white", zorder=4)
        ax_gen.annotate(f"{m['precision']:.3f}", (x[i] - .08, m["precision"]), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8)
        ax_gen.annotate(f"{m['recall']:.3f}", (x[i] + .08, m["recall"]), xytext=(0, -16), textcoords="offset points", ha="center", fontsize=8)
    # V2 Tokito local partial-mask diagnostic is separate from external candidate-region audit.
    m = models[2]
    ax_gen.scatter([3.27], [m["alternate_precision"]], facecolors="none", edgecolors=colors[2], marker="o", s=105, linewidths=2, label="V2 Tokito partial audit")
    ax_gen.scatter([3.27], [m["alternate_recall"]], facecolors="none", edgecolors=colors[2], marker="s", s=105, linewidths=2)
    ax_gen.annotate("1.000", (3.27, m["alternate_precision"]), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8, color="#246B4E")
    ax_gen.annotate("0.136", (3.27, m["alternate_recall"]), xytext=(0, -16), textcoords="offset points", ha="center", fontsize=8, color="#246B4E")
    ax_gen.set_xlim(.55, 3.65); ax_gen.set_ylim(0, 1.1)
    ax_gen.set_xticks(x, [f"G{m['generation']}\n{m['date'][5:]}" for m in models])
    ax_gen.set_ylabel("Reported precision / recall")
    ax_gen.set_title("Generation timeline\n● precision   ■ recall")
    ax_gen.legend(loc="upper left", fontsize=8)
    ax_gen.text(.02, .02, "Each point uses its own scope;\nnot an apples-to-apples trend.", transform=ax_gen.transAxes, fontsize=8, color="#555")

    # Model scale against reported P/R, with bubble size proportional to artifact bytes.
    params = np.array([m["parameters"] for m in models]) / 1e6
    for i, m in enumerate(models):
        bubble = 55 + 2.2 * (m["checkpoint_bytes"] / 1e6)
        ax_scale.scatter(params[i], m["precision"], s=bubble, color=colors[i], alpha=.8, marker="o", edgecolor="white", linewidth=.8)
        ax_scale.scatter(params[i], m["recall"], s=bubble, color=colors[i], alpha=.8, marker="s", edgecolor="white", linewidth=.8)
        ax_scale.annotate(f"G{i+1}: {params[i]:.2f}M params\n{m['checkpoint_bytes']/1e6:.2f} MB", (params[i], max(m["precision"], m["recall"])), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=7, color=colors[i])
    ax_scale.set_xscale("log"); ax_scale.set_xlim(1.5, 38); ax_scale.set_ylim(0, 1.1)
    ax_scale.set_xlabel("Learned parameters (millions, log scale)")
    ax_scale.set_title("Model size vs reported P/R\n● precision   ■ recall")
    ax_scale.text(.02, .02, "Bubble area scales with checkpoint bytes.\nP/R scopes differ and are not comparable.", transform=ax_scale.transAxes, fontsize=8, color="#555")

    # Only G1 has mAP metrics, so do not invent cross-generation mAP values.
    class_names = ["IC", "Capacitor", "Connector"]
    vals = models[0]["per_class_map50_95"]
    ys = [vals[k] for k in ["ic", "capacitor", "connector"]]
    bars = ax_ap.bar(class_names, ys, color=colors[0], width=.62)
    ax_ap.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
    ax_ap.set_ylim(0, .105); ax_ap.set_ylabel("mAP50–95")
    ax_ap.set_title("G1 held-out test\nper-class mAP50–95")
    ax_ap.tick_params(axis="x", labelrotation=20)
    ax_ap.text(.02, .96, "G2/G3: no comparable per-class mAP;\npartial-region audits only.", transform=ax_ap.transAxes, va="top", fontsize=7.5, color="#555")

    fig.suptitle("Tokito component YOLO generations — full recorded-metric audit", fontsize=15)
    png = OUT_DIR / "component-yolo-generations-2026-10-11.png"
    fig.savefig(png, dpi=190, bbox_inches="tight")
    plt.close(fig)

    # Release-history style view: performance over generations, model scale in
    # marker area, and the complete threshold sweep in a separate inset.
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.lines import Line2D

    release_fig = plt.figure(figsize=(17, 10), facecolor="#F4F7FB")
    grid = release_fig.add_gridspec(2, 2, height_ratios=[3.4, 1.35], width_ratios=[3.3, 1.2], hspace=.31, wspace=.23, left=.07, right=.97, top=.79, bottom=.08)
    ax = release_fig.add_subplot(grid[0, 0])
    ax_sweep = release_fig.add_subplot(grid[0, 1])
    ax.axis("on")
    ink, muted = "#182338", "#65738A"
    release_colors = ["#3C70D6", "#E18A33", "#19A58C"]
    x = np.array([1.0, 2.0, 3.0])
    params_m = np.array([m["parameters"] for m in models]) / 1e6
    bubble_sizes = 105 + 22 * params_m
    primary_p = np.array([m["precision"] for m in models])
    primary_r = np.array([m["recall"] for m in models])

    ax.set_facecolor("#FFFFFF")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#C9D3E0")
    ax.grid(axis="y", color="#E7ECF2", linewidth=.9)
    ax.set_axisbelow(True)
    ax.plot(x, primary_p, color="#365EAC", linewidth=2, alpha=.76, zorder=1)
    ax.plot(x, primary_r, color="#D06859", linewidth=2, alpha=.76, zorder=1)
    for i, m in enumerate(models):
        c = release_colors[i]
        ax.scatter(x[i], primary_p[i], s=bubble_sizes[i], color=c, marker="o", edgecolor="white", linewidth=1.6, zorder=3)
        ax.scatter(x[i], primary_r[i], s=bubble_sizes[i] * .76, color=c, marker="s", edgecolor="white", linewidth=1.6, zorder=3)
        ax.annotate(f"{primary_p[i]:.3f}", (x[i], primary_p[i]), xytext=(0, 12), textcoords="offset points", ha="center", color=ink, fontsize=9, fontweight="bold")
        ax.annotate(f"{primary_r[i]:.3f}", (x[i], primary_r[i]), xytext=(0, -18), textcoords="offset points", ha="center", color=ink, fontsize=9, fontweight="bold")
    # G1's validation point is shown as hollow markers; G3 local is a separate scope.
    g1v = models[0]["validation_metrics"]
    ax.scatter([.87], [g1v["precision"]], s=115, facecolors="none", edgecolors=release_colors[0], linewidths=2, marker="o", zorder=4)
    ax.scatter([.87], [g1v["recall"]], s=98, facecolors="none", edgecolors=release_colors[0], linewidths=2, marker="s", zorder=4)
    ax.annotate("G1 val .587", (.87, g1v["precision"]), xytext=(-8, 9), textcoords="offset points", ha="right", color=muted, fontsize=8)
    ax.scatter([3.14], [models[2]["alternate_precision"]], s=bubble_sizes[2], facecolors="none", edgecolors=release_colors[2], linewidths=2.2, marker="o", zorder=4)
    ax.scatter([3.14], [models[2]["alternate_recall"]], s=bubble_sizes[2] * .76, facecolors="none", edgecolors=release_colors[2], linewidths=2.2, marker="s", zorder=4)
    ax.annotate("Tokito local P 1.000", (3.14, 1.0), xytext=(-8, 11), textcoords="offset points", ha="right", color="#087C68", fontsize=8, fontweight="bold")
    ax.annotate("R .136", (3.14, .136), xytext=(8, -5), textcoords="offset points", color="#087C68", fontsize=8)
    ax.set_xlim(.55, 3.45); ax.set_ylim(0, 1.12)
    ax.set_xticks(x, [f"GENERATION {i}\n{m['date']}" for i, m in enumerate(models, start=1)], color=ink, fontsize=9, fontweight="bold")
    ax.set_ylabel("Reported precision / recall", color=ink, fontsize=10)
    ax.tick_params(axis="y", colors=muted)
    ax.set_title("Performance reported at each model release", loc="left", color=ink, fontsize=13, fontweight="bold", pad=13)
    legend = [Line2D([0], [0], color="#365EAC", marker="o", label="Precision", linewidth=2), Line2D([0], [0], color="#D06859", marker="s", label="Recall", linewidth=2)]
    ax.legend(handles=legend, frameon=False, loc="upper left", ncol=2, fontsize=9)

    ax_sweep.set_facecolor("#FFFFFF")
    ax_sweep.spines[["top", "right"]].set_visible(False)
    ax_sweep.spines[["left", "bottom"]].set_color("#C9D3E0")
    ax_sweep.grid(color="#E7ECF2", linewidth=.9)
    ax_sweep.set_axisbelow(True)
    sweep = models[1]["threshold_sweep"]
    sx = [p["precision"] for p in sweep]
    sy = [p["recall"] for p in sweep]
    ax_sweep.plot(sx, sy, color=release_colors[1], linewidth=1.5, alpha=.7)
    for p in sweep:
        ax_sweep.scatter(p["precision"], p["recall"], color=release_colors[1], edgecolor="white", s=80, zorder=3)
        ax_sweep.annotate(f"conf {p['confidence']:.2f}", (p["precision"], p["recall"]), xytext=(5, 5), textcoords="offset points", fontsize=7, color=ink)
    ax_sweep.set_xlim(.24, .38); ax_sweep.set_ylim(.03, .53)
    ax_sweep.set_xlabel("Precision", color=muted, fontsize=9); ax_sweep.set_ylabel("Recall", color=muted, fontsize=9)
    ax_sweep.set_title("G2 threshold sensitivity", loc="left", color=ink, fontsize=11, fontweight="bold", pad=11)
    ax_sweep.text(.03, .02, "Same four partial validation frames;\nnot independent test performance.", transform=ax_sweep.transAxes, color=muted, fontsize=7.5, va="bottom")

    card_ax = release_fig.add_subplot(grid[1, :])
    card_ax.set_xlim(0, 3); card_ax.set_ylim(0, 1); card_ax.axis("off")
    specs = [
        ("YOLO11n · DETECT", "2.59M parameters  ·  5.45 MB", "53 images  ·  3 classes  ·  20 epochs", "External candidate-box test · P .283 / R .140"),
        ("YOLO11m · SEGMENT", "22.38M parameters  ·  45.17 MB", "14 images  ·  21 classes  ·  91 epochs", "Known-specimen partial audit · P .429 / R .068"),
        ("YOLO11m · SEGMENT V2", "22.37M parameters  ·  89.97 MB", "70 images  ·  8 classes  ·  25 epochs", "External partial audit · P .750 / R .300"),
    ]
    for i, (title, scale, data, metric) in enumerate(specs):
        x0 = i + .035
        card_ax.add_patch(FancyBboxPatch((x0, .08), .93, .82, boxstyle="round,pad=.018,rounding_size=.025", linewidth=0, facecolor="#FFFFFF"))
        card_ax.add_patch(FancyBboxPatch((x0, .08), .025, .82, boxstyle="round,pad=.0,rounding_size=.02", linewidth=0, facecolor=release_colors[i]))
        card_ax.text(x0 + .07, .75, title, color=release_colors[i], fontsize=10, fontweight="bold", va="center")
        card_ax.text(x0 + .07, .53, scale, color=ink, fontsize=9, fontweight="bold", va="center")
        card_ax.text(x0 + .07, .34, data, color=muted, fontsize=8.5, va="center")
        card_ax.text(x0 + .07, .17, metric, color=muted, fontsize=7.7, va="center")

    release_fig.text(.07, .95, "TOKITO  /  COMPONENT VISION", color="#4D5D74", fontsize=9, fontweight="bold")
    release_fig.text(.07, .90, "Three model generations. One clear history.", color=ink, fontsize=21, fontweight="bold")
    release_fig.text(.07, .86, "Checkpoints, scale and reported diagnostics · different label scopes, not directly comparable · 10–11 Oct 2026", color=muted, fontsize=10)
    release_path = OUT_DIR / "component-yolo-model-release-timeline-2026-10-11.png"
    release_fig.savefig(release_path, dpi=190, facecolor=release_fig.get_facecolor(), bbox_inches="tight")
    plt.close(release_fig)
    print(json.dumps({"chart": str(png), "release_timeline": str(release_path), "csv": str(OUT_DIR / "component-yolo-generations-2026-10-11.csv"), "full_metrics_csv": str(audit_path), "generations": len(models), "full_metric_rows": len(audit_rows)}))


if __name__ == "__main__":
    main()
