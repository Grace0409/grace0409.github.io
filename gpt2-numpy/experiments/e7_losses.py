import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import torch
import torch.nn.functional as F
from transformers import GPT2LMHeadModel

from bpe import GPT2Tokenizer
from common import WEIGHTS, save_json
from gpt2 import GPT2, Config, log_softmax, random_params, softmax

tok = GPT2Tokenizer(WEIGHTS / "vocab.json", WEIGHTS / "merges.txt")
base = GPT2.from_safetensors(WEIGHTS / "model.safetensors", np.float64)
hf = GPT2LMHeadModel.from_pretrained(str(WEIGHTS), attn_implementation="eager").eval()
EOS = 50256
result = {}


def next_token_nll(model, ids):
    logits = model.forward(np.array([ids])).logits[0]
    lp = log_softmax(logits)[:-1]
    return -lp[np.arange(len(ids) - 1), ids[1:]]


toy_logits = np.array([2.0, 1.0, 0.0, -1.0])
toy_p = softmax(toy_logits)
result["toy_cross_entropy"] = dict(logits=toy_logits.tolist(), probs=toy_p.tolist(), target=0, loss=float(-np.log(toy_p[0])))

text = "The capital of France is Paris."
ids = tok.encode(text)
nll = next_token_nll(base, ids)
hf64 = copy.deepcopy(hf).double()
with torch.no_grad():
    out = hf64(torch.tensor([ids]), labels=torch.tensor([ids]))
    ref32, ref = out.loss.item(), F.cross_entropy(out.logits[0, :-1], torch.tensor(ids[1:])).item()
result["pretrain"] = dict(
    text=text, tokens=[tok.decode([i]) for i in ids],
    per_token=[dict(context=tok.decode(ids[:i + 1]), target=tok.decode([ids[i + 1]]), p=float(np.exp(-n)), nll=float(n))
               for i, n in enumerate(nll)],
    mean_loss=float(nll.mean()), hf_loss=ref, hf_loss_field_float32=ref32, abs_diff=abs(float(nll.mean()) - ref),
)
print("pretrain", result["pretrain"]["mean_loss"], ref)
for row in result["pretrain"]["per_token"]:
    print(f"  {row['context']!r:36s} -> {row['target']!r:10s} p={row['p']:.4f} nll={row['nll']:.3f}")

all_ids = tok.encode((WEIGHTS / "tinyshakespeare.txt").read_text(encoding="utf-8"))
rng = np.random.default_rng(0)
windows = np.stack([all_ids[s:s + 65] for s in rng.integers(0, len(all_ids) - 66, size=8)])


def corpus_loss(model):
    lp = log_softmax(model.forward(windows[:, :-1]).logits)
    return float(-np.take_along_axis(lp, windows[:, 1:, None], axis=-1).mean())


random_losses = [corpus_loss(GPT2(random_params(Config(), seed=s, dtype=np.float32))) for s in range(3)]
result["pretrain_effect"] = dict(
    ln_vocab=float(np.log(50257)), random_init_loss_by_seed=random_losses, pretrained_loss=corpus_loss(base),
)
print(result["pretrain_effect"])

prompt = "Question: What is the capital of France?\nAnswer:"
chosen = " The capital of France is Paris."
rejected = " I don't know."
x, y_w, y_l = tok.encode(prompt), tok.encode(chosen) + [EOS], tok.encode(rejected) + [EOS]


full = x + y_w
per_token = next_token_nll(base, full)
sft = per_token[len(x) - 1:]
labels = torch.tensor([[-100] * len(x) + y_w])
with torch.no_grad():
    logits = hf64(torch.tensor([full])).logits[0, :-1]
    ref = F.cross_entropy(logits, labels[0, 1:], ignore_index=-100).item()
result["sft"] = dict(
    prompt=prompt, response=chosen, all_tokens_loss=float(per_token.mean()), response_only_loss=float(sft.mean()),
    hf_response_only_loss=ref, abs_diff=abs(float(sft.mean()) - ref),
    response_per_token=[dict(target=tok.decode([t]), p=float(np.exp(-n)), nll=float(n)) for t, n in zip(y_w, sft)],
)
print("sft", result["sft"]["all_tokens_loss"], result["sft"]["response_only_loss"], ref)


def ppo_term(ratio, adv, eps=0.2):
    return -min(ratio * adv, float(np.clip(ratio, 1 - eps, 1 + eps)) * adv)


