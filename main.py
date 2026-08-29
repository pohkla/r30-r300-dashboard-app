from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import secrets
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA = BASE_DIR / "data" / "trades.json"

SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_urlsafe(48)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_FILE = os.getenv("GITHUB_FILE", "data/trades.json")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

SUPPORTED_SYMBOLS = (
    "XAUUSD",
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    "USDJPY", "EURJPY", "GBPJPY", "AUDJPY",
    "EURGBP", "EURCHF", "EURAUD", "GBPAUD", "GBPCHF",
)

app = FastAPI(title="R30 / R300 Trade Dashboard", docs_url=None, redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="r30_admin_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=COOKIE_SECURE,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; "
        "script-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.url.path.startswith(("/admin", "/login")):
        response.headers["Cache-Control"] = "no-store"
    return response


class GitHubJsonStore:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.cache: list[dict[str, Any]] | None = None
        self.cached_at = 0.0

    @property
    def enabled(self) -> bool:
        return bool(GITHUB_TOKEN and GITHUB_REPO and GITHUB_FILE)

    @property
    def api_url(self) -> str:
        return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "r30-r300-dashboard",
        }

    def _github_read(self) -> tuple[list[dict[str, Any]], str]:
        with httpx.Client(timeout=20) as client:
            response = client.get(self.api_url, headers=self.headers, params={"ref": GITHUB_BRANCH})
        response.raise_for_status()
        payload = response.json()
        content = base64.b64decode(payload["content"]).decode("utf-8")
        trades = json.loads(content)
        if not isinstance(trades, list):
            raise ValueError("GitHub JSON ต้องเป็น Array")
        return trades, payload["sha"]

    def load(self, force: bool = False) -> list[dict[str, Any]]:
        with self.lock:
            if not force and self.cache is not None and time.time() - self.cached_at < 20:
                return json.loads(json.dumps(self.cache))
            if self.enabled:
                trades, _ = self._github_read()
            else:
                trades = json.loads(LOCAL_DATA.read_text(encoding="utf-8"))
            self.cache = trades
            self.cached_at = time.time()
            return json.loads(json.dumps(trades))

    def save(self, trades: list[dict[str, Any]]) -> None:
        with self.lock:
            if self.enabled:
                _, sha = self._github_read()
                raw = json.dumps(trades, ensure_ascii=False, indent=2) + "\n"
                payload = {
                    "message": "Update R30/R300 trade journal",
                    "content": base64.b64encode(raw.encode("utf-8")).decode("ascii"),
                    "sha": sha,
                    "branch": GITHUB_BRANCH,
                }
                with httpx.Client(timeout=20) as client:
                    response = client.put(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
            else:
                LOCAL_DATA.write_text(
                    json.dumps(trades, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            self.cache = trades
            self.cached_at = time.time()


store = GitHubJsonStore()
login_attempts: dict[str, list[float]] = {}


def number(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}"


def symbol_digits(symbol: str) -> int:
    """Return the broker-style quote precision used by the journal."""
    if symbol == "XAUUSD":
        return 3
    return 3 if symbol.endswith("JPY") else 5


def point_size(symbol: str) -> float:
    """One point is the smallest displayed quote increment."""
    if symbol == "XAUUSD":
        return 0.01
    return 0.001 if symbol.endswith("JPY") else 0.00001


def price(value: float | int | None, symbol: str = "XAUUSD") -> str:
    if value is None:
        return "—"
    if symbol == "XAUUSD":
        rendered = f"{value:,.3f}".rstrip("0").rstrip(".")
        return rendered
    return f"{value:.{symbol_digits(symbol)}f}"


def thai_datetime(value: str | None) -> str:
    if not value:
        return "ไม่พบข้อมูล"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    days = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
    return f"{days[dt.weekday()]} {dt.day:02d}/{dt.month:02d}/{dt.year + 543} {dt:%H:%M}"


def normalize_trade(trade: dict[str, Any]) -> dict[str, Any]:
    item = dict(trade)
    symbol = str(item.get("symbol") or "XAUUSD").upper()
    if symbol not in SUPPORTED_SYMBOLS:
        symbol = "XAUUSD"
    entry = float(item.get("entry") or 0)
    stop_loss = float(item["stop_loss"]) if item.get("stop_loss") not in (None, "") else None
    tp1 = float(item.get("tp1") or 0)
    tp2 = float(item["tp2"]) if item.get("tp2") not in (None, "") else None
    highest = item.get("highest_target")
    target_name = highest if highest in {"TP1", "TP2"} else "TP1"
    target_price = tp2 if target_name == "TP2" and tp2 is not None else tp1
    size = point_size(symbol)
    reward = round(abs(target_price - entry) / size)
    risk = round(abs(stop_loss - entry) / size) if stop_loss is not None else 0
    reward_pips = reward / 10 if symbol != "XAUUSD" else None
    risk_pips = risk / 10 if symbol != "XAUUSD" else None
    state = item.get("status", "pending")
    result = reward if state == "win" else -risk if state == "loss" else 0
    rr = f"1:{reward / risk:.2f}" if risk else "—"
    item.update(
        entry=entry,
        symbol=symbol,
        asset_type="GOLD" if symbol == "XAUUSD" else "FOREX",
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        target_name=target_name,
        target_price=target_price,
        reward=reward,
        risk=risk,
        reward_pips=reward_pips,
        risk_pips=risk_pips,
        result=result,
        rr=rr,
    )
    return item


def status_label(value: str) -> str:
    return {"win": "✓ TP", "loss": "✕ SL", "no-entry": "— ไม่ได้เข้า", "pending": "• รอผล"}.get(
        value, "• รอผล"
    )


templates.env.filters["num"] = number
templates.env.filters["price"] = price
templates.env.filters["thai_dt"] = thai_datetime
templates.env.globals["status_label"] = status_label


def signed_in(request: Request) -> bool:
    return request.session.get("admin") is True


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


def require_admin(request: Request) -> RedirectResponse | None:
    if not signed_in(request):
        return RedirectResponse("/login?next=/admin", status_code=status.HTTP_303_SEE_OTHER)
    return None


def verify_csrf(request: Request, submitted: str) -> None:
    expected = str(request.session.get("csrf", ""))
    if not expected or not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=400, detail="CSRF token ไม่ถูกต้อง")


def build_dashboard_context(request: Request, is_admin: bool) -> dict[str, Any]:
    try:
        plans = [normalize_trade(t) for t in store.load()]
        storage_error = ""
    except Exception as exc:
        plans = []
        storage_error = f"ไม่สามารถอ่านข้อมูลได้: {exc}"

    completed = [p for p in plans if p["status"] in {"win", "loss"}]
    wins = sum(p["status"] == "win" for p in plans)
    losses = sum(p["status"] == "loss" for p in plans)
    no_entries = sum(p["status"] == "no-entry" for p in plans)
    gross_profit = sum(max(0, p["result"]) for p in plans)
    gross_loss = abs(sum(min(0, p["result"]) for p in plans))
    net = gross_profit - gross_loss
    running = sorted((p for p in plans if p["status"] == "pending"), key=lambda p: p["id"], reverse=True)

    q = request.query_params.get("q", "")[:80].strip()
    status_filter = request.query_params.get("status", "")
    side_filter = request.query_params.get("side", "")
    symbol_filter = request.query_params.get("symbol", "")
    sort_key = request.query_params.get("sort", "latest")
    if status_filter not in {"", "win", "loss", "no-entry", "pending"}:
        status_filter = ""
    if side_filter not in {"", "BUY", "SELL"}:
        side_filter = ""
    if symbol_filter not in {"", *SUPPORTED_SYMBOLS}:
        symbol_filter = ""
    if sort_key not in {"latest", "oldest", "result_desc", "result_asc", "entry_desc", "entry_asc"}:
        sort_key = "latest"

    filtered = []
    for plan in plans:
        if status_filter and plan["status"] != status_filter:
            continue
        if side_filter and plan["side"] != side_filter:
            continue
        if symbol_filter and plan["symbol"] != symbol_filter:
            continue
        searchable = " ".join(
            str(plan.get(key, ""))
            for key in ("id", "symbol", "side", "entry", "stop_loss", "tp1", "tp2", "note", "open_at", "close_at")
        )
        if q and q.casefold() not in searchable.casefold():
            continue
        filtered.append(plan)

    sorters = {
        "latest": (lambda p: p["id"], True),
        "oldest": (lambda p: p["id"], False),
        "result_desc": (lambda p: p["result"], True),
        "result_asc": (lambda p: p["result"], False),
        "entry_desc": (lambda p: p["entry"], True),
        "entry_asc": (lambda p: p["entry"], False),
    }
    key_fn, reverse = sorters[sort_key]
    filtered.sort(key=key_fn, reverse=reverse)
    per_page = 10
    total_rows = len(filtered)
    total_pages = max(1, math.ceil(total_rows / per_page))
    try:
        page = max(1, min(int(request.query_params.get("page", "1")), total_pages))
    except ValueError:
        page = 1
    table_plans = filtered[(page - 1) * per_page : page * per_page]

    cumulative = [0]
    for plan in plans:
        cumulative.append(cumulative[-1] + plan["result"])
    chart_w, chart_h, pad_x, pad_y = 820, 230, 30, 24
    min_y, max_y = min(cumulative), max(cumulative)
    value_range = max(1, max_y - min_y)
    points = []
    for index, value in enumerate(cumulative):
        x = pad_x + index / max(1, len(cumulative) - 1) * (chart_w - 2 * pad_x)
        y = pad_y + (max_y - value) / value_range * (chart_h - 2 * pad_y)
        points.append(f"{x:.1f},{y:.1f}")
    area = f"{pad_x},{chart_h-pad_y} {' '.join(points)} {chart_w-pad_x},{chart_h-pad_y}"

    query = {"q": q, "status": status_filter, "side": side_filter, "symbol": symbol_filter, "sort": sort_key}
    page_urls = {}
    for page_no in range(1, total_pages + 1):
        params = {k: v for k, v in query.items() if v and not (k == "sort" and v == "latest")}
        params["page"] = page_no
        page_urls[page_no] = f"{'/admin' if is_admin else '/dashboard'}?{urlencode(params)}#trade-report"

    return {
        "request": request,
        "plans": plans,
        "running": running,
        "wins": wins,
        "losses": losses,
        "no_entries": no_entries,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net": net,
        "win_rate": wins / len(completed) * 100 if completed else 0,
        "table_plans": table_plans,
        "total_rows": total_rows,
        "row_start": (page - 1) * per_page + 1 if total_rows else 0,
        "row_end": min(page * per_page, total_rows),
        "page": page,
        "total_pages": total_pages,
        "page_urls": page_urls,
        "q": q,
        "status_filter": status_filter,
        "side_filter": side_filter,
        "symbol_filter": symbol_filter,
        "supported_symbols": SUPPORTED_SYMBOLS,
        "sort_key": sort_key,
        "chart_points": " ".join(points),
        "chart_area": area,
        "is_admin": is_admin,
        "saved": request.query_params.get("saved") == "1",
        "storage_error": storage_error,
        "storage_mode": "GitHub JSON" if store.enabled else "Local JSON (Development)",
    }


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "storage": "github" if store.enabled else "local"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context=build_dashboard_context(request, False))


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    redirect = require_admin(request)
    if redirect:
        return redirect
    context = build_dashboard_context(request, True)
    context["csrf"] = csrf_token(request)
    return templates.TemplateResponse(request=request, name="dashboard.html", context=context)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if signed_in(request):
        return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request, "csrf": csrf_token(request), "error": ""},
    )


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form(...), csrf: str = Form(...)):
    verify_csrf(request, csrf)
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [stamp for stamp in login_attempts.get(ip, []) if now - stamp < 600]
    if len(attempts) >= 5:
        error = "ลองเข้าสู่ระบบหลายครั้งเกินไป กรุณารอ 10 นาที"
    elif not ADMIN_PASSWORD:
        error = "ยังไม่ได้ตั้งค่า ADMIN_PASSWORD บน Render"
    elif hmac.compare_digest(password, ADMIN_PASSWORD):
        request.session.clear()
        request.session["admin"] = True
        request.session["csrf"] = secrets.token_urlsafe(32)
        login_attempts.pop(ip, None)
        return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
    else:
        attempts.append(now)
        login_attempts[ip] = attempts
        error = "รหัสผ่านไม่ถูกต้อง"
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request, "csrf": csrf_token(request), "error": error},
        status_code=400,
    )


