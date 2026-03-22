"""
Mock server with an intentional BOLA vulnerability.

POST /auth              — authenticate, receive token + user_id
GET  /users/{id}/orders — returns orders for any user_id as long as the
                          token is valid; ownership is never checked (the bug)
"""
import secrets
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI()

USERS = {
    "alice": {"password": "password123", "user_id": 1},
    "bob":   {"password": "password456", "user_id": 2},
}

ORDERS = {
    1: [{"id": 101, "item": "Widget A", "amount": 29.99}],
    2: [{"id": 201, "item": "Widget B", "amount": 49.99}],
}

# token → user_id; in-memory only
TOKENS: dict[str, int] = {}


class AuthRequest(BaseModel):
    username: str
    password: str


@app.post("/auth")
def authenticate(req: AuthRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(16)
    TOKENS[token] = user["user_id"]
    return {"token": token, "user_id": user["user_id"]}


@app.get("/users/{user_id}/orders")
def get_orders(user_id: int, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="Invalid token")
    # BOLA: validates that the token exists, but never checks whether the
    # authenticated user owns the requested user_id.
    orders = ORDERS.get(user_id, [])
    return {"user_id": user_id, "orders": orders}
