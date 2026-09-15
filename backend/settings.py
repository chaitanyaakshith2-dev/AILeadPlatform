import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from auth import AuthContext, get_auth_context

router = APIRouter(prefix="/settings", tags=["settings"])


class BusinessSettingsUpdate(BaseModel):
    business_name: str = Field(default="", max_length=200)
    services_offered: str = Field(default="", max_length=2000)
    reply_signature: str = Field(default="", max_length=1000)


class BusinessSettingsResponse(BusinessSettingsUpdate):
    model_config = ConfigDict(extra="ignore")

    user_id: UUID
    webhook_url: str


def _webhook_url(webhook_token: str) -> str:
    base_url = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000").rstrip("/")
    return f"{base_url}/public/leads?token={webhook_token}"


def _response(data: dict) -> dict:
    return {**data, "webhook_url": _webhook_url(data["webhook_token"])}


def _default_settings(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "business_name": "",
        "services_offered": "",
        "reply_signature": "",
    }


@router.get("", response_model=BusinessSettingsResponse)
def get_settings(context: AuthContext = Depends(get_auth_context)) -> dict:
    result = (
        context.supabase.table("business_settings")
        .select("*")
        .eq("user_id", context.user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        payload = _default_settings(context.user_id)
        created = (
            context.supabase.table("business_settings")
            .insert(payload)
            .select("*")
            .maybe_single()
            .execute()
        )
        if not created.data:
            raise HTTPException(status_code=500, detail="Settings could not be created")
        return _response(created.data)
    return _response(result.data)


@router.put("", response_model=BusinessSettingsResponse)
def update_settings(
    settings: BusinessSettingsUpdate,
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    payload = settings.model_dump()
    payload["user_id"] = context.user_id
    result = (
        context.supabase.table("business_settings")
        .upsert(payload, on_conflict="user_id")
        .select("*")
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Settings could not be saved")
    return _response(result.data)
