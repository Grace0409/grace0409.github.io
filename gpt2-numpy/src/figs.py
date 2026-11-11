from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from common import FIGURES, RESULTS

LINES = [
    dict(color="black", linestyle="-", marker="o", markerfacecolor="black"),
    dict(color="black", linestyle="--", marker="s", markerfacecolor="white"),
    dict(color="0.25", linestyle=":", marker="^", markerfacecolor="white"),
    dict(color="0.25", linestyle="-.", marker="D", markerfacecolor="0.25"),
]
REF = dict(color="0.55", linewidth=0.7, linestyle=(0, (1, 2)))


FONT_FILES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
]


def register_fonts():
    from matplotlib import font_manager

    for path in FONT_FILES:
        if Path(path).exists():
            font_manager.fontManager.addfont(path)


def paper_style(plt):
    register_fonts()
    plt.rcParams.update({
        "font.family": ["NanumGothic", "Malgun Gothic", "DejaVu Sans"],
        "axes.unicode_minus": True,
        "font.size": 9.5, "axes.labelsize": 9.5, "axes.titlesize": 9.5,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "legend.fontsize": 8.5,
        "text.color": "black", "axes.labelcolor": "black", "axes.edgecolor": "black",
        "xtick.color": "black", "ytick.color": "black",
        "axes.linewidth": 0.7,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True,
        "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": True, "axes.spines.right": True,
        "axes.grid": False,
        "legend.frameon": True, "legend.fancybox": False, "legend.framealpha": 1,
        "legend.edgecolor": "black", "legend.borderpad": 0.4, "legend.handlelength": 2.4,
        "patch.linewidth": 0.7, "hatch.linewidth": 0.6,
        "lines.linewidth": 1.0, "lines.markersize": 4.2, "lines.markeredgewidth": 0.8,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.04,
    })
    FIGURES.mkdir(exist_ok=True)
    return plt


def _handles(plt, labels, **extra):
    return [plt.Line2D([], [], label=l, **{**LINES[i], **extra}) for i, l in enumerate(labels)]


def load_e6_groups():
    groups = {}
    rerun = sorted((RESULTS / "e6_rerun").glob("*.json"))
    paths = rerun if len(rerun) == 36 else sorted((RESULTS / "e6_runs").glob("*.json"))
    for path in paths:
        run = json.loads(path.read_text(encoding="utf-8"))
        groups.setdefault(run["run"]["label"], []).append(run)
    unigram = json.loads((RESULTS / "e6_train_ablation.json").read_text(encoding="utf-8"))["unigram_val_loss"]
    return groups, unigram


def token_counts(plt, result):
    counts, sizes = result["counts"], result["sizes"]
    names = list(counts)
    pos = np.arange(len(names))
    w = 0.34
    fig, ax = plt.subplots(figsize=(4.8, 2.7), constrained_layout=True)
    ko = ax.bar(pos - w / 2, [counts[n]["ko_total"] for n in names], w, facecolor="0.3", edgecolor="black",
                label=f"한국어 8문장 ({sizes['ko_chars']}자)")
    en = ax.bar(pos + w / 2, [counts[n]["en_total"] for n in names], w, facecolor="white", edgecolor="black",
                hatch="////", label=f"같은 뜻 영어 8문장 ({sizes['en_chars']}자)")
    ax.bar_label(ko, padding=2, fontsize=8.5)
    ax.bar_label(en, padding=2, fontsize=8.5)
    ax.set_xticks(pos, names)
    ax.set_ylabel("토큰 수")
    ax.set_ylim(0, 440)
    ax.legend(loc="upper right")
    fig.savefig(FIGURES / "token_counts.png")


def train_ablation(plt, groups, unigram):
    series = ["기준", "√d_k 제거", "causal mask 제거", "잔차 연결 제거"]
    shown = ["기준", "√dₖ 제거", "causal mask 제거", "잔차 연결 제거"]
    panels = [("val_seen", "(a) 학습 때 손실 (모든 위치 평균)"), ("val_deployed", "(b) 생성 상황의 손실 (마지막 위치)")]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True, constrained_layout=True)
    for ax, (key, title) in zip(axes, panels):
        for i, label in enumerate(series):
            if label not in groups:
                continue
            runs = groups[label]
            steps = [h["step"] for h in runs[0]["history"]]
            curve = np.mean([[h[key] for h in r["history"]] for r in runs], axis=0)
            ax.plot(steps, curve, markevery=(i, 3), clip_on=False, **LINES[i])
        ax.axhline(unigram, **REF)
        ax.set_title(title, loc="left")
        ax.set_xlabel("학습 스텝")
        ax.set_xlim(-30, 1530)
        ax.set_xticks([0, 500, 1000, 1500])
    axes[0].set_ylabel("검증 손실 (nats)")
    axes[0].set_ylim(0, 4.6)
    handles = _handles(plt, shown) + [plt.Line2D([], [], label=f"글자 빈도만 쓸 때 ({unigram:.2f})", **REF)]
    fig.legend(handles=handles, loc="outside lower center", ncols=3, frameon=False,
               handlelength=3.0, columnspacing=1.8)
    fig.savefig(FIGURES / "train_ablation.png")


