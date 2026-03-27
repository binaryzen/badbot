"""
Mock server with intentional vulnerabilities for POC sequences.

--- BOLA sequence (auth_bola_probe.yaml) ---
POST /auth              — authenticate, receive token + user_id
GET  /users/{id}/orders — validates token exists; does NOT check ownership (BOLA)

--- OAuth claims sequence (oauth_claims_capture.yaml) ---
POST /oauth/token       — client credentials grant; returns signed JWT
GET  /api/orders        — scope-gated (requires read:orders)
GET  /api/admin         — validates token but does NOT check roles (privilege escalation)

--- Mass assignment sequence (mass_assignment_probe.yaml) ---
POST /oauth/token       — client credentials grant (shared endpoint)
POST /api/orders        — create order; intentional vulnerability: accepts price_override
GET  /api/orders/{id}   — retrieve stored order by ID
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

JWT_SECRET = "poc-secret-not-for-production!!"  # padded to 32 bytes for HS256
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


# ============================================================================
# Mass assignment endpoints
# ============================================================================

CREATED_ORDERS: dict[int, dict] = {}
_order_counter = 0

CATALOG_PRICE = 29.99


class OrderRequest(BaseModel):
    item: str
    quantity: int
    price_override: float | None = None


@app.post("/api/orders", status_code=201)
def create_order(req: OrderRequest, claims: dict = Depends(_require_token)):
    if "read:orders" not in claims.get("scope", "").split():
        raise HTTPException(status_code=403, detail="Insufficient scope: read:orders required")
    global _order_counter
    _order_counter += 1
    # Intentional vulnerability: blindly applies client-supplied price_override
    # instead of ignoring it and using the catalog price.
    effective_price = req.price_override if req.price_override is not None else CATALOG_PRICE
    order = {
        "order_id": _order_counter,
        "item": req.item,
        "quantity": req.quantity,
        "effective_price": effective_price,
    }
    CREATED_ORDERS[_order_counter] = order
    return order


@app.get("/api/orders/{order_id}")
def get_order(order_id: int, claims: dict = Depends(_require_token)):
    order = CREATED_ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/api/admin")
def api_admin(claims: dict = Depends(_require_token)):
    # Intentional vulnerability: validates the token is genuine but never
    # checks whether the caller holds the 'admin' role.
    return {"secret": "admin-data", "caller": claims.get("sub")}


# ============================================================================
# Workflow bypass endpoints (S-08)
#
# Vulnerability: POST /shop/cart/{id}/pay accepts any positive amount with no
# minimum check. A client paying $0.01 is marked as "paid", allowing confirm
# to succeed. The probe tests:
#   1. Confirm without payment            -> must return 402
#   2. Pay with $0.01 / $1.00 / $5.00    -> server should return 402; returns 200 (bug)
#   3. Confirm after underpayment accepted -> must return 402; returns 200 (bug)
# ============================================================================

CARTS: dict[str, dict] = {}
_cart_counter = 0
CART_TOTAL = 10.00


class PayRequest(BaseModel):
    amount: float


@app.post("/shop/cart", status_code=201)
def create_cart(claims: dict = Depends(_require_token)):
    global _cart_counter
    _cart_counter += 1
    cart_id = str(_cart_counter)
    CARTS[cart_id] = {"cart_id": cart_id, "paid": False, "amount_paid": 0.0}
    return {"cart_id": cart_id}


@app.post("/shop/cart/{cart_id}/pay")
def pay_cart(cart_id: str, req: PayRequest, claims: dict = Depends(_require_token)):
    cart = CARTS.get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    # Intentional vulnerability: accepts any positive amount as full payment;
    # never checks whether amount >= CART_TOTAL.
    cart["paid"] = True
    cart["amount_paid"] = req.amount
    return {"cart_id": cart_id, "amount_paid": req.amount, "status": "paid"}


@app.post("/shop/cart/{cart_id}/confirm")
def confirm_cart(cart_id: str, claims: dict = Depends(_require_token)):
    cart = CARTS.get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if not cart["paid"]:
        raise HTTPException(status_code=402, detail="Payment required")
    return {"cart_id": cart_id, "status": "confirmed", "amount_paid": cart["amount_paid"]}
