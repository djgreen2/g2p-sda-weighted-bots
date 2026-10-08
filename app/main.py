"""G2P SDA Weighted Bots API."""
from __future__ import annotations
import os, secrets, time
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.engine import merge, reply, token_hash
from app.memory import Memory

app = FastAPI(title="G2P SDA Weighted Bots", version="1.0.0")
SITE = Path(__file__).resolve().parent.parent / "site"
ADMIN = os.environ.get("G2P_ADMIN_KEY", "g2p-admin-dev")
BOTS: dict[str, dict] = {}
TOKENS: dict[str, dict] = {}
LEDGER: list[dict] = []

class InferIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=32000)
    bot_id: str = "sda-prime"
    force_gpu: bool = False
    salient: bool = False

class LicenseIn(BaseModel):
    partner: str
    share: float = 0.15
    note: str = ""

class ReportIn(BaseModel):
    gross_usd: float = Field(ge=0)
    period: str

def _auth(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "bearer token required")
    rec = TOKENS.get(token_hash(authorization.split(" ", 1)[1].strip()))
    if not rec or rec.get("revoked"):
        raise HTTPException(403, "token invalid")
    return rec

def _bot(bid: str) -> dict:
    if bid not in BOTS:
        BOTS[bid] = {"id": bid, "weights": None, "memory": Memory("triple"), "calls": 0, "gpu_calls": 0}
    return BOTS[bid]

@app.get("/health")
def health():
    return {"ok": True, "product": "g2p-sda-weighted-bots", "share_default": 0.15}

@app.get("/")
def index():
    return FileResponse(SITE / "index.html")

@app.get("/v1/merge")
def get_merge():
    return merge(None)

@app.post("/v1/license")
def issue(body: LicenseIn, x_admin_key: str | None = Header(default=None)):
    if x_admin_key != ADMIN:
        raise HTTPException(401, "admin key required")
    if not 0.10 <= body.share <= 0.20:
        raise HTTPException(400, "share must be 0.10-0.20")
    raw = "g2p_" + secrets.token_urlsafe(24)
    TOKENS[token_hash(raw)] = {"partner": body.partner, "share": body.share, "note": body.note, "issued": time.time(), "revoked": False}
    return {"token": raw, "partner": body.partner, "share": body.share, "show_once": True}

@app.post("/v1/infer")
def infer(body: InferIn, authorization: str | None = Header(default=None)):
    rec = _auth(authorization)
    b = _bot(body.bot_id)
    b["memory"].observe("user", body.prompt, body.salient)
    out = reply(body.prompt, b["memory"].dump(), b["weights"], body.force_gpu)
    b["memory"].observe("agent", out["text"], False)
    b["calls"] += 1
    if out["route"]["gpu"]:
        b["gpu_calls"] += 1
    return {"partner": rec["partner"], "bot_id": body.bot_id, **out, "memory": b["memory"].dump()}

@app.get("/v1/memory/{bot_id}")
def mem(bot_id: str, authorization: str | None = Header(default=None)):
    _auth(authorization)
    return _bot(bot_id)["memory"].dump()

@app.post("/v1/revenue")
def revenue(body: ReportIn, authorization: str | None = Header(default=None)):
    rec = _auth(authorization)
    owed = round(body.gross_usd * rec["share"], 2)
    row = {"partner": rec["partner"], "period": body.period, "gross_usd": body.gross_usd, "share": rec["share"], "owed_usd": owed, "t": time.time()}
    LEDGER.append(row)
    return row

@app.get("/v1/market")
def market():
    return {
        "name": "G2P SDA Weighted Bots",
        "parents": ["Serana", "Danny", "Bel"],
        "memory": ["echoic", "iconic", "dual-window", "triple-window"],
        "routing": "local until 1800 chars, then host token/GPU",
        "share": "15% attributable gross, band 10-20%",
        "contact": "djg2@g2ptechnologies.com",
    }
