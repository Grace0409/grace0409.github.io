from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gpt2 import GPT2, softmax


@dataclass(frozen=True)
class Strategy:
    name: str
    temperature: float = 1.0
    top_k: int | None = None
    top_p: float | None = None
    greedy: bool = False


def filter_logits(logits: np.ndarray, s: Strategy) -> np.ndarray:
    x = logits.astype(np.float64) / s.temperature

    if s.top_k is not None:
        kth = np.sort(x, axis=-1)[:, -s.top_k][:, None]
        x = np.where(x < kth, -np.inf, x)

    if s.top_p is not None:
        order = np.argsort(-x, axis=-1)
        sorted_probs = np.take_along_axis(softmax(x), order, axis=-1)
        cumulative = np.cumsum(sorted_probs, axis=-1)
        drop_sorted = np.concatenate(
            [np.zeros_like(cumulative[:, :1], dtype=bool), cumulative[:, :-1] >= s.top_p], axis=-1
        )
        drop = np.zeros_like(drop_sorted)
        np.put_along_axis(drop, order, drop_sorted, axis=-1)
        x = np.where(drop, -np.inf, x)
    return x


def pick(logits: np.ndarray, s: Strategy, rng: np.random.Generator) -> np.ndarray:
    if s.greedy:
        return logits.argmax(axis=-1)
    probs = softmax(filter_logits(logits, s))
    u = rng.random((logits.shape[0], 1))
    return (probs.cumsum(axis=-1) < u).sum(axis=-1).clip(max=probs.shape[-1] - 1)


def generate(model: GPT2, prompt: list[int], n: int, s: Strategy, batch: int = 1, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    ids = np.tile(np.array(prompt), (batch, 1))
    out = model.forward(ids)
    generated = []
    for _ in range(n):
        token = pick(out.logits[:, -1], s, rng)
        generated.append(token)
        out = model.forward(token[:, None], past=out.presents)
    return np.stack(generated, axis=1)
