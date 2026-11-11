import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np

from bpe import GPT2Tokenizer
from common import RESULTS, WEIGHTS, save_json
from gpt2 import GPT2

tok = GPT2Tokenizer(WEIGHTS / "vocab.json", WEIGHTS / "merges.txt")
model = GPT2.from_safetensors(WEIGHTS / "model.safetensors", np.float64)
wte, wpe = model.p["wte.weight"], model.p["wpe.weight"]
result = {}

cos = lambda a, b: float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
one = lambda word: tok.encode(word)[0]


def neighbours(word, k=6):
    v = wte[one(word)]
    sims = wte @ v / (np.linalg.norm(wte, axis=1) * np.linalg.norm(v))
    return [(tok.decode([int(i)]), float(sims[i])) for i in np.argsort(-sims)[1:k + 1]]


result["embedding"] = {
    "wte_shape": list(wte.shape), "wpe_shape": list(wpe.shape),
    "wte_mean_norm": float(np.linalg.norm(wte, axis=1).mean()),
    "wpe_mean_norm_first_128": float(np.linalg.norm(wpe[:128], axis=1).mean()),
    "wpe_mean_norm_all": float(np.linalg.norm(wpe, axis=1).mean()),
    "cos": {
        "king-queen": cos(wte[one(" king")], wte[one(" queen")]),
        "Paris-London": cos(wte[one(" Paris")], wte[one(" London")]),
        "cat-dog": cos(wte[one(" cat")], wte[one(" dog")]),
        "cat-Paris": cos(wte[one(" cat")], wte[one(" Paris")]),
    },
    "neighbours": {w: neighbours(w) for w in [" Paris", " king"]},
}

ids = tok.encode("the cat and the dog and the bird")
x = model.embed(np.array([ids]))[0]
the = [i for i, t in enumerate(ids) if t == one(" the")]
result["embedding"]["same_token_positions"] = the
result["embedding"]["same_token_cos"] = cos(x[the[0]], x[the[1]])
result["embedding"]["same_token_wpe_cos_0_100"] = cos(wte[one(" the")] + wpe[0], wte[one(" the")] + wpe[100])

base = "The animal didn't cross the street because it was too"
sentences = {"tired": base + " tired", "wide": base + " wide"}
per_sentence = {}
for key, text in sentences.items():
    ids = tok.encode(text)
    labels = [tok.decode([i]) for i in ids]
    a = model.forward(np.array([ids])).attentions
    T = len(ids)
    a = np.concatenate(a, axis=0)
    upper = a[:, :, np.triu_indices(T, 1)[0], np.triu_indices(T, 1)[1]]
    animal, street = labels.index(" animal"), labels.index(" street")
    it, last = labels.index(" it"), T - 1
    per_sentence[key] = {
        "labels": labels,
        "upper_triangle_max": float(upper.max()),
        "row_sum_error": float(np.abs(a.sum(-1) - 1).max()),
        "it_mean_over_heads_animal_by_layer": a[:, :, it, animal].mean(1).round(4).tolist(),
        "it_mean_over_heads_street_by_layer": a[:, :, it, street].mean(1).round(4).tolist(),
        "last_mean_over_heads_animal_by_layer": a[:, :, last, animal].mean(1).round(4).tolist(),
        "last_mean_over_heads_street_by_layer": a[:, :, last, street].mean(1).round(4).tolist(),
        "max_single_head_it_animal": float(a[:, :, it, animal].max()),
        "max_single_head_it_street": float(a[:, :, it, street].max()),
        "max_single_head_it_animal_where": [int(v) for v in np.unravel_index(a[:, :, it, animal].argmax(), (12, 12))],
    }
    if key == "tired":
        tired_attention, tired_labels = a, labels
result["attention"] = per_sentence

a = tired_attention
T = a.shape[-1]
entropy = []
for t in range(1, T):
    row = a[:, :, t, : t + 1]
    h = -(row * np.log(row + 1e-30)).sum(-1) / np.log(t + 1)
    entropy.append(h)
entropy = np.stack(entropy).mean(0)
result["attention_entropy_by_layer"] = entropy.mean(1).round(4).tolist()
result["attention_entropy_head_spread_layer1"] = [float(entropy[0].min()), float(entropy[0].max())]

save_json("e3_attention.json", result)
print({k: v for k, v in result["embedding"].items()})
for k, v in per_sentence.items():
    print(k, {m: n for m, n in v.items() if m != "labels"})
print(tired_labels, result["attention_entropy_by_layer"])

np.savez_compressed(
    RESULTS / "e3_attention_maps.npz", attention=tired_attention.astype(np.float32), labels=np.array(tired_labels)
)
