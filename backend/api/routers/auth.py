from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import load_config
from database import SessionLocal, Account
from services import NylasClient, new_state


router = APIRouter()
config = load_config()
nylas = NylasClient()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/auth/nylas/url")
async def get_auth_url():
    state = new_state()
    return {"auth_url": nylas.get_auth_url(state), "state": state}


@router.get("/nylas/callback")
async def nylas_callback(
    code: str, state: Optional[str] = None, db: Session = Depends(get_db)
):
    try:
        token_data = nylas.exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    grant = token_data.get("grant_id") or token_data.get("grant", {}).get("id")
    access_token = token_data.get("access_token") or token_data.get("access_token", "")

    if not grant or not access_token:
        raise HTTPException(
            status_code=400, detail="Missing grant/access token from Nylas response"
        )

    acct = db.query(Account).filter(Account.nylas_grant_id == grant).first()
    if not acct:
        acct = Account(
            email="unknown@example.com",
            nylas_grant_id=grant,
            access_token=access_token,
            provider="nylas",
        )
        db.add(acct)
    else:
        acct.access_token = access_token
    db.commit()

    redirect_url = f"{config.frontend_base_url}/connect?success=1"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/auth/me")
async def auth_me(db: Session = Depends(get_db)):
    acct = db.query(Account).first()
    if not acct:
        return {"account": None}
    return {"account": {"id": acct.id, "email": acct.email}}