@app.post("/logout")
def logout(request: Request, csrf: str = Form(...)):
    verify_csrf(request, csrf)
    request.session.clear()
    return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)


def find_trade(trades: list[dict[str, Any]], trade_id: int) -> dict[str, Any] | None:
    return next((trade for trade in trades if int(trade.get("id", 0)) == trade_id), None)


@app.get("/admin/trade/new", response_class=HTMLResponse)
def new_trade(request: Request):
    redirect = require_admin(request)
    if redirect:
        return redirect
    form = {
        "id": 0, "symbol": "XAUUSD", "side": "BUY", "entry": "", "stop_loss": "", "tp1": "", "tp2": "",
        "highest_target": "", "status": "pending", "open_at": "", "close_at": "", "note": "",
    }
    return templates.TemplateResponse(
        request=request,
        name="trade_form.html",
        context={"request": request, "form": form, "editing": False, "errors": [], "csrf": csrf_token(request), "supported_symbols": SUPPORTED_SYMBOLS},
    )


@app.get("/admin/trade/{trade_id}", response_class=HTMLResponse)
def edit_trade(request: Request, trade_id: int):
    redirect = require_admin(request)
    if redirect:
        return redirect
    trade = find_trade(store.load(), trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="ไม่พบแผน")
    form = {key: "" if value is None else value for key, value in trade.items()}
    form.setdefault("symbol", "XAUUSD")
    return templates.TemplateResponse(
        request=request,
        name="trade_form.html",
        context={"request": request, "form": form, "editing": True, "errors": [], "csrf": csrf_token(request), "supported_symbols": SUPPORTED_SYMBOLS},
    )