result["toy_ppo"] = [dict(ratio=r, advantage=a, loss=ppo_term(r, a))
                     for r, a in [(1.0, 1.0), (1.1, 1.0), (1.5, 1.0), (0.5, 1.0), (1.5, -1.0), (0.5, -1.0)]]


def dpo_loss(lp_w, lp_w_ref, lp_l, lp_l_ref, beta=0.1):
    margin = (lp_w - lp_w_ref) - (lp_l - lp_l_ref)
    return float(np.logaddexp(0.0, -beta * margin)), margin


result["toy_dpo"] = [
    dict(lp_w=a, lp_w_ref=b, lp_l=c, lp_l_ref=d, beta=0.1, loss=dpo_loss(a, b, c, d)[0], margin=dpo_loss(a, b, c, d)[1])
    for a, b, c, d in [(-20, -20, -10, -10), (-18, -20, -10, -10), (-18, -20, -14, -10), (-22, -20, -6, -10)]
]
print(result["toy_ppo"], result["toy_dpo"])

LR, STEPS, BETA, EPS = 2e-5, 30, 0.1, 0.2


def response_logprob(model, x, y):
    logits = model(torch.tensor([x + y])).logits[0, len(x) - 1:-1]
    return logits.log_softmax(-1).gather(1, torch.tensor(y)[:, None]).sum()


def fresh():
    m = copy.deepcopy(hf)
    m.train(False)
    return m, torch.optim.Adam(m.parameters(), lr=LR)


with torch.no_grad():
    ref_w, ref_l = response_logprob(hf, x, y_w).item(), response_logprob(hf, x, y_l).item()

runs = {}

m, opt = fresh()
trace = []
for _ in range(STEPS):
    loss = -response_logprob(m, x, y_w) / len(y_w)
    trace.append(loss.item())
    opt.zero_grad(); loss.backward(); opt.step()
runs["SFT"] = dict(model=m, trace=trace)

m, opt = fresh()
trace = []
for _ in range(STEPS):
    margin = (response_logprob(m, x, y_w) - ref_w) - (response_logprob(m, x, y_l) - ref_l)
    loss = -F.logsigmoid(BETA * margin)
    trace.append(loss.item())
    opt.zero_grad(); loss.backward(); opt.step()
runs["DPO"] = dict(model=m, trace=trace)
result["dpo_first_loss"] = trace[0]
result["ln2"] = float(np.log(2))
print("dpo first", trace[0], "ln2", np.log(2))

m, opt = fresh()
torch.manual_seed(0)
trace, ppo_log, worked = [], [], None
N_SAMPLES, N_NEW, EPOCHS = 32, 8, 5
ITERATIONS = STEPS // EPOCHS
prompt_ids = torch.tensor([x]).repeat(N_SAMPLES, 1)
for iteration in range(ITERATIONS):
    with torch.no_grad():
        ids = prompt_ids
        for _ in range(N_NEW):
            logits = m(ids).logits[:, -1]
            ids = torch.cat([ids, torch.multinomial(logits.softmax(-1), 1)], dim=1)
        lp_old = m(ids).logits[:, len(x) - 1:-1].log_softmax(-1).gather(2, ids[:, len(x):, None])[..., 0]
    replies = [tok.decode(r.tolist()) for r in ids[:, len(x):]]
    rewards = torch.tensor([1.0 if "Paris" in r else 0.0 for r in replies])
    adv = (rewards - rewards.mean())[:, None].expand_as(lp_old)
    for epoch in range(EPOCHS):
        lp = m(ids).logits[:, len(x) - 1:-1].log_softmax(-1).gather(2, ids[:, len(x):, None])[..., 0]
        ratio = (lp - lp_old).exp()
        snapshot = ratio.detach(), lp.detach()
        clipped = ratio.clamp(1 - EPS, 1 + EPS)
        loss = -torch.min(ratio * adv, clipped * adv).mean()
        trace.append(loss.item())
        opt.zero_grad(); loss.backward(); opt.step()
        if iteration == 0 and epoch == EPOCHS - 1:
            i = int(rewards.argmax())
            worked = dict(reply=replies[i], reward=float(rewards[i]), baseline=float(rewards.mean()),
                          advantage=float(adv[i, 0]), mean_ratio=float(snapshot[0][i].mean()),
                          ratio_first_token=float(snapshot[0][i, 0]), lp_old_first=float(lp_old[i, 0]),
                          lp_new_first=float(snapshot[1][i, 0]))
    ppo_log.append(dict(iteration=iteration, mean_reward=float(rewards.mean()), mean_ratio=float(snapshot[0].mean()),
                        clip_fraction=float(((snapshot[0] - 1).abs() > EPS).float().mean()), example=replies[0]))
    print(ppo_log[-1])
