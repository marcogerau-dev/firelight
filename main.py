"""
Traffic Light API - DevRev SE Challenge Part 3
Stack: Python + FastAPI + SSE
Deploy: Railway / Render / Fly.io
"""
import asyncio
import json
import secrets
import time
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# ─── Config ──────────────────────────────────────────────────────────────────

API_KEY = "demo-api-key-devrev-2026"          # In production: load from env var
VALID_COLORS = ["red", "amber", "green"]

app = FastAPI(
    title="Traffic Light API",
    description="API-driven traffic light demo for DevRev SE Challenge",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI auto-generated
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production: restrict to known origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── State ───────────────────────────────────────────────────────────────────

state = {"color": "red", "updated_at": datetime.utcnow().isoformat()}
request_log: list[dict] = []
sse_clients: list[asyncio.Queue] = []

# ─── Auth ────────────────────────────────────────────────────────────────────

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# ─── Helpers ─────────────────────────────────────────────────────────────────

def log_request(method: str, endpoint: str, payload: Optional[dict], response: dict):
    entry = {
        "id": secrets.token_hex(4),
        "timestamp": datetime.utcnow().isoformat(),
        "method": method,
        "endpoint": endpoint,
        "payload": payload,
        "response": response,
    }
    request_log.insert(0, entry)
    if len(request_log) > 50:
        request_log.pop()
    # Broadcast to SSE clients
    for q in sse_clients:
        q.put_nowait(json.dumps(entry))


async def broadcast_state():
    for q in sse_clients:
        q.put_nowait(json.dumps({"event": "state_change", "data": state}))

# ─── Endpoints ───────────────────────────────────────────────────────────────

class SetColorRequest(BaseModel):
    color: str

@app.get("/colors", tags=["Traffic Light"])
def list_colors(_=Depends(verify_token)):
    """Return the list of valid traffic light colors."""
    result = {"colors": VALID_COLORS}
    log_request("GET", "/colors", None, result)
    return result


@app.get("/status", tags=["Traffic Light"])
def get_status(_=Depends(verify_token)):
    """Return the current color of the traffic light."""
    result = {"current_color": state["color"], "updated_at": state["updated_at"]}
    log_request("GET", "/status", None, result)
    return result


@app.post("/set", tags=["Traffic Light"])
async def set_color(body: SetColorRequest, _=Depends(verify_token)):
    """Change the traffic light to a specified color."""
    if body.color not in VALID_COLORS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid color '{body.color}'. Valid: {VALID_COLORS}",
        )
    state["color"] = body.color
    state["updated_at"] = datetime.utcnow().isoformat()
    result = {"message": f"Light set to {body.color}", "current_color": body.color}
    log_request("POST", "/set", {"color": body.color}, result)
    await broadcast_state()
    return result


# ─── SSE (Server-Sent Events) ─────────────────────────────────────────────────

@app.get("/events", include_in_schema=False)
async def sse_stream(request: Request):
    """Real-time SSE stream: state changes + request log updates."""
    queue: asyncio.Queue = asyncio.Queue()
    sse_clients.append(queue)

    async def generator():
        # Send current state immediately on connect
        yield f"data: {json.dumps({'event': 'connected', 'data': state})}\n\n"
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            sse_clients.remove(queue)

    return StreamingResponse(generator(), media_type="text/event-stream")


@app.get("/log", include_in_schema=False)
def get_log(_=Depends(verify_token)):
    """Return recent request log (used by the live debugger UI)."""
    return {"log": request_log}


# ─── Frontend (single-file, served from backend) ──────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def frontend():
    """Serve the traffic light UI."""
    return open("index.html").read()
