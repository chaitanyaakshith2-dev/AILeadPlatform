from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ai import (
    AIAnalysisError,
    AIConfigurationError,
    AIReplyError,
    LeadAnalysis,
    analyze_lead_with_ai,
    generate_followup_reply,
)
from auth import AuthContext, get_auth_context

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None
    company: str | None = None
    message: str = Field(min_length=1)

    @field_validator("name", "message")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class LeadUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    email: str | None = None
    company: str | None = None
    message: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)

    @field_validator("name", "message", "status")
    @classmethod
    def optional_text_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "LeadUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        return self


class LeadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    name: str
    email: str | None = None
    company: str | None = None
    message: str
    status: str
    analysis: LeadAnalysis | None = None
    created_at: datetime
    updated_at: datetime


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    lead: LeadCreate,
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    payload = lead.model_dump(exclude_none=True)
    payload["user_id"] = context.user_id
    result = context.supabase.table("leads").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Lead could not be created")
    return result.data[0]


@router.get("", response_model=list[LeadResponse])
def list_leads(context: AuthContext = Depends(get_auth_context)) -> list[dict]:
    result = (
        context.supabase.table("leads")
        .select("*")
        .eq("user_id", context.user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(
    lead_id: UUID,
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    result = (
        context.supabase.table("leads")
        .select("*")
        .eq("id", str(lead_id))
        .eq("user_id", context.user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise not_found()
    return result.data


@router.post("/{lead_id}/analyze", response_model=LeadResponse)
def analyze_lead(
    lead_id: UUID,
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    lead_result = (
        context.supabase.table("leads")
        .select("*")
        .eq("id", str(lead_id))
        .eq("user_id", context.user_id)
        .maybe_single()
        .execute()
    )
    if not lead_result.data:
        raise not_found()

    try:
        analysis = analyze_lead_with_ai(lead_result.data["message"])
    except AIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except AIAnalysisError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    updated_result = (
        context.supabase.table("leads")
        .update({"analysis": analysis.model_dump()})
        .eq("id", str(lead_id))
        .eq("user_id", context.user_id)
        .select()
        .maybe_single()
        .execute()
    )
    if not updated_result.data:
        raise not_found()
    return updated_result.data


@router.post("/{lead_id}/generate-reply")
def generate_reply(
    lead_id: UUID,
    context: AuthContext = Depends(get_auth_context),
) -> dict[str, str]:
    lead_result = (
        context.supabase.table("leads")
        .select("*")
        .eq("id", str(lead_id))
        .eq("user_id", context.user_id)
        .maybe_single()
        .execute()
    )
    if not lead_result.data:
        raise not_found()

    analysis = lead_result.data.get("analysis")
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analyze the lead before generating a follow-up reply",
        )

    try:
        settings_result = (
            context.supabase.table("business_settings")
            .select("business_name, services_offered, reply_signature")
            .eq("user_id", context.user_id)
            .maybe_single()
            .execute()
        )
        suggested_reply = generate_followup_reply(
            lead_result.data["message"],
            analysis,
            settings_result.data or {},
        )
    except AIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except AIReplyError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return {"suggested_reply": suggested_reply}


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: UUID,
    lead: LeadUpdate,
    context: AuthContext = Depends(get_auth_context),
) -> dict:
    result = (
        context.supabase.table("leads")
        .update(lead.model_dump(exclude_unset=True))
        .eq("id", str(lead_id))
        .eq("user_id", context.user_id)
        .select()
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise not_found()
    return result.data


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: UUID,
    context: AuthContext = Depends(get_auth_context),
) -> Response:
    result = (
        context.supabase.table("leads")
        .delete()
        .eq("id", str(lead_id))
        .eq("user_id", context.user_id)
        .execute()
    )
    if not result.data:
        raise not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
