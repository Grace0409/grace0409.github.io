import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import torch
from transformers import TemperatureLogitsWarper, TopKLogitsWarper, TopPLogitsWarper

from bpe import GPT2Tokenizer
from common import WEIGHTS, save_json
from gpt2 import GPT2, log_softmax, softmax
from sampling import Strategy, filter_logits, generate

tok = GPT2Tokenizer(WEIGHTS / "vocab.json", WEIGHTS / "merges.txt")
model = GPT2.from_safetensors(WEIGHTS / "model.safetensors", np.float64)

STRATEGIES = [
    Strategy("greedy", greedy=True),
    Strategy("T=0.1", temperature=0.1),
    Strategy("T=1.0", temperature=1.0),
    Strategy("T=2.0", temperature=2.0),
    Strategy("top-k=40", top_k=40),
    Strategy("top-p=0.9", top_p=0.9),
]
PROMPTS = {
    "france": "The capital of France is",
    "unicorn": "In a shocking finding, scientists discovered a herd of unicorns living in a remote valley.",
    "once": "Once upon a time, there was a little girl who",
}
N_SAMPLES, N_TOKENS = 64, 50
result = {"n_samples": N_SAMPLES, "n_tokens": N_TOKENS, "prompts": PROMPTS}

logits = model.forward(np.array([tok.encode(PROMPTS["unicorn"])])).logits[:, -1]
t_logits = torch.tensor(logits)
checks = {}
for s, warper in [
    (Strategy("t", temperature=0.7), TemperatureLogitsWarper(0.7)),
    (Strategy("k", top_k=40), TopKLogitsWarper(40)),
    (Strategy("p", top_p=0.9), TopPLogitsWarper(0.9)),
]:
    ref = warper(None, t_logits.clone()).numpy()
    mine = filter_logits(logits, s)
    same_kept = bool((np.isfinite(ref) == np.isfinite(mine)).all())
    keep = np.isfinite(ref)
    checks[s.name] = dict(same_kept=same_kept, kept=int(keep.sum()), max_err=float(np.abs(ref[keep] - mine[keep]).max()))
result["hf_warper_check"] = checks
print(checks)

first = {}
for key, prompt in PROMPTS.items():
    row = model.forward(np.array([tok.encode(prompt)])).logits[:, -1]
    stats = {}
    for s in STRATEGIES:
        if s.greedy:
            stats[s.name] = dict(top1=1.0, entropy=0.0, effective_tokens=1.0, support=1)
            continue
        p = softmax(filter_logits(row, s))[0]
        h = float(-(p[p > 0] * np.log(p[p > 0])).sum())
        stats[s.name] = dict(top1=float(p.max()), entropy=h, effective_tokens=float(np.exp(h)), support=int((p > 0).sum()))
    first[key] = stats
    p = softmax(row)[0]
    first[key]["top5_T1"] = [(tok.decode([int(i)]), float(p[i])) for i in np.argsort(-p)[:5]]
result["first_step"] = first


def repeated_ngram_share(seq, n=4):
    grams = [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]
    return 1 - len(set(grams)) / len(grams)


def average_logprob(prompt_ids, tokens):
    ids = np.concatenate([np.tile(prompt_ids, (len(tokens), 1)), tokens], axis=1)
    lp = log_softmax(model.forward(ids).logits)[:, :-1]
    picked = np.take_along_axis(lp, ids[:, 1:, None], axis=-1)[..., 0]
    return picked[:, len(prompt_ids) - 1:].mean(axis=1)


rows, examples = [], {}
for key, prompt in PROMPTS.items():
    prompt_ids = tok.encode(prompt)
    greedy_tokens = None
    for s in STRATEGIES:
        tokens = generate(model, prompt_ids, N_TOKENS, s, batch=N_SAMPLES, seed=1234)
        if s.greedy:
            greedy_tokens = tokens[0]
        lp = average_logprob(np.array(prompt_ids), tokens)
        rows.append(dict(
            prompt=key, strategy=s.name,
            distinct_outputs=len({t.tobytes() for t in tokens}),
            distinct_first_tokens=len(set(tokens[:, 0].tolist())),
            repeated_4gram_share=float(np.mean([repeated_ngram_share(t.tolist()) for t in tokens])),
            mean_logprob=float(lp.mean()),
            same_as_greedy=float((tokens == greedy_tokens).mean()),
        ))
        r = rows[-1]
        print(f"{key:8s} {s.name:10s} distinct={r['distinct_outputs']:3d} first={r['distinct_first_tokens']:3d} "
              f"rep4={r['repeated_4gram_share']:.3f} logp={r['mean_logprob']:.2f} =greedy={r['same_as_greedy']:.3f}")
        examples.setdefault(key, {})[s.name] = tok.decode(tokens[0].tolist())
result["rows"] = rows
result["examples"] = examples
row = model.forward(np.array([tok.encode(PROMPTS["france"])])).logits[:, -1]
top = np.argsort(-softmax(row)[0])[:10]
result["temperature_top10"] = {
    "tokens": [repr(tok.decode([int(i)])).strip("'") for i in top],
    **{f"T={t}": softmax(row / t)[0][top].tolist() for t in (0.1, 1.0, 2.0)},
}
save_json("e4_sampling.json", result)
for key, ex in examples.items():
    for name, text in ex.items():
        print(f"[{key}/{name}] {text[:170]!r}")
