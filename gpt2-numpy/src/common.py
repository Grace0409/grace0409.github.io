import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
WEIGHTS = Path(os.environ.get("GPT2_WEIGHTS", ROOT / "weights"))

sys.stdout.reconfigure(encoding="utf-8")


def save_json(name, data):
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def setup_plots():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from figs import paper_style

    return paper_style(plt)
