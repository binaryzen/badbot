"""
Mock server with two intentional vulnerabilities for POC sequences.

--- BOLA sequence (auth_bola_probe.yaml) ---
POST /auth              — authenticate, receive token + user_id
GET  /users/{id}/orders — validates token exists; does NOT check ownership (BOLA)

--- OAuth claims sequence (oauth_claims_capture.yaml) ---
POST /oauth/token       — client credentials grant; returns signed JWT
GET  /api/orders        — scope-gated (requires read:orders)
GET  /api/admin         — validates token but does NOT check roles (privilege escalation)
"""
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, Form, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()

# ============================================================================
# BOLA mock data
# ============================================================================

USERS = {
    "alice": {"password": "password123", "user_id": 1},
    "bob":   {"password": "password456", "user_id": 2},
}

ORDERS = {
    1: [{"id": 101, "item": "Widget A", "amount": 29.99}],
    2: [{"id": 201, "item": "Widget B", "amount": 49.99}],
}

SESSION_TOKENS: dict[str, int] = {}  # token → user_id


class AuthRequest(BaseModel):
    username: str
    password: str


@app.post("/auth")
def authenticate(req: AuthRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(16)
    SESSION_TOKENS[token] = user["user_id"]
    return {"token": token, "user_id": user["user_id"]}


@app.get("/users/{user_id}/orders")
def get_user_orders(user_id: int, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]
    if token not in SESSION_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    # BOLA: validates token exists but never checks ownership.
    orders = ORDERS.get(user_id, [])
    return {"user_id": user_id, "orders": orders}


# ============================================================================
# OAuth mock data
# ============================================================================

JWT_SECRET = "poc-secret-not-for-production"
JWT_ALGORITHM = "HS256"

OAUTH_CLIENTS = {
    "client_app": {
        "secret": "client_secret_123",
        "allowed_scopes": {"read:orders", "read:profile"},
        "roles": ["reader"],
    },
}


@app.post("/oauth/token")
def oauth_token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(""),
):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

    client = OAUTH_CLIENTS.get(client_id)
    if not client or client["secret"] != client_secret:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    requested = set(scope.split()) if scope else client["allowed_scopes"]
    granted = requested & client["allowed_scopes"]

    now = datetime.now(timezone.utc)
    claims = {
        "iss": "http://localhost:8000",
        "sub": client_id,
        "iat": now,
        "exp": now + timedelta(hours=1),
        "scope": " ".join(sorted(granted)),
        "roles": client["roles"],
    }
    access_token = jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "scope": " ".join(sorted(granted)),
    }


def _require_token(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return jwt.decode(authorization[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@app.get("/api/orders")
def api_orders(claims: dict = Depends(_require_token)):
    if "read:orders" not in claims.get("scope", "").split():
        raise HTTPException(status_code=403, detail="Insufficient scope: read:orders required")
    return {"orders": [{"id": 1, "item": "Widget A", "amount": 29.99}]}


@app.get("/api/admin")
def api_admin(claims: dict = Depends(_require_token)):
    # Intentional vulnerability: validates the token is genuine but never
    # checks whether the caller holds the 'admin' role.
    return {"secret": "admin-data", "caller": claims.get("sub")}
