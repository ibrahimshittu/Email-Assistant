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

    grant_id = token_data.get("grant_id")
    email = token_data.get("email")

    if not grant_id:
        raise HTTPException(
            status_code=400, detail="Missing grant_id from Nylas response"
        )

    # Fetch user email from Nylas if not in token response
    if not email:
        try:
            email = nylas.get_grant_email(grant_id)
        except Exception:
            email = "unknown@example.com"

    # Check if account already exists
    acct = db.query(Account).filter(Account.nylas_grant_id == grant_id).first()
    if not acct:
        acct = Account(
            email=email,
            nylas_grant_id=grant_id,
            access_token=grant_id,  # In v3, grant_id is used for API calls
            provider="nylas",
        )
        db.add(acct)
    else:
        acct.email = email  # Update email in case it changed
        acct.access_token = grant_id

    db.commit()
    db.refresh(acct)

    # Redirect with account_id so frontend can track the user
    redirect_url = f"{config.frontend_base_url}/connect?success=1&account_id={acct.id}"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/auth/me")
async def auth_me(account_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Get current account information.

    If account_id is provided, returns that specific account.
    Otherwise, returns the first account (for single-user setup).
    For multi-user apps, you should implement proper session management.
    """
    if account_id:
        acct = db.query(Account).filter(Account.id == account_id).first()
    else:
        acct = db.query(Account).first()

    if not acct:
        return {"account": None}

    return {
        "account": {
            "id": acct.id,
            "email": acct.email,
            "provider": acct.provider,
            "nylas_grant_id": acct.nylas_grant_id,
            "created_at": acct.created_at.isoformat() if acct.created_at else None
        }
    }


@router.get("/auth/accounts")
async def list_accounts(db: Session = Depends(get_db)):
    """List all connected accounts"""
    accounts = db.query(Account).all()
    return {
        "accounts": [
            {
                "id": acct.id,
                "email": acct.email,
                "provider": acct.provider,
                "created_at": acct.created_at.isoformat() if acct.created_at else None
            }
            for acct in accounts
        ]
    }
