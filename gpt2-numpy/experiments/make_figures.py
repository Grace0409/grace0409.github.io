import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np

import figs
from common import RESULTS, setup_plots


def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


plt = setup_plots()
groups, unigram = figs.load_e6_groups()

figs.token_counts(plt, load("e1_tokenizer.json"))

maps = np.load(RESULTS / "e3_attention_maps.npz")
layer, head = load("e3_attention.json")["attention"]["tired"]["max_single_head_it_animal_where"]
names = [str(s).strip() or "\u2423" for s in maps["labels"]]
figs.attention_map(plt, maps["attention"].astype(np.float64), names, layer, head)

top = load("e4_sampling.json")["temperature_top10"]
figs.temperature(plt, [(k, top[k]) for k in ("T=0.1", "T=1.0", "T=2.0")], top["tokens"])

figs.train_ablation(plt, groups, unigram)
figs.depth(plt, groups, unigram)
figs.fine_tuning(plt, load("e7_losses.json")["evaluation"])
print("saved 6 figures")