def depth(plt, groups, unigram):
    names = ["잔차 있음", "잔차 없음"]
    labels = {
        "잔차 있음": {2: "깊이 2 잔차 있음", 4: "깊이 4 잔차 있음", 8: "기준", 16: "깊이 16 잔차 있음"},
        "잔차 없음": {2: "깊이 2 잔차 없음", 4: "깊이 4 잔차 없음", 8: "잔차 연결 제거", 16: "깊이 16 잔차 없음"},
    }
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9), constrained_layout=True)
    ax = axes[0]
    for i, name in enumerate(names):
        xs = [d for d in (2, 4, 8, 16) if labels[name][d] in groups]
        runs = [groups[labels[name][d]] for d in xs]
        mean = [np.mean([r["history"][-1]["val_deployed"] for r in g]) for g in runs]
        std = [np.std([r["history"][-1]["val_deployed"] for r in g]) for g in runs]
        ax.errorbar(xs, mean, yerr=std, capsize=2, elinewidth=0.7, **LINES[i])
        for x, m in zip(xs, mean):
            ax.annotate(f"{m:.2f}", (x, m), xytext=(0, 6 if i == 0 else -11), textcoords="offset points",
                        ha="center", fontsize=7.5)
    ax.axhline(unigram, **REF)
    ax.set_xscale("log", base=2)
    ax.set_xticks([2, 4, 8, 16], ["2", "4", "8", "16"])
    ax.minorticks_off()
    ax.set_xlim(1.6, 20)
    ax.set_ylim(0, 4.2)
    ax.set_xlabel("층 수")
    ax.set_ylabel("마지막 위치 손실 (nats)")
    ax.set_title("(a) 층 수에 따른 최종 손실", loc="left")
    ax.legend(handles=_handles(plt, names) + [plt.Line2D([], [], label=f"글자 빈도만 ({unigram:.2f})", **REF)],
              loc="lower center")

    ax = axes[1]
    for i, name in enumerate(names):
        grads = np.mean([r["grads"] for r in groups[labels[name][16]]], axis=0)
        ax.plot(range(1, len(grads) + 1), grads, **LINES[i])
    ax.set_xlim(0.5, 16.5)
    ax.set_xticks([1, 4, 8, 12, 16])
    ax.set_ylim(0, 19)
    ax.set_xlabel("블록 (1 = 입력 쪽)")
    ax.set_ylabel("기울기 크기")
    ax.set_title("(b) 16층 모델의 블록별 기울기 (첫 스텝)", loc="left")
    ax.legend(handles=_handles(plt, names), loc="upper left")
    fig.savefig(FIGURES / "depth.png")


def fine_tuning(plt, evaluation):
    names = ["start", "SFT", "RLHF(PPO)", "DPO"]
    shown = ["시작", "SFT", "RLHF(PPO)", "DPO"]
    pos = np.arange(4)
    w = 0.34
    fig, ax = plt.subplots(figsize=(5.4, 3.0), constrained_layout=True)
    good = ax.bar(pos - w / 2, [evaluation[n]["logp_chosen"] for n in names], w, facecolor="0.3", edgecolor="black",
                  label="좋은 답")
    bad = ax.bar(pos + w / 2, [evaluation[n]["logp_rejected"] for n in names], w, facecolor="white", edgecolor="black",
                 hatch="////", label="나쁜 답")
    def fmt(v):
        return (f"{v:.3f}" if abs(v) < 0.1 else f"{v:.1f}").replace("-", "−")
    for label, b in zip(ax.bar_label(good, labels=[fmt(b.get_height()) for b in good], padding=2, fontsize=8.5), good):
        label.set_ha("right")
        label.set_x(b.get_x() + b.get_width())
    ax.bar_label(bad, labels=[fmt(b.get_height()) for b in bad], padding=2, fontsize=8.5)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_xticks(pos, shown)
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", top=True, bottom=False)
    ax.set_ylabel("답변의 로그확률 (0에 가까울수록 높음)")
    ax.set_ylim(-104, 0)
    ax.legend(loc="lower left")
    fig.savefig(FIGURES / "fine_tuning.png")


def attention_map(plt, a, names, layer, head):
    T = len(names)
    panels = [
        (a[0].mean(0), "(a) 1층, 헤드 평균"),
        (a[11].mean(0), "(b) 12층, 헤드 평균"),
        (a[layer, head], f"(c) {layer + 1}층 {head + 1}번 헤드"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), constrained_layout=True)
    for ax, (m, title) in zip(axes, panels):
        im = ax.imshow(m, cmap="Greys", vmin=0, vmax=1)
        ax.set_title(title, loc="left")
        ax.set_xticks(range(T), names, rotation=90, fontsize=6.5)
        ax.set_yticks(range(T), names, fontsize=6.5)
        ax.tick_params(length=2)
    axes[0].set_ylabel("보내는 토큰 (Query)")
    axes[1].set_xlabel("참고되는 토큰 (Key)")
    cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.02, aspect=22)
    cb.set_label("어텐션 가중치")
    cb.outline.set_linewidth(0.6)
    fig.savefig(FIGURES / "attention_map.png")


def temperature(plt, probs_by_t, labels):
    n = len(labels)
    style = [dict(facecolor="0.15"), dict(facecolor="0.7"), dict(facecolor="white", hatch="////")]
    w = 0.27
    fig, ax = plt.subplots(figsize=(6.2, 2.9), constrained_layout=True)
    for j, (name, p) in enumerate(probs_by_t):
        ax.bar(np.arange(n) + (j - 1) * w, p, w, edgecolor="black", label=name, **style[j])
    ax.set_xticks(range(n), labels)
    ax.set_ylabel("다음 토큰 확률")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", ncols=3)
    lines = [f"{name}: {p[0]:.3f}" for name, p in probs_by_t]
    ax.text(0.17, 0.62, "\n".join([f"첫 번째 토큰({labels[0].strip()})의 확률"] + lines), transform=ax.transAxes,
            fontsize=8.5, va="top", linespacing=1.5)
    fig.savefig(FIGURES / "temperature.png")
