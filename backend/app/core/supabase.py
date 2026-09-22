from typing import Optional

from supabase import Client, create_client

from app.core.config import settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Returns a singleton instance of the Supabase Client if credentials
    are configured in settings, otherwise returns None.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = settings.supabase_url.strip()
    key = (settings.supabase_service_role_key.strip() or settings.supabase_key.strip())

    if url and key:
        try:
            _supabase_client = create_client(url, key)
        except Exception:
            _supabase_client = None

    return _supabase_client


def is_supabase_configured() -> bool:
    """Check whether Supabase credentials are provided."""
    return bool(settings.supabase_url.strip() and (settings.supabase_service_role_key.strip() or settings.supabase_key.strip()))


def reset_supabase_client():
    """Reset singleton instance (useful for testing)."""
    global _supabase_client
    _supabase_client = None
