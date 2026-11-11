import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from collections import Counter

import tiktoken

from bpe import GPT2Tokenizer, encode_with_merges, train_bpe
from common import WEIGHTS, save_json

PAIRS = [
    ("안녕하세요, 만나서 반갑습니다.", "Hello, nice to meet you."),
    ("오늘 날씨가 정말 좋네요.", "The weather is really nice today."),
    ("나는 어제 도서관에서 책을 읽었다.", "I read a book at the library yesterday."),
    ("서울은 대한민국의 수도이다.", "Seoul is the capital of South Korea."),
    ("대규모 언어 모델은 다음 토큰을 예측한다.", "A large language model predicts the next token."),
    ("인공지능은 우리의 일상을 빠르게 바꾸고 있습니다.", "Artificial intelligence is rapidly changing our daily lives."),
    ("이 문제를 해결하려면 먼저 원인을 찾아야 한다.", "To solve this problem, we must first find the cause."),
    ("어텐션은 각 토큰이 다른 토큰을 얼마나 참고할지 결정한다.", "Attention decides how much each token refers to the others."),
]

tok = GPT2Tokenizer(WEIGHTS / "vocab.json", WEIGHTS / "merges.txt")
result = {}

counts = {}
for name in ["gpt2", "cl100k_base", "o200k_base"]:
    enc = tiktoken.get_encoding(name)
    ko = [len(enc.encode(k)) for k, _ in PAIRS]
    en = [len(enc.encode(e)) for _, e in PAIRS]
    counts[name] = {
        "ko_tokens": ko, "en_tokens": en, "ko_total": sum(ko), "en_total": sum(en),
        "ratio": sum(ko) / sum(en),
    }
ko_chars = sum(len(k) for k, _ in PAIRS)
en_chars = sum(len(e) for _, e in PAIRS)
ko_bytes = sum(len(k.encode()) for k, _ in PAIRS)
en_bytes = sum(len(e.encode()) for _, e in PAIRS)
for name, c in counts.items():
    c["ko_chars_per_token"] = ko_chars / c["ko_total"]
    c["en_chars_per_token"] = en_chars / c["en_total"]
    c["ko_bytes_per_token"] = ko_bytes / c["ko_total"]
    c["en_bytes_per_token"] = en_bytes / c["en_total"]
result["counts"] = counts
result["sizes"] = dict(ko_chars=ko_chars, en_chars=en_chars, ko_bytes=ko_bytes, en_bytes=en_bytes)
result["pairs"] = PAIRS

ref = tiktoken.get_encoding("gpt2")
shakespeare = (WEIGHTS / "tinyshakespeare.txt").read_text(encoding="utf-8")
cases = shakespeare.split("\n")
cases += [k for k, _ in PAIRS] + [e for _, e in PAIRS]
cases += [
    "", " ", "  \n\n  ", "\t", "한글 English 混合 テスト 123", "🙂🤖 emoji!", "don't we'll I'd they're",
    "   leading spaces", "trailing spaces   ", "a b", "1,234.56%", "<|endoftext|>", "naïve café",
]
mismatch = [c for c in cases if tok.encode(c) != ref.encode(c, disallowed_special=())]
whole = tok.encode(shakespeare) == ref.encode(shakespeare, disallowed_special=())
roundtrip_bad = [c for c in cases if tok.decode(tok.encode(c)) != c]
result["bpe_check"] = {
    "cases": len(cases), "mismatches": len(mismatch), "whole_corpus_identical": whole,
    "corpus_chars": len(shakespeare), "corpus_tokens": len(tok.encode(shakespeare)),
    "roundtrip_failures": len(roundtrip_bad),
}

sentence = "서울은 대한민국의 수도이다."
ids = tok.encode(sentence)
pieces = []
for i in ids:
    raw = tok.token_bytes(i)
    try:
        text, whole_char = raw.decode("utf-8"), True
    except UnicodeDecodeError:
        text, whole_char = raw.decode("utf-8", errors="replace"), False
    pieces.append(dict(id=i, hex=raw.hex(" "), text=text, valid_utf8=whole_char))
result["korean_pieces"] = pieces


def share_invalid(texts):
    ids = [i for t in texts for i in tok.encode(t)]
    bad = 0
    for i in ids:
        try:
            tok.token_bytes(i).decode("utf-8")
        except UnicodeDecodeError:
            bad += 1
    return bad / len(ids), len(ids)


ko_bad, ko_n = share_invalid([k for k, _ in PAIRS])
en_bad, en_n = share_invalid([e for _, e in PAIRS])
result["invalid_utf8_token_share"] = dict(korean=ko_bad, korean_n=ko_n, english=en_bad, english_n=en_n)

syllables = [chr(c) for c in range(0xAC00, 0xD7A4)]
hist = Counter(len(tok.encode(s)) for s in syllables)
hist_space = Counter(len(tok.encode(" " + s)) for s in syllables)
vocab_hangul = sum(1 for t in range(50256)
                   if any(0xAC00 <= ord(ch) <= 0xD7A3 for ch in tok.token_bytes(t).decode("utf-8", errors="ignore")))
result["hangul"] = {
    "syllables": len(syllables),
    "tokens_per_syllable": {str(k): v for k, v in sorted(hist.items())},
    "tokens_per_syllable_with_space": {str(k): v for k, v in sorted(hist_space.items())},
    "vocab_entries_containing_a_whole_syllable": vocab_hangul,
}

corpus = shakespeare[:200_000]
merges, sizes = train_bpe(corpus, 1000)
heldout = shakespeare[200_000:300_000]
heldout_bytes = len(heldout.encode())
curve = []
for n in [0, 10, 50, 100, 250, 500, 1000]:
    curve.append(dict(merges=n, train_tokens=sizes[n], heldout_tokens=len(encode_with_merges(heldout, merges[:n]))))
result["train_bpe"] = {
    "corpus_chars": len(corpus),
    "first_merges": [(a.decode("utf-8", "replace"), b.decode("utf-8", "replace")) for a, b in merges[:12]],
    "merges_100_to_105": [(a + b).decode("utf-8", "replace") for a, b in merges[100:105]],
    "curve": curve, "heldout_bytes": heldout_bytes,
    "korean_bytes": ko_bytes,
    "korean_tokens_with_english_merges": sum(len(encode_with_merges(k, merges)) for k, _ in PAIRS),
}

save_json("e1_tokenizer.json", result)
for name, c in counts.items():
    print(f"{name:12s} ko={c['ko_total']:3d} en={c['en_total']:3d} ratio={c['ratio']:.2f} "
          f"chars/token ko={c['ko_chars_per_token']:.2f} en={c['en_chars_per_token']:.2f}")
print(result["sizes"])
print(result["bpe_check"])
print(result["invalid_utf8_token_share"])
print(result["hangul"])
for p in pieces:
    print(p)
print(result["train_bpe"]["first_merges"], result["train_bpe"]["merges_100_to_105"])
print(curve, heldout_bytes, result["train_bpe"]["korean_tokens_with_english_merges"], ko_bytes)
