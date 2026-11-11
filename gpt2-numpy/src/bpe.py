from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import regex as re

GPT2_SPLIT = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""")


def bytes_to_unicode() -> dict[int, str]:
    printable = [*range(ord("!"), ord("~") + 1), *range(0xA1, 0xAC + 1), *range(0xAE, 0xFF + 1)]
    table = {b: chr(b) for b in printable}
    n = 0
    for b in range(256):
        if b not in table:
            table[b] = chr(256 + n)
            n += 1
    return table


def merge_pair(parts, pair):
    merged, i = [], 0
    while i < len(parts):
        if i + 1 < len(parts) and (parts[i], parts[i + 1]) == pair:
            merged.append(parts[i] + parts[i + 1])
            i += 2
        else:
            merged.append(parts[i])
            i += 1
    return merged


class GPT2Tokenizer:
    def __init__(self, vocab_path: str | Path, merges_path: str | Path):
        self.encoder: dict[str, int] = json.loads(Path(vocab_path).read_text(encoding="utf-8"))
        self.decoder = {v: k for k, v in self.encoder.items()}
        lines = Path(merges_path).read_text(encoding="utf-8").split("\n")[1:]
        self.ranks = {tuple(line.split()): i for i, line in enumerate(lines) if line}
        self.byte_encoder = bytes_to_unicode()
        self.byte_decoder = {v: k for k, v in self.byte_encoder.items()}
        self.cache: dict[str, list[str]] = {}

    def bpe(self, token: str) -> list[str]:
        if token in self.cache:
            return self.cache[token]
        parts = list(token)
        while len(parts) > 1:
            pairs = set(zip(parts, parts[1:]))
            best = min(pairs, key=lambda pair: self.ranks.get(pair, float("inf")))
            if best not in self.ranks:
                break
            parts = merge_pair(parts, best)
        self.cache[token] = parts
        return parts

    def encode(self, text: str) -> list[int]:
        ids = []
        for chunk in GPT2_SPLIT.findall(text):
            chars = "".join(self.byte_encoder[b] for b in chunk.encode("utf-8"))
            ids.extend(self.encoder[piece] for piece in self.bpe(chars))
        return ids

    def token_bytes(self, token_id: int) -> bytes:
        return bytes(self.byte_decoder[c] for c in self.decoder[token_id])

    def decode(self, ids: list[int]) -> str:
        return b"".join(self.token_bytes(i) for i in ids).decode("utf-8", errors="replace")


def train_bpe(text: str, num_merges: int) -> tuple[list[tuple[bytes, bytes]], list[int]]:
    words = Counter(tuple(bytes([b]) for b in w.encode("utf-8")) for w in GPT2_SPLIT.findall(text))
    merges: list[tuple[bytes, bytes]] = []
    sizes = [sum(len(w) * n for w, n in words.items())]

    for _ in range(num_merges):
        pairs: Counter = Counter()
        for word, n in words.items():
            for pair in zip(word, word[1:]):
                pairs[pair] += n
        if not pairs:
            break
        best = max(pairs, key=lambda pair: (pairs[pair], pair))
        merges.append(best)

        updated: Counter = Counter()
        for word, n in words.items():
            updated[tuple(merge_pair(word, best))] += n
        words = updated
        sizes.append(sum(len(w) * n for w, n in words.items()))
    return merges, sizes


def encode_with_merges(text: str, merges: list[tuple[bytes, bytes]]) -> list[bytes]:
    ranks = {pair: i for i, pair in enumerate(merges)}
    out: list[bytes] = []
    for chunk in GPT2_SPLIT.findall(text):
        parts = [bytes([b]) for b in chunk.encode("utf-8")]
        while len(parts) > 1:
            best = min(zip(parts, parts[1:]), key=lambda pair: ranks.get(pair, float("inf")))
            if best not in ranks:
                break
            parts = merge_pair(parts, best)
        out.extend(parts)
    return out
