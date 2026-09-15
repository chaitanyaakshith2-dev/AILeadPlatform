from fastapi import APIRouter, HTTPException, Query, status

from leads import LeadCreate, LeadResponse
from supabase_client import SupabaseConfigurationError, get_service_role_client

router = APIRouter(prefix="/public", tags=["public"])


@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def capture_public_lead(
    lead: LeadCreate,
    token: str = Query(..., min_length=16),
) -> dict:
    try:
        supabase = get_service_role_client()
    except SupabaseConfigurationError as error:
        raise HTTPException(status_code=503, detail="Public lead capture is not configured") from error

    settings_result = (
        supabase.table("business_settings")
        .select("user_id")
        .eq("webhook_token", token)
        .maybe_single()
        .execute()
    )
    if not settings_result.data:
        raise HTTPException(status_code=404, detail="Invalid webhook token")

    payload = lead.model_dump(exclude_none=True)
    payload["user_id"] = settings_result.data["user_id"]
    result = supabase.table("leads").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Lead could not be captured")
    return result.data[0]
