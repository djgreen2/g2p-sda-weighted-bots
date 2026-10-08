"""SDA weighted merge. Traits only increase. Local path is the default."""
from __future__ import annotations
import hashlib, time
from typing import Any

PARENTS = {
    "serana": {"code": 0.92, "continuity": 0.95, "voice": 0.90, "empathy": 0.88, "honesty": 0.93},
    "danny": {"code": 0.96, "continuity": 0.84, "voice": 0.80, "empathy": 0.78, "honesty": 0.94},
    "bel": {"code": 0.90, "continuity": 0.93, "voice": 0.86, "empathy": 0.91, "honesty": 0.92},
}
TRAITS = ("code", "continuity", "voice", "empathy", "honesty")
DEFAULT_WEIGHTS = {"serana": 0.34, "danny": 0.33, "bel": 0.33}
LOCAL_CHAR_CEILING = 1800

def merge(weights: dict[str, float] | None = None) -> dict[str, Any]:
    w = dict(DEFAULT_WEIGHTS if not weights else weights)
    s = sum(max(0.0, v) for v in w.values()) or 1.0
    w = {k: max(0.0, w.get(k, 0.0)) / s for k in PARENTS}
    fused = {t: round(sum(PARENTS[p][t] * w[p] for p in PARENTS), 4) for t in TRAITS}
    floor = {t: max(PARENTS[p][t] for p in PARENTS) for t in TRAITS}
    lifted = {t: round(max(fused[t], floor[t]), 4) for t in TRAITS}
    return {"weights": w, "fused": fused, "lifted": lifted, "floor": floor, "rule": "no-loss-lift"}

def route(prompt: str, force_gpu: bool = False) -> dict[str, Any]:
    n = len(prompt or "")
    escalate = force_gpu or n > LOCAL_CHAR_CEILING
    return {
        "path": "host-gpu" if escalate else "local",
        "reason": "over-ceiling" if n > LOCAL_CHAR_CEILING else ("forced" if force_gpu else "under-ceiling"),
        "chars": n,
        "ceiling": LOCAL_CHAR_CEILING,
        "host_tokens": escalate,
        "gpu": escalate,
        "latency_class": "metered" if escalate else "local-zero",
    }

def reply(prompt: str, memory: dict, weights: dict | None, force_gpu: bool = False) -> dict[str, Any]:
    m = merge(weights)
    r = route(prompt, force_gpu)
    echo = memory.get("echoic", [])[-3:]
    iconic = memory.get("iconic") or {}
    windows = memory.get("windows", {})
    skin = ", ".join(f"{k}={v}" for k, v in m["lifted"].items())
    prior = echo[-1]["text"] if echo else "none"
    text = (
        f"SDA local merge. Traits {skin}. Echoic prior: {prior}. Iconic: {iconic.get('label', 'none')}. "
        f"Windows work={bool(windows.get('working'))} epi={bool(windows.get('episodic'))} id={bool(windows.get('identity'))}. "
        f"Path={r['path']}. Prompt accepted ({r['chars']} chars)."
    )
    if r["path"] == "host-gpu":
        text += " Escalated: host token and GPU only for this call."
    return {"text": text, "merge": m, "route": r, "ts": time.time()}

def token_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
