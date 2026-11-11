from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Config:
    vocab_size: int = 50257
    n_positions: int = 1024
    n_embd: int = 768
    n_layer: int = 12
    n_head: int = 12
    layer_norm_epsilon: float = 1e-5


@dataclass(frozen=True)
class Ablation:
    scale_by_sqrt_dk: bool = True
    causal_mask: bool = True
    residual: bool = True
    position_embedding: bool = True
    gelu: str = "tanh_approx"


REAL_GPT2 = Ablation()

_erf = np.vectorize(math.erf)


def gelu(x: np.ndarray, kind: str = "tanh_approx") -> np.ndarray:
    if kind == "tanh_approx":
        return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * x**3)))
    if kind == "erf":
        return (0.5 * x * (1.0 + _erf(x / math.sqrt(2.0)))).astype(x.dtype)
    raise ValueError(kind)


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def log_softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    return x - np.log(np.exp(x).sum(axis=axis, keepdims=True))


def layer_norm(x: np.ndarray, g: np.ndarray, b: np.ndarray, eps: float) -> np.ndarray:
    mean = x.mean(axis=-1, keepdims=True)
    var = ((x - mean) ** 2).mean(axis=-1, keepdims=True)
    return (x - mean) / np.sqrt(var + eps) * g + b


def linear(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    return x @ w + b


def attention(
    h: np.ndarray,
    w: np.ndarray,
    b: np.ndarray,
    w_proj: np.ndarray,
    b_proj: np.ndarray,
    n_head: int,
    ablation: Ablation = REAL_GPT2,
    past: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray, tuple[np.ndarray, np.ndarray]]:
    B, T, D = h.shape
    d_k = D // n_head

    q, k, v = np.split(linear(h, w, b), 3, axis=-1)
    split = lambda t: t.reshape(B, T, n_head, d_k).transpose(0, 2, 1, 3)
    q, k, v = split(q), split(k), split(v)

    if past is not None:
        k = np.concatenate([past[0], k], axis=2)
        v = np.concatenate([past[1], v], axis=2)
    T_total = k.shape[2]

    scores = q @ k.transpose(0, 1, 3, 2)
    if ablation.scale_by_sqrt_dk:
        scores = scores / math.sqrt(d_k)

    if ablation.causal_mask:
        mask = np.tril(np.ones((T_total, T_total), dtype=bool))[T_total - T :, :]
        scores = np.where(mask, scores, -np.inf)

    weights = softmax(scores, axis=-1)
    out = weights @ v

    out = out.transpose(0, 2, 1, 3).reshape(B, T, D)
    return linear(out, w_proj, b_proj), weights, (k, v)


def block(
    x: np.ndarray,
    p: dict[str, np.ndarray],
    prefix: str,
    cfg: Config,
    ablation: Ablation = REAL_GPT2,
    past: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, np.ndarray, tuple[np.ndarray, np.ndarray]]:
    eps = cfg.layer_norm_epsilon

    a, weights, present = attention(
        layer_norm(x, p[f"{prefix}ln_1.weight"], p[f"{prefix}ln_1.bias"], eps),
        p[f"{prefix}attn.c_attn.weight"],
        p[f"{prefix}attn.c_attn.bias"],
        p[f"{prefix}attn.c_proj.weight"],
        p[f"{prefix}attn.c_proj.bias"],
        cfg.n_head,
        ablation,
        past,
    )
    x = x + a if ablation.residual else a

    m = layer_norm(x, p[f"{prefix}ln_2.weight"], p[f"{prefix}ln_2.bias"], eps)
    m = gelu(linear(m, p[f"{prefix}mlp.c_fc.weight"], p[f"{prefix}mlp.c_fc.bias"]), ablation.gelu)
    m = linear(m, p[f"{prefix}mlp.c_proj.weight"], p[f"{prefix}mlp.c_proj.bias"])
    x = x + m if ablation.residual else m
    return x, weights, present


@dataclass
class Output:
    logits: np.ndarray
    hidden_states: list[np.ndarray] = field(default_factory=list)
    attentions: list[np.ndarray] = field(default_factory=list)
    presents: list[tuple[np.ndarray, np.ndarray]] = field(default_factory=list)


class GPT2:
    def __init__(self, params: dict[str, np.ndarray], cfg: Config = Config()):
        self.p, self.cfg = params, cfg

    @classmethod
    def from_safetensors(cls, path: str | Path, dtype=np.float32) -> "GPT2":
        from safetensors.numpy import load_file

        params = {k: v.astype(dtype) for k, v in load_file(str(path)).items() if not k.endswith(".attn.bias")}
        return cls(params)

    def embed(self, ids: np.ndarray, start: int = 0, ablation: Ablation = REAL_GPT2) -> np.ndarray:
        positions = np.arange(start, start + ids.shape[1])
        x = self.p["wte.weight"][ids]
        if ablation.position_embedding:
            x = x + self.p["wpe.weight"][positions]
        return x

    def forward(
        self,
        ids: np.ndarray,
        ablation: Ablation = REAL_GPT2,
        past: list[tuple[np.ndarray, np.ndarray]] | None = None,
    ) -> Output:
        ids = np.atleast_2d(ids)
        start = 0 if past is None else past[0][0].shape[2]
        x = self.embed(ids, start, ablation)

        out = Output(logits=None, hidden_states=[x])
        for i in range(self.cfg.n_layer):
            x, weights, present = block(
                x, self.p, f"h.{i}.", self.cfg, ablation, None if past is None else past[i]
            )
            out.attentions.append(weights)
            out.presents.append(present)
            out.hidden_states.append(x)

        x = layer_norm(x, self.p["ln_f.weight"], self.p["ln_f.bias"], self.cfg.layer_norm_epsilon)
        out.hidden_states[-1] = x
        out.logits = x @ self.p["wte.weight"].T
        return out


def random_params(cfg: Config = Config(), seed: int = 0, dtype=np.float32) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = lambda *shape: (rng.standard_normal(shape) * 0.02).astype(dtype)
    z = lambda *shape: np.zeros(shape, dtype=dtype)
    one = lambda *shape: np.ones(shape, dtype=dtype)
    D = cfg.n_embd
    scale = 1.0 / math.sqrt(2 * cfg.n_layer)
    p = {"wte.weight": n(cfg.vocab_size, D), "wpe.weight": n(cfg.n_positions, D),
         "ln_f.weight": one(D), "ln_f.bias": z(D)}
    for i in range(cfg.n_layer):
        q = f"h.{i}."
        p |= {
            q + "ln_1.weight": one(D), q + "ln_1.bias": z(D),
            q + "ln_2.weight": one(D), q + "ln_2.bias": z(D),
            q + "attn.c_attn.weight": n(D, 3 * D), q + "attn.c_attn.bias": z(3 * D),
            q + "attn.c_proj.weight": n(D, D) * scale, q + "attn.c_proj.bias": z(D),
            q + "mlp.c_fc.weight": n(D, 4 * D), q + "mlp.c_fc.bias": z(4 * D),
            q + "mlp.c_proj.weight": n(4 * D, D) * scale, q + "mlp.c_proj.bias": z(D),
        }
    return p
