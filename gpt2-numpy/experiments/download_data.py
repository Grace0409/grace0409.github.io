import hashlib
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from common import WEIGHTS

HF = "https://huggingface.co/openai-community/gpt2/resolve/main/"
FILES = {
    "config.json": HF + "config.json",
    "vocab.json": HF + "vocab.json",
    "merges.txt": HF + "merges.txt",
    "model.safetensors": HF + "model.safetensors",
    "tinyshakespeare.txt": "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt",
}
MODEL_SHA256 = "248dfc3911869ec493c76e65bf2fcf7f615828b0254c12b473182f0f81d3a707"

WEIGHTS.mkdir(parents=True, exist_ok=True)
for name, url in FILES.items():
    path = WEIGHTS / name
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    print(f"{name}: {path.stat().st_size:,} bytes")

digest = hashlib.sha256((WEIGHTS / "model.safetensors").read_bytes()).hexdigest()
assert digest == MODEL_SHA256, "model.safetensors does not match the published checksum"
print("model.safetensors checksum ok")
