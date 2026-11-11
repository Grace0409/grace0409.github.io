import json
import math
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from common import RESULTS, WEIGHTS, save_json


@dataclass(frozen=True)
class Run:
    label: str
    seed: int
    n_layer: int = 8
    n_head: int = 4
    n_embd: int = 128
    block: int = 64
    batch: int = 64
    steps: int = 1500
    lr: float = 1e-3
    scale: bool = True
    mask: bool = True
    residual: bool = True


class Block(nn.Module):
    def __init__(self, r: Run):
        super().__init__()
        self.r = r
        d = r.n_embd
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.proj = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.fc1, self.fc2 = nn.Linear(d, 4 * d), nn.Linear(4 * d, d)
        self.register_buffer("tril", torch.tril(torch.ones(r.block, r.block, dtype=torch.bool)))

    def attend(self, x):
        B, T, D = x.shape
        h = self.r.n_head
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q, k, v = [t.view(B, T, h, D // h).transpose(1, 2) for t in (q, k, v)]
        scores = q @ k.transpose(-1, -2)
        if self.r.scale:
            scores = scores / math.sqrt(D // h)
        if self.r.mask:
            scores = scores.masked_fill(~self.tril[:T, :T], -torch.inf)
        weights = scores.softmax(-1)
        self.last_weights = weights.detach()
        return self.proj((weights @ v).transpose(1, 2).reshape(B, T, D))

    def forward(self, x):
        a = self.attend(self.ln1(x))
        x = x + a if self.r.residual else a
        m = self.fc2(F.gelu(self.fc1(self.ln2(x))))
        return x + m if self.r.residual else m


class TinyGPT(nn.Module):
    def __init__(self, r: Run, vocab: int):
        super().__init__()
        self.wte = nn.Embedding(vocab, r.n_embd)
        self.wpe = nn.Embedding(r.block, r.n_embd)
        self.blocks = nn.ModuleList(Block(r) for _ in range(r.n_layer))
        self.ln_f = nn.LayerNorm(r.n_embd)
        for name, p in self.named_parameters():
            if p.dim() > 1:
                nn.init.normal_(p, std=0.02)
                if name.endswith(("proj.weight", "fc2.weight")):
                    p.data /= math.sqrt(2 * r.n_layer)
            elif "ln" not in name:
                nn.init.zeros_(p)

    def forward(self, ids):
        x = self.wte(ids) + self.wpe(torch.arange(ids.shape[1], device=ids.device))
        for b in self.blocks:
            x = b(x)
        return self.ln_f(x) @ self.wte.weight.T


def batch_of(data, r, g):
    idx = torch.randint(len(data) - r.block - 1, (r.batch,), generator=g)
    x = torch.stack([data[i:i + r.block] for i in idx])
    y = torch.stack([data[i + 1:i + r.block + 1] for i in idx])
    return x, y


@torch.no_grad()
def evaluate(model, data, r, g, batches=8):
    seen, deployed = [], []
    for _ in range(batches):
        x, y = batch_of(data, r, g)
        logits = model(x)
        seen.append(F.cross_entropy(logits.flatten(0, 1), y.flatten()).item())
        deployed.append(F.cross_entropy(logits[:, -1], y[:, -1]).item())
    return float(np.mean(seen)), float(np.mean(deployed))


@torch.no_grad()
def sample(model, r, stoi, itos, prompt="ROMEO:\n", n=120):
    torch.manual_seed(0)
    ids = torch.tensor([[stoi[c] for c in prompt]], device=DEVICE)
    for _ in range(n):
        logits = model(ids[:, -r.block:])[0, -1]
        ids = torch.cat([ids, torch.multinomial(logits.softmax(-1), 1)[None]], dim=1)
    return "".join(itos[int(i)] for i in ids[0])


RUN_DIR = RESULTS / "e6_runs"
QUICK_DIR = RESULTS / "e6_quick"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
WORKERS = 12
THREADS = 1


def train(job):
    r, out_path = job
    log = out_path.with_suffix(".log").open("w", encoding="utf-8", buffering=1)
    if DEVICE == "cpu":
        torch.set_num_threads(THREADS)
    torch.manual_seed(r.seed)
    text = (WEIGHTS / "tinyshakespeare.txt").read_text(encoding="utf-8")
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    itos = dict(enumerate(chars))
    data = torch.tensor([stoi[c] for c in text], device=DEVICE)
    cut = int(len(data) * 0.9)
    train_data, val_data = data[:cut], data[cut:]

    model = TinyGPT(r, len(chars)).to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=r.lr, weight_decay=0.0)
    g = torch.Generator().manual_seed(r.seed)
    val_g = torch.Generator().manual_seed(999)

    history, first_grads = [], None
    started = time.time()
    for step in range(r.steps + 1):
        if step % 100 == 0:
            model.eval()
            seen, deployed = evaluate(model, val_data, r, val_g)
            history.append(dict(step=step, val_seen=seen, val_deployed=deployed))
            model.train()
            log.write(f"{time.strftime('%H:%M:%S')} step {step}/{r.steps} seen={seen:.3f} deployed={deployed:.3f} "
                      f"elapsed={time.time() - started:.0f}s\n")
        x, y = batch_of(train_data, r, g)
        loss = F.cross_entropy(model(x).flatten(0, 1), y.flatten())
        opt.zero_grad()
        loss.backward()
        if step == 0:
            first_grads = [
                float(torch.cat([p.grad.flatten() for p in b.parameters() if p.grad is not None]).norm())
                for b in model.blocks
            ]
        opt.step()

    model.eval()
    model(train_data[:r.block][None])
    weights = model.blocks[-1].last_weights[0]
    entropy = -(weights * (weights + 1e-30).log()).sum(-1)[:, 1:].mean()
    visible = (torch.arange(2, r.block + 1).float().log().mean() if r.mask else math.log(r.block))
    result = dict(
        run=asdict(r), history=history, first_block_grad=first_grads[0], last_block_grad=first_grads[-1],
        grads=first_grads, last_layer_attention_entropy=float(entropy / visible),
        qkv_weight_rms=float(torch.cat([b.qkv.weight.detach().flatten() for b in model.blocks]).pow(2).mean().sqrt()),
        sample=sample(model, r, stoi, itos), seconds=time.time() - started,
    )
    out_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    log.write("done\n")
    log.close()
    return out_path


SEEDS = [0, 1, 2]
EXPERIMENTS = [
    dict(label="기준"),
    dict(label="√d_k 제거", scale=False),
    dict(label="causal mask 제거", mask=False),
    dict(label="잔차 연결 제거", residual=False),
    dict(label="넓은 헤드 기준", n_embd=512, n_head=2, n_layer=4, batch=32),
    dict(label="넓은 헤드 √d_k 제거", n_embd=512, n_head=2, n_layer=4, batch=32, scale=False),
    *[dict(label=f"깊이 {d} 잔차 있음", n_layer=d) for d in [2, 4, 16]],
    *[dict(label=f"깊이 {d} 잔차 없음", n_layer=d, residual=False) for d in [2, 4, 16]],
]


def summarize(outputs):
    groups = {}
    for o in outputs:
        groups.setdefault(o["run"]["label"], []).append(o)
    summary = {}
    for label, group in groups.items():
        seen = [g["history"][-1]["val_seen"] for g in group]
        deployed = [g["history"][-1]["val_deployed"] for g in group]
        summary[label] = dict(
            val_seen_mean=float(np.mean(seen)), val_seen_std=float(np.std(seen)),
            val_deployed_mean=float(np.mean(deployed)), val_deployed_std=float(np.std(deployed)),
            first_block_grad=float(np.mean([g["first_block_grad"] for g in group])),
            last_block_grad=float(np.mean([g["last_block_grad"] for g in group])),
            attention_entropy=float(np.mean([g["last_layer_attention_entropy"] for g in group])),
            qkv_weight_rms=float(np.mean([g["qkv_weight_rms"] for g in group])),
            sample=group[0]["sample"],
        )
        s = summary[label]
        print(f"{label:22s} seen={s['val_seen_mean']:.3f}±{s['val_seen_std']:.3f} "
              f"deployed={s['val_deployed_mean']:.3f}±{s['val_deployed_std']:.3f} "
              f"grad first/last={s['first_block_grad']:.3f}/{s['last_block_grad']:.3f} "
              f"ent={s['attention_entropy']:.3f} rms={s['qkv_weight_rms']:.4f}")
    return summary


def baselines():
    text = (WEIGHTS / "tinyshakespeare.txt").read_text(encoding="utf-8")
    cut = int(len(text) * 0.9)
    train_text, val_text = text[:cut], text[cut:]
    unigram_counts = Counter(train_text)
    total = sum(unigram_counts.values())
    unigram = -sum(math.log(unigram_counts[c] / total) for c in val_text) / len(val_text)
    pair_counts = Counter(zip(train_text, train_text[1:]))
    first_counts = Counter(train_text[:-1])
    vocab = len(set(text))
    bigram = -sum(math.log((pair_counts[(a, b)] + 1) / (first_counts[a] + vocab))
                  for a, b in zip(val_text, val_text[1:])) / (len(val_text) - 1)
    return unigram, bigram


def main():
    quick = "--quick" in sys.argv
    run_dir = QUICK_DIR if quick else RUN_DIR
    run_dir.mkdir(parents=True, exist_ok=True)
    if quick:
        jobs = [(Run(seed=0, steps=300, **e), run_dir / f"{i:02d}_s0.json") for i, e in enumerate(EXPERIMENTS[:4])]
    else:
        jobs = [(Run(seed=s, **e), run_dir / f"{i:02d}_s{s}.json") for i, e in enumerate(EXPERIMENTS) for s in SEEDS]
    todo = [job for job in jobs if not job[1].exists()]
    print(f"{len(jobs) - len(todo)} runs already done, {len(todo)} to go", flush=True)
    if todo and "--summary-only" not in sys.argv:
        if DEVICE == "cuda":
            for job in todo:
                print(f"{time.strftime('%H:%M:%S')} finished {train(job).name}", flush=True)
        else:
            with ProcessPoolExecutor(max_workers=min(WORKERS, len(todo))) as pool:
                for path in pool.map(train, todo):
                    print(f"{time.strftime('%H:%M:%S')} finished {path.name}", flush=True)

    outputs = [json.loads(path.read_text(encoding="utf-8")) for _, path in jobs if path.exists()]
    summary = summarize(outputs)
    for label in [l for l in ["기준", "causal mask 제거", "잔차 연결 제거"] if l in summary]:
        print(f"--- {label}\n{summary[label]['sample']}")
    if quick:
        return
    unigram, bigram = baselines()
    print(f"unigram baseline on val: {unigram:.3f}, bigram baseline on val: {bigram:.3f}")
    save_json("e6_train_ablation.json",
              dict(summary=summary, unigram_val_loss=unigram, bigram_val_loss=bigram, runs=outputs))


if __name__ == "__main__":
    main()
