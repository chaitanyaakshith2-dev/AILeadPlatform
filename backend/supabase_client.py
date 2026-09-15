import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


class SupabaseConfigurationError(RuntimeError):
    """Raised when the Supabase client is missing required configuration."""


load_dotenv(Path(__file__).with_name(".env"))


def get_supabase_client() -> Client:
    """Create a Supabase client from environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")

    missing_variables = [
        variable
        for variable, value in (
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_ANON_KEY", supabase_anon_key),
        )
        if not value
    ]

    if missing_variables:
        variables = ", ".join(missing_variables)
        raise SupabaseConfigurationError(
            f"Missing required Supabase environment variable(s): {variables}. "
            "Set them in backend/.env before creating a Supabase client."
        )

    return create_client(supabase_url, supabase_anon_key)


def get_service_role_client() -> Client:
    """Create the server-only client used by the tokenized public webhook."""
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    missing_variables = [
        variable
        for variable, value in (
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_SERVICE_ROLE_KEY", service_role_key),
        )
        if not value
    ]
    if missing_variables:
        variables = ", ".join(missing_variables)
        raise SupabaseConfigurationError(
            f"Missing required server-side Supabase environment variable(s): {variables}."
        )

    return create_client(supabase_url, service_role_key)