runs["RLHF(PPO)"] = dict(model=m, trace=trace)
result["ppo_log"], result["ppo_worked"] = ppo_log, worked


def to_numpy(model):
    sd = model.state_dict()
    params = {}
    for name, value in sd.items():
        key = name.removeprefix("transformer.")
        if key in base.p:
            params[key] = value.numpy().astype(np.float64)
    assert params.keys() == base.p.keys()
    assert all(params[k].shape == base.p[k].shape for k in params)
    return GPT2(params)


def seq_logprob(model, x, y):
    return float(-next_token_nll(model, x + y)[len(x) - 1:].sum())


def first_token(model, prompt_ids, k=4):
    p = softmax(model.forward(np.array([prompt_ids])).logits[0, -1])
    return p, [(tok.decode([int(i)]), float(p[i])) for i in np.argsort(-p)[:k]]


def greedy(model, prompt_ids, n=14):
    ids = list(prompt_ids)
    for _ in range(n):
        ids.append(int(model.forward(np.array([ids])).logits[0, -1].argmax()))
    return tok.decode(ids[len(prompt_ids):])


GROUPS = {"wte": "wte", "wpe": "wpe", "attn": ".attn.", "mlp": ".mlp.", "ln": "ln_"}
control = tok.encode("Question: What is the capital of Japan?\nAnswer:")
unrelated = tok.encode("The weather today is")
p_base, top_base = first_token(base, x)
c_base, _ = first_token(base, control)
u_base, _ = first_token(base, unrelated)
kl = lambda p, q: float((p * (np.log(p + 1e-30) - np.log(q + 1e-30))).sum())

evaluation = {"start": dict(
    logp_chosen=seq_logprob(base, x, y_w), logp_rejected=seq_logprob(base, x, y_l), top_first=top_base,
    greedy=greedy(base, x), greedy_control=greedy(base, control), corpus_loss=corpus_loss(base),
)}
for name, run in runs.items():
    model = to_numpy(run["model"])
    p, top = first_token(model, x)
    c, _ = first_token(model, control)
    u, _ = first_token(model, unrelated)
    numerator = sum(float(((model.p[k] - base.p[k]) ** 2).sum()) for k in base.p)
    denominator = sum(float((base.p[k] ** 2).sum()) for k in base.p)
    groups = {}
    for g, needle in GROUPS.items():
        keys = [k for k in base.p if needle in k]
        groups[g] = float(np.sqrt(sum(((model.p[k] - base.p[k]) ** 2).sum() for k in keys)
                                  / sum((base.p[k] ** 2).sum() for k in keys)))
    lp_w, lp_l = seq_logprob(model, x, y_w), seq_logprob(model, x, y_l)
    evaluation[name] = dict(
        logp_chosen=lp_w, logp_rejected=lp_l, top_first=top, greedy=greedy(model, x), greedy_control=greedy(model, control),
        corpus_loss=corpus_loss(model), kl_prompt=kl(p, p_base), kl_control=kl(c, c_base), kl_unrelated=kl(u, u_base),
        weight_change_relative=float(np.sqrt(numerator / denominator)), weight_change_by_group=groups,
        first_loss=run["trace"][0], last_loss=run["trace"][-1], trace=run["trace"],
    )
    if name == "DPO":
        evaluation[name]["numpy_dpo_loss"] = dpo_loss(lp_w, ref_w, lp_l, ref_l, BETA)[0]
    e = evaluation[name]
    print(f"{name:10s} logp(w)={lp_w:.2f} logp(l)={lp_l:.2f} loss {e['first_loss']:.4f}->{e['last_loss']:.4f} "
          f"KL prompt={e['kl_prompt']:.4f} control={e['kl_control']:.4f} unrelated={e['kl_unrelated']:.5f} "
          f"corpus={e['corpus_loss']:.3f} dW={e['weight_change_relative']:.5f}")
    print("   ", top, repr(e["greedy"]), repr(e["greedy_control"]))
print("start", {k: v for k, v in evaluation["start"].items()})
result["evaluation"] = evaluation
result["settings"] = dict(lr=LR, steps=STEPS, beta=BETA, eps=EPS, ppo_samples=N_SAMPLES, ppo_new_tokens=N_NEW, ppo_epochs=EPOCHS)
result["texts"] = dict(prompt=prompt, chosen=chosen, rejected=rejected)
save_json("e7_losses.json", result)