@app.post("/admin/trade/save", response_class=HTMLResponse)
def save_trade(
    request: Request,
    csrf: str = Form(...),
    trade_id: int = Form(0, alias="id"),
    symbol: str = Form("XAUUSD"),
    side: str = Form(...),
    status_value: str = Form(..., alias="status"),
    entry: str = Form(...),
    stop_loss: str = Form(""),
    tp1: str = Form(...),
    tp2: str = Form(""),
    highest_target: str = Form(""),
    open_at: str = Form(""),
    close_at: str = Form(""),
    note: str = Form(""),
):
    redirect = require_admin(request)
    if redirect:
        return redirect
    verify_csrf(request, csrf)
    form = {
        "id": trade_id, "symbol": symbol.upper(), "side": side, "status": status_value, "entry": entry,
        "stop_loss": stop_loss, "tp1": tp1, "tp2": tp2, "highest_target": highest_target,
        "open_at": open_at, "close_at": close_at, "note": note.strip(),
    }
    errors = []
    symbol = symbol.upper()
    if symbol not in SUPPORTED_SYMBOLS:
        errors.append("สินทรัพย์หรือคู่เงินไม่ถูกต้อง")
    if side not in {"BUY", "SELL"}:
        errors.append("ฝั่งไม่ถูกต้อง")
    if status_value not in {"pending", "win", "loss", "no-entry"}:
        errors.append("สถานะไม่ถูกต้อง")
    if highest_target not in {"", "TP1", "TP2"}:
        errors.append("TP สูงสุดไม่ถูกต้อง")
    try:
        entry_value = float(entry)
        tp1_value = float(tp1)
        stop_value = float(stop_loss) if stop_loss else None
        tp2_value = float(tp2) if tp2 else None
    except ValueError:
        errors.append("Entry, Stop Loss และ TP ต้องเป็นตัวเลข")
        entry_value, tp1_value, stop_value, tp2_value = 0, 0, None, None
    if status_value == "win" and not highest_target:
        errors.append("สถานะ TP ต้องเลือก TP สูงสุดที่ชน")
    if status_value == "loss" and stop_value is None:
        errors.append("สถานะ SL ต้องระบุ Stop Loss")
    if highest_target == "TP2" and tp2_value is None:
        errors.append("เลือก TP2 แล้ว ต้องระบุราคา TP2")
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="trade_form.html",
            context={"request": request, "form": form, "editing": bool(trade_id), "errors": errors, "csrf": csrf_token(request), "supported_symbols": SUPPORTED_SYMBOLS},
            status_code=422,
        )

    trades = store.load(force=True)
    new_id = trade_id or max([int(t.get("id", 0)) for t in trades] + [0]) + 1
    record = {
        "id": new_id,
        "symbol": symbol,
        "side": side,
        "entry": entry_value,
        "stop_loss": stop_value,
        "tp1": tp1_value,
        "tp2": tp2_value,
        "highest_target": highest_target or None,
        "status": status_value,
        "open_at": open_at or None,
        "close_at": close_at or None,
        "note": note.strip(),
        "result_points": 0,
    }
    record["result_points"] = normalize_trade(record)["result"]
    existing = find_trade(trades, new_id)
    if existing:
        trades[trades.index(existing)] = record
    else:
        trades.append(record)
    trades.sort(key=lambda item: int(item["id"]))
    try:
        store.save(trades)
    except Exception as exc:
        errors.append(f"บันทึก GitHub ไม่สำเร็จ: {exc}")
        return templates.TemplateResponse(
            request=request,
            name="trade_form.html",
            context={"request": request, "form": form, "editing": bool(trade_id), "errors": errors, "csrf": csrf_token(request), "supported_symbols": SUPPORTED_SYMBOLS},
            status_code=502,
        )
    return RedirectResponse("/admin?saved=1", status_code=status.HTTP_303_SEE_OTHER)
