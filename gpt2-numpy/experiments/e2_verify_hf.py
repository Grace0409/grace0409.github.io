import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import torch
from transformers import GPT2LMHeadModel

from bpe import GPT2Tokenizer
from common import WEIGHTS, save_json
from gpt2 import GPT2, Ablation

torch.set_grad_enabled(False)

tok = GPT2Tokenizer(WEIGHTS / "vocab.json", WEIGHTS / "merges.txt")
shakespeare = (WEIGHTS / "tinyshakespeare.txt").read_text(encoding="utf-8")

PROMPTS = {
    "short_en": "The capital of France is",
    "one_token": "Hello",
    "korean": "서울은 대한민국의 수도이다.",
    "mixed": "GPT-2는 2019년에 공개됐다. It has 12 layers & 🙂",
    "medium_en": "In a shocking finding, scientists discovered a herd of unicorns living in a remote valley.",
    "long_256": None,
    "full_1024": None,
}
all_ids = tok.encode(shakespeare[:20000])
inputs = {k: tok.encode(v) for k, v in PROMPTS.items() if v is not None}
inputs["long_256"] = all_ids[:256]
inputs["full_1024"] = all_ids[:1024]

hf = {
    "float32": GPT2LMHeadModel.from_pretrained(str(WEIGHTS), attn_implementation="eager").eval(),
    "float64": GPT2LMHeadModel.from_pretrained(str(WEIGHTS), attn_implementation="eager").eval().double(),
}
ours = {
    "float32": GPT2.from_safetensors(WEIGHTS / "model.safetensors", np.float32),
    "float64": GPT2.from_safetensors(WEIGHTS / "model.safetensors", np.float64),
}

rows = []
for precision in ["float32", "float64"]:
    for name, ids in inputs.items():
        arr = np.array([ids])
        t = time.perf_counter()
        mine = ours[precision].forward(arr)
        ours_s = time.perf_counter() - t
        t = time.perf_counter()
        ref = hf[precision](torch.tensor(arr), output_hidden_states=True, output_attentions=True)
        hf_s = time.perf_counter() - t

        ref_logits = ref.logits.numpy()
        diff = np.abs(mine.logits - ref_logits)
        rel = (diff / np.maximum(np.abs(ref_logits), 1e-12)).max()
        hidden = max(float(np.abs(a - b.numpy()).max()) for a, b in zip(mine.hidden_states, ref.hidden_states))
        attn = max(float(np.abs(a - b.numpy()).max()) for a, b in zip(mine.attentions, ref.attentions))
        rows.append(dict(
            precision=precision, input=name, tokens=len(ids),
            max_abs_err=float(diff.max()), mean_abs_err=float(diff.mean()), max_rel_err=float(rel),
            logit_abs_max=float(np.abs(ref_logits).max()),
            max_hidden_err=hidden, max_attention_err=attn,
            argmax_all_match=bool((mine.logits.argmax(-1) == ref_logits.argmax(-1)).all()),
            ours_seconds=ours_s, hf_seconds=hf_s,
        ))
        r = rows[-1]
        print(f"{precision} {name:10s} T={r['tokens']:4d} max={r['max_abs_err']:.3e} mean={r['mean_abs_err']:.3e} "
              f"hidden={hidden:.3e} attn={attn:.3e} argmax={r['argmax_all_match']} "
              f"ours={ours_s:.2f}s hf={hf_s:.2f}s")

ids = np.array([inputs["long_256"]])
ref64 = hf["float64"](torch.tensor(ids)).logits.numpy()
gelu_compare = {kind: float(np.abs(ours["float64"].forward(ids, Ablation(gelu=kind)).logits - ref64).max())
                for kind in ["tanh_approx", "erf"]}
print("gelu", gelu_compare)

a, b = inputs["short_en"], inputs["medium_en"][:len(inputs["short_en"])]
batch = ours["float64"].forward(np.array([a, b])).logits
batch_err = float(max(np.abs(batch[0] - ours["float64"].forward(np.array([a])).logits[0]).max(),
                      np.abs(batch[1] - ours["float64"].forward(np.array([b])).logits[0]).max()))

ids = inputs["medium_en"]
full = ours["float64"].forward(np.array([ids])).logits
cached = ours["float64"].forward(np.array([ids[:5]]))
past, last = cached.presents, []
for i in ids[5:]:
    step = ours["float64"].forward(np.array([[i]]), past=past)
    past = step.presents
    last.append(step.logits[0, -1])
cache_err = float(np.abs(np.stack(last) - full[0, 5:]).max())
print("batch_err", batch_err, "cache_err", cache_err)

n_params = sum(v.size for k, v in ours["float32"].p.items())
top = lambda logits: [(tok.decode([int(i)]), float(logits[i])) for i in np.argsort(-logits)[:5]]
sample = ours["float32"].forward(np.array([inputs["short_en"]])).logits[0, -1]
print(n_params, top(sample))

save_json("e2_verify_hf.json", dict(
    rows=rows, gelu_max_abs_err=gelu_compare, batch_err=batch_err, cache_err=cache_err,
    n_params=int(n_params), top5_france=top(sample), prompt_ids=inputs["short_en"],
    param_shapes={k: list(v.shape) for k, v in list(ours["float32"].p.items())[:16]},
))
