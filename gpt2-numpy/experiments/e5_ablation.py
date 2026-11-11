import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np

from bpe import GPT2Tokenizer
from common import WEIGHTS, save_json
from gpt2 import GPT2, Ablation, log_softmax, softmax

tok = GPT2Tokenizer(WEIGHTS / "vocab.json", WEIGHTS / "merges.txt")
model = GPT2.from_safetensors(WEIGHTS / "model.safetensors", np.float64)
all_ids = tok.encode((WEIGHTS / "tinyshakespeare.txt").read_text(encoding="utf-8"))

VARIANTS = {
    "기준(GPT-2)": Ablation(),
    "√d_k 제거": Ablation(scale_by_sqrt_dk=False),
    "causal mask 제거": Ablation(causal_mask=False),
    "잔차 연결 제거": Ablation(residual=False),
    "위치 임베딩 제거": Ablation(position_embedding=False),
}

rng = np.random.default_rng(0)
starts = rng.integers(0, len(all_ids) - 129, size=16)
windows = np.stack([all_ids[s:s + 129] for s in starts])
inputs, targets = windows[:, :-1], windows[:, 1:]


def evaluate(ablation):
    out = model.forward(inputs, ablation)
    lp = log_softmax(out.logits)
    nll = -np.take_along_axis(lp, targets[..., None], axis=-1)[..., 0]
    acc = out.logits.argmax(-1) == targets
    entropies = []
    for a in out.attentions:
        p = a.reshape(-1, a.shape[-1])
        h = -(p * np.log(p + 1e-30)).sum(-1)
        if ablation.causal_mask:
            visible = np.tile(np.arange(1, a.shape[-1] + 1), a.shape[0] * a.shape[1])
        else:
            visible = np.full(p.shape[0], a.shape[-1])
        keep = visible > 1
        entropies.append(float((h[keep] / np.log(visible[keep])).mean()))
    return dict(
        loss=float(nll.mean()), top1_acc=float(acc.mean()),
        attention_entropy_first=entropies[0], attention_entropy_last=entropies[-1],
        attention_max_mean=float(np.mean([a.max(-1).mean() for a in out.attentions])),
        hidden_std_by_layer=[round(float(h.std()), 3) for h in out.hidden_states],
        logit_std=float(out.logits.std()),
    )


def greedy(prompt, ablation, n=20):
    ids = tok.encode(prompt)
    start = len(ids)
    for _ in range(n):
        logits = model.forward(np.array([ids]), ablation).logits[0, -1]
        ids.append(int(logits.argmax()))
    return tok.decode(ids[start:])


result = {"variants": {}, "uniform_loss": float(np.log(50257))}
for name, ablation in VARIANTS.items():
    r = evaluate(ablation)
    r["greedy"] = greedy("The capital of France is", ablation)
    result["variants"][name] = r
    print(f"{name:16s} loss={r['loss']:7.3f} acc={r['top1_acc']:.3f} ent(1st/last)={r['attention_entropy_first']:.3f}/"
          f"{r['attention_entropy_last']:.3f} attn_max={r['attention_max_mean']:.3f} logit_std={r['logit_std']:.1f}")
    print("   ", r["hidden_std_by_layer"])
    print("   ", repr(r["greedy"]))

ids = np.array([tok.encode("The animal didn't cross the street because it was too tired to walk")])
edited = ids.copy()
position = 8
edited[0, position] = tok.encode(" cat")[0]
leak = {}
for name in ["기준(GPT-2)", "causal mask 제거"]:
    a = model.forward(ids, VARIANTS[name]).logits
    b = model.forward(edited, VARIANTS[name]).logits
    change = np.abs(a - b).max(axis=-1)[0]
    leak[name] = dict(before_edit_max=float(change[:position].max()), from_edit_max=float(change[position:].max()),
                      by_position=change.round(4).tolist())
    print(name, leak[name]["before_edit_max"], leak[name]["from_edit_max"])
result["leak"] = dict(edited_position=position, **leak)

rng = np.random.default_rng(1)
n_keys, n_trials = 16, 4000
rows = []
for d in [4, 16, 64, 256, 1024, 4096]:
    q = rng.standard_normal((n_trials, 1, d))
    k = rng.standard_normal((n_trials, n_keys, d))
    scores = (q @ k.transpose(0, 2, 1))[:, 0]
    row = dict(d_k=d, theory_std=float(np.sqrt(d)), score_std=float(scores.std()))
    for label, s in [("raw", scores), ("scaled", scores / np.sqrt(d))]:
        p = softmax(s)
        h = -(p * np.log(p + 1e-30)).sum(-1)
        jacobian = np.einsum("ni,ij->nij", p, np.eye(n_keys)) - np.einsum("ni,nj->nij", p, p)
        row[label] = dict(
            top_weight=float(p.max(-1).mean()),
            entropy_ratio=float(h.mean() / np.log(n_keys)),
            jacobian_norm_median=float(np.median(np.linalg.norm(jacobian, axis=(1, 2)))),
        )
    rows.append(row)
    print(d, f"std={row['score_std']:.2f}", row["raw"], row["scaled"])
result["sqrt_dk"] = rows

save_json("e5_ablation.json", result)
